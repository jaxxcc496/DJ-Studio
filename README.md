# DJ-Studio

DJ-Studio is an independent DJ application project aiming for a VirtualDJ-style workflow. It is not affiliated with or powered by VirtualDJ.

## Implemented development features

- Two-deck desktop interface and callback-based stereo audio mixer
- Simultaneous deck playback, pause, stop, seeking and variable playback speed
- Equal-power crossfader, deck gain and three-band LOW/MID/HIGH EQ
- Per-deck low-pass filter and echo effects
- Eight one-shot sample slots with load, trigger and stop controls
- BPM analysis, simple BPM-ratio sync, hot cues and beat-length loops
- Waveform display and jogwheel drag with bidirectional variable-speed scratch transport
- Optional pitch-preserving key-lock using offline time-stretch processing
- MIDI input selection and MIDI-learn mappings for crossfader, deck gain, pitch and EQ
- Local audio library, playlists, saved sample assignments, saved MIDI mappings and themes

## Important limitations

This remains an early development build, not a finished professional DJ system. Scratch response, beat-grid and phase-aligned sync, key-lock sound quality, effect quality, MIDI compatibility across controllers, audio-device handling and performance under load still require testing and refinement. There is no VST host, full effects rack, multi-channel audio routing, or complete VirtualDJ feature parity.

Some processing, especially key-lock time-stretch, is performed offline and may take time depending on track length and computer performance. Do not rely on this build for a live performance until it has been tested with the intended Windows computer, audio interface and controller.

## Run from source

Install Python 3.10 or newer, install the packages in `requirements.txt`, then run:

```bash
python app/main.py
```

An audio output device is required. MIDI input uses pygame's MIDI support. Supported audio formats depend on the installed audio libraries and codecs.

## Windows build

A push to the `main` branch starts the GitHub Actions workflow. Open **Actions**, select the latest successful **Build Windows app** run, and download its `DJ-Studio-Windows` artifact.

## Development direction

The goal is to develop and test the core audio engine first, then connect each visible control to real functionality. Feature parity with a mature product such as VirtualDJ requires substantial implementation and testing; it cannot be guaranteed by copying its appearance.
