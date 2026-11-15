# DJ-Studio

DJ-Studio is an independent DJ application project aiming for a VirtualDJ-style workflow. It is not affiliated with or powered by VirtualDJ.

## Current implementation

- Two-deck desktop interface
- Local audio library and playlists
- Audio output through a Python audio callback engine
- Deck playback, pause, stop and seeking
- Basic speed change (this changes playback pitch too; key-lock time-stretch is not implemented)
- Basic three-band EQ, deck gain and crossfader
- Basic BPM analysis, pitch-ratio sync, hot cues and beat-length loops
- Waveform display and jogwheel-style seeking interface
- Theme selection

## Important limitations

This is an early development build, not a finished professional DJ system. The following are not yet implemented or not yet at VirtualDJ quality:

- Proper scratch/jogwheel vinyl emulation and low-latency response
- Beat-grid and phase-aligned sync
- High-quality key-lock time-stretch
- Persistent-state EQ filters and professionally tuned audio processing
- Working sample-bank playback and sample editor
- Built-in effects rack and VST hosting
- MIDI/controller mapping and audio routing configuration
- Reliable automated performance tests on Windows hardware

The interface may show controls for features that are still being developed. Do not rely on this build for a live performance.

## Run from source

Install Python 3.10 or newer, install the packages in `requirements.txt`, then run:

```bash
python app/main.py
```

An audio output device is required. Supported file formats depend on the installed audio libraries and codecs.

## Windows build

A push to the `main` branch starts the GitHub Actions workflow. Open **Actions**, select the latest successful **Build Windows app** run, and download its `DJ-Studio-Windows` artifact.

## Development direction

The goal is to develop and test the core audio engine first, then connect each visible control to real functionality. Feature parity with a mature product such as VirtualDJ requires substantial implementation and testing; it cannot be guaranteed by copying its appearance.
