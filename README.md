# DJ-Studio

A free, customizable Windows DJ software project. The current release focuses on the performance-screen design and library workflow.

## Included in this build

- Redesigned two-deck layout with round jogwheel visuals
- Large waveform-style display areas (currently visual mockups, not audio analysis)
- Deck load controls, cue, play/stop, pitch, sync, loop and hot-cue interface controls
- Mixer layout with gain, EQ and crossfader sliders (visual controls only)
- Eight sampler pads (interface only)
- Music library: add local audio files and search by filename
- Playlists: create, rename, delete, and add/remove tracks
- Library and playlist data saved locally on the computer
- Four themes: Midnight, VirtualDJ Grey, Rekordbox Blue, and Purple

## Not connected yet

Audio playback, real-time waveform analysis, jogwheel scratching, cue/loop playback, MIDI/controller support, effects processing, and sampler audio are not implemented yet. The controls and jogwheels in this build are interface elements, not functioning audio controls. These need a separate audio-engine development stage.

## Run

Install Python 3.10 or newer and run:

    python app/main.py

The app currently uses Python's standard library (Tkinter).

## Windows build

A push to the `main` branch starts the GitHub Actions workflow. Open **Actions**, select the latest successful **Build Windows app** run, and download its `DJ-Studio-Windows` artifact.

## Next development stages

1. Complete and refine the interface and save layout preferences
2. Add the audio engine and real two-deck playback
3. Connect jogwheel movement, seeking, scratch behavior, cue points and loops
4. Add beat analysis and genuine scrolling waveforms

MIDI and VST/plugin support are not part of the current requested stage.
