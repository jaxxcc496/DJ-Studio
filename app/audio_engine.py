import math
import threading

import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly


class AudioEngine:
    """Callback-based two-deck mixer with stateful EQ and eight one-shot sample slots."""

    def __init__(self, sample_rate=44100, blocksize=512):
        self.sample_rate = int(sample_rate)
        self.blocksize = int(blocksize)
        self.lock = threading.RLock()
        self.decks = {key: self._new_deck() for key in ("A", "B")}
        self.crossfade = 0.0
        self.samples = [self._new_sample() for _ in range(8)]
        self.effects = {key: {"filter": False, "echo": False} for key in ("A", "B")}
        self._fx_filters = {
            "filter": butter(2, 1200, btype="lowpass", fs=self.sample_rate, output="sos")
        }
        self._fx_state = {
            key: np.zeros((len(self._fx_filters["filter"]), 2, 2), dtype=np.float64)
            for key in ("A", "B")
        }
        self._echo_buffers = {
            key: np.zeros((int(self.sample_rate * 0.28), 2), dtype=np.float32)
            for key in ("A", "B")
        }
        self._echo_positions = {"A": 0, "B": 0}
        self.stream = None
        self.error = None
        self._filters = {
            "low": butter(2, 250, btype="lowpass", fs=self.sample_rate, output="sos"),
            "mid": butter(2, (250, 2500), btype="bandpass", fs=self.sample_rate, output="sos"),
            "high": butter(2, 2500, btype="highpass", fs=self.sample_rate, output="sos"),
        }
        self._eq_state = {
            deck: {band: np.zeros((len(sos), 2, 2), dtype=np.float64)
                   for band, sos in self._filters.items()}
            for deck in ("A", "B")
        }

    @staticmethod
    def _new_deck():
        return {
            "audio": None, "source_audio": None, "position": 0.0, "playing": False, "pitch": 1.0,
            "gain": 1.0, "eq": {"low": 0.0, "mid": 0.0, "high": 0.0},
            "loop": None, "path": None, "scratch_rate": None,
        }

    @staticmethod
    def _new_sample():
        return {"audio": None, "position": 0, "playing": False, "path": None, "gain": 1.0}

    def start(self):
        if self.stream is not None:
            return True
        try:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate, channels=2, dtype="float32",
                blocksize=self.blocksize, callback=self._callback,
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

    def _decode(self, path):
        try:
            data, sr = sf.read(path, dtype="float32", always_2d=True)
        except Exception:
            import librosa
            audio, sr = librosa.load(path, sr=self.sample_rate, mono=False, dtype=np.float32)
            data = audio.T if audio.ndim > 1 else audio[:, None]
            sr = self.sample_rate
        if sr != self.sample_rate:
            divisor = math.gcd(int(sr), self.sample_rate)
            data = resample_poly(data, self.sample_rate // divisor, int(sr) // divisor, axis=0)
        if data.shape[1] == 1:
            data = np.repeat(data, 2, axis=1)
        elif data.shape[1] > 2:
            data = data[:, :2]
        return np.ascontiguousarray(data, dtype=np.float32)

    def load(self, deck, path):
        data = self._decode(path)
        with self.lock:
            self.decks[deck].update(audio=data, source_audio=data.copy(), position=0.0, playing=False,
                                    pitch=1.0, loop=None, path=path)
            self._reset_eq_state(deck)
        return len(data) / self.sample_rate

    def load_sample(self, slot, path):
        data = self._decode(path)
        with self.lock:
            self.samples[int(slot)].update(audio=data, position=0, playing=False, path=path)
        return len(data) / self.sample_rate

    def trigger_sample(self, slot):
        with self.lock:
            sample = self.samples[int(slot)]
            if sample["audio"] is None:
                return False
            sample["position"] = 0
            sample["playing"] = True
            return True

    def stop_sample(self, slot):
        with self.lock:
            sample = self.samples[int(slot)]
            sample["playing"] = False
            sample["position"] = 0

    def stop_all_samples(self):
        with self.lock:
            for sample in self.samples:
                sample["playing"] = False
                sample["position"] = 0

    def _reset_eq_state(self, deck):
        for band, sos in self._filters.items():
            self._eq_state[deck][band] = np.zeros((len(sos), 2, 2), dtype=np.float64)

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
            self._reset_eq_state(deck)

    def seek(self, deck, seconds):
        with self.lock:
            d = self.decks[deck]
            if d["audio"] is not None:
                d["position"] = float(np.clip(seconds, 0, len(d["audio"]) / self.sample_rate))
                self._reset_eq_state(deck)

    def position(self, deck):
        with self.lock:
            return float(self.decks[deck]["position"])

    def set_pitch(self, deck, percent):
        with self.lock:
            self.decks[deck]["pitch"] = float(np.clip(1.0 + percent / 100.0, 0.5, 1.5))

    def source_audio(self, deck):
        with self.lock:
            source = self.decks[deck]["source_audio"]
            return None if source is None else source.copy()

    def restore_source_audio(self, deck):
        with self.lock:
            d = self.decks[deck]
            if d["source_audio"] is not None:
                d["audio"] = d["source_audio"]
                d["position"] = min(d["position"], len(d["audio"]) / self.sample_rate)
                self._reset_eq_state(deck)

    def set_stretched_audio(self, deck, data):
        with self.lock:
            d = self.decks[deck]
            old_length = max(1, len(d["audio"]) if d["audio"] is not None else 1)
            fraction = d["position"] * self.sample_rate / old_length
            d["audio"] = np.ascontiguousarray(data, dtype=np.float32)
            d["position"] = fraction * len(d["audio"]) / self.sample_rate
            d["pitch"] = 1.0
            self._reset_eq_state(deck)

    def set_scratch_rate(self, deck, rate):
        with self.lock:
            self.decks[deck]["scratch_rate"] = float(np.clip(rate, -8.0, 8.0))

    def end_scratch(self, deck):
        with self.lock:
            self.decks[deck]["scratch_rate"] = None

    def set_gain(self, deck, value):
        with self.lock:
            self.decks[deck]["gain"] = float(np.clip(value, 0.0, 1.5))

    def set_eq(self, deck, band, value):
        if band not in ("low", "mid", "high"):
            raise ValueError("EQ band must be low, mid or high")
        with self.lock:
            self.decks[deck]["eq"][band] = float(np.clip(value, -1.0, 1.0))

    def set_crossfade(self, value):
        with self.lock:
            self.crossfade = float(np.clip(value, -1.0, 1.0))

    def set_effect(self, deck, effect, enabled):
        if effect not in ("filter", "echo"):
            raise ValueError("Effect must be filter or echo")
        with self.lock:
            self.effects[deck][effect] = bool(enabled)
            if effect == "filter":
                self._fx_state[deck].fill(0)
            else:
                self._echo_buffers[deck].fill(0)
                self._echo_positions[deck] = 0

    def _process_effects(self, deck, block):
        fx = self.effects[deck]
        if fx["filter"]:
            filtered, state = sosfilt(
                self._fx_filters["filter"], block, axis=0,
                zi=self._fx_state[deck]
            )
            self._fx_state[deck] = state
            block = filtered.astype(np.float32, copy=False)
        if fx["echo"]:
            buffer = self._echo_buffers[deck]
            pos = self._echo_positions[deck]
            delayed = np.empty_like(block)
            for i in range(len(block)):
                delayed[i] = buffer[pos]
                buffer[pos] = block[i] + delayed[i] * 0.32
                pos = (pos + 1) % len(buffer)
            self._echo_positions[deck] = pos
            block = block + delayed * 0.38
        return block

    def set_loop(self, deck, start, end):
        with self.lock:
            d = self.decks[deck]
            if d["audio"] is not None and end > start:
                d["loop"] = (float(start), float(end))
                d["position"] = float(start)
                self._reset_eq_state(deck)

    def clear_loop(self, deck):
        with self.lock:
            self.decks[deck]["loop"] = None

    def _eq_block(self, deck, data, eq):
        if not any(abs(value) > 0.001 for value in eq.values()):
            return data
        result = data.astype(np.float64, copy=True)
        for band, sos in self._filters.items():
            amount = eq[band]
            if abs(amount) <= 0.001:
                continue
            filtered, state = sosfilt(
                sos, data, axis=0, zi=self._eq_state[deck][band]
            )
            self._eq_state[deck][band] = state
            gain = 10.0 ** (amount * 1.2)
            result += filtered * (gain - 1.0)
        return result.astype(np.float32)

    def _callback(self, outdata, frames, time_info, status):
        outdata.fill(0)
        with self.lock:
            fade = self.crossfade
            # Equal-power law keeps perceived level steadier through the centre.
            angle = (fade + 1.0) * (math.pi / 4.0)
            deck_levels = {"A": math.cos(angle), "B": math.sin(angle)}
            for key in ("A", "B"):
                d = self.decks[key]
                audio = d["audio"]
                if not d["playing"] or audio is None:
                    continue
                length = len(audio)
                step = d["scratch_rate"] if d["scratch_rate"] is not None else d["pitch"]
                indices = d["position"] * self.sample_rate + step * np.arange(frames)
                if d["loop"] is not None:
                    start, end = d["loop"]
                    loop_start = start * self.sample_rate
                    loop_length = max(1.0, (end - start) * self.sample_rate)
                    indices = loop_start + np.mod(indices - loop_start, loop_length)
                valid = (indices >= 0) & (indices < length)
                if not np.any(valid):
                    d["playing"] = False
                    continue
                i0 = np.floor(indices[valid]).astype(np.int64)
                i1 = np.minimum(i0 + 1, length - 1)
                frac = (indices[valid] - i0).astype(np.float32)[:, None]
                block = np.zeros((frames, 2), dtype=np.float32)
                block[valid] = audio[i0] * (1.0 - frac) + audio[i1] * frac
                block = self._eq_block(key, block, d["eq"])
                block = self._process_effects(key, block)
                outdata += block * (d["gain"] * deck_levels[key])
                d["position"] += frames * step / self.sample_rate
                if d["scratch_rate"] is not None:
                    d["position"] = float(np.clip(d["position"], 0.0, length / self.sample_rate))
                elif d["loop"] is not None and d["position"] >= d["loop"][1]:
                    start, end = d["loop"]
                    d["position"] = start + (d["position"] - start) % (end - start)
                elif d["position"] >= length / self.sample_rate:
                    d["position"] = length / self.sample_rate
                    d["playing"] = False

            for sample in self.samples:
                audio = sample["audio"]
                if not sample["playing"] or audio is None:
                    continue
                start = sample["position"]
                count = min(frames, len(audio) - start)
                if count > 0:
                    outdata[:count] += audio[start:start + count] * sample["gain"]
                    sample["position"] += count
                if sample["position"] >= len(audio):
                    sample["playing"] = False
                    sample["position"] = 0

        # Soft clipping prevents harsh digital overflow when decks and samples overlap.
        np.tanh(outdata, out=outdata)
