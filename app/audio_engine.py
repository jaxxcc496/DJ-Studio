import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import butter, sosfilt

class AudioEngine:
    """Two-deck callback audio engine with pitch, 3-band EQ and crossfader."""
    def __init__(self, sample_rate=44100, blocksize=512):
        self.sample_rate = int(sample_rate)
        self.blocksize = int(blocksize)
        self.lock = threading.RLock()
        self.decks = {k: self._new_deck() for k in ("A", "B")}
        self.crossfade = 0.0
        self.stream = None
        self.error = None
        self._filters = {
            "low": butter(2, 250, btype="lowpass", fs=self.sample_rate, output="sos"),
            "lowcut": butter(2, 250, btype="highpass", fs=self.sample_rate, output="sos"),
            "midcut": butter(2, 2500, btype="lowpass", fs=self.sample_rate, output="sos"),
            "high": butter(2, 2500, btype="highpass", fs=self.sample_rate, output="sos"),
        }

    @staticmethod
    def _new_deck():
        return {
            "audio": None, "position": 0.0, "playing": False, "pitch": 1.0,
            "gain": 1.0, "eq": {"low": 0.0, "mid": 0.0, "high": 0.0},
            "loop": None, "path": None
        }

    def start(self):
        if self.stream is not None:
            return True
        try:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate, channels=2, dtype="float32",
                blocksize=self.blocksize, callback=self._callback
            )
            self.stream.start()
            return True
        except Exception as exc:
            self.error = str(exc)
            self.stream = None
            return False

    def close(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            finally:
                self.stream = None

    def load(self, deck, path):
        data, sr = sf.read(path, dtype="float32", always_2d=True)
        if sr != self.sample_rate:
            # Resample once on load; playback pitch remains an independent control.
            from scipy.signal import resample_poly
            import math
            g = math.gcd(int(sr), self.sample_rate)
            data = resample_poly(data, self.sample_rate // g, int(sr) // g, axis=0).astype(np.float32)
        if data.shape[1] == 1:
            data = np.repeat(data, 2, axis=1)
        elif data.shape[1] > 2:
            data = data[:, :2]
        with self.lock:
            d = self.decks[deck]
            d.update(audio=np.ascontiguousarray(data), position=0.0, playing=False,
                     pitch=1.0, loop=None, path=path)
        return len(data) / self.sample_rate

    def play(self, deck):
        with self.lock:
            if self.decks[deck]["audio"] is not None:
                self.decks[deck]["playing"] = True

    def pause(self, deck):
        with self.lock:
            self.decks[deck]["playing"] = False

    def stop(self, deck, reset=True):
        with self.lock:
            d = self.decks[deck]
            d["playing"] = False
            d["loop"] = None
            if reset:
                d["position"] = 0.0

    def seek(self, deck, seconds):
        with self.lock:
            d = self.decks[deck]
            if d["audio"] is not None:
                d["position"] = float(np.clip(seconds, 0, max(0, len(d["audio"]) / self.sample_rate)))
    
    def position(self, deck):
        with self.lock:
            return float(self.decks[deck]["position"])

    def set_pitch(self, deck, percent):
        with self.lock:
            self.decks[deck]["pitch"] = float(np.clip(1.0 + percent / 100.0, 0.5, 1.5))

    def set_gain(self, deck, value):
        with self.lock:
            self.decks[deck]["gain"] = float(np.clip(value, 0.0, 1.0))

    def set_eq(self, deck, band, value):
        with self.lock:
            self.decks[deck]["eq"][band] = float(np.clip(value, -1.0, 1.0))

    def set_crossfade(self, value):
        with self.lock:
            self.crossfade = float(np.clip(value, -1.0, 1.0))

    def set_loop(self, deck, start, end):
        with self.lock:
            d = self.decks[deck]
            if d["audio"] is not None and end > start:
                d["loop"] = (float(start), float(end))
                d["position"] = float(start)

    def clear_loop(self, deck):
        with self.lock:
            self.decks[deck]["loop"] = None

    def _eq_block(self, data, eq):
        # Three-band parallel EQ: low + mid + high with neutral unity defaults.
        if not any(abs(v) > 0.001 for v in eq.values()):
            return data
        try:
            low = sosfilt(self._filters["low"], data, axis=0)
            high = sosfilt(self._filters["high"], data, axis=0)
            mid = sosfilt(self._filters["lowcut"], data, axis=0)
            mid = sosfilt(self._filters["midcut"], mid, axis=0)
            gl, gm, gh = (10.0 ** (eq[k] * 1.2) for k in ("low", "mid", "high"))
            return low * gl + mid * gm + high * gh
        except Exception:
            return data

    def _callback(self, outdata, frames, time_info, status):
        outdata.fill(0)
        with self.lock:
            for key in ("A", "B"):
                d = self.decks[key]
                audio = d["audio"]
                if not d["playing"] or audio is None:
                    continue
                n = len(audio)
                step = d["pitch"] * (self.sample_rate / self.sample_rate)
                pos = d["position"]
                idx = pos * self.sample_rate + step * np.arange(frames, dtype=np.float64)
                if d["loop"] is not None:
                    a, b = d["loop"]
                    length = max(1.0, (b-a) * self.sample_rate)
                    idx = a * self.sample_rate + np.mod(idx - a*self.sample_rate, length)
                valid = idx < n
                if not np.any(valid):
                    d["playing"] = False
                    continue
                idx0 = np.floor(idx[valid]).astype(np.int64)
                idx1 = np.minimum(idx0 + 1, n - 1)
                frac = (idx[valid] - idx0).astype(np.float32)[:, None]
                block = np.zeros((frames, 2), dtype=np.float32)
                block[valid] = audio[idx0] * (1.0-frac) + audio[idx1] * frac
                block = self._eq_block(block, d["eq"])
                fade = self.crossfade
                level = d["gain"] * ((1.0-max(0.0, fade)) if key == "A" else (1.0+min(0.0, fade)))
                outdata += block * level
                d["position"] = float(pos + frames * step / self.sample_rate)
                if d["loop"] is not None and d["position"] >= d["loop"][1]:
                    d["position"] = d["loop"][0] + (d["position"]-d["loop"][0]) % (d["loop"][1]-d["loop"][0])
                elif d["position"] >= n / self.sample_rate:
                    d["position"] = n / self.sample_rate
                    d["playing"] = False
        np.clip(outdata, -1.0, 1.0, out=outdata)
