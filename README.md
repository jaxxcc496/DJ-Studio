# DJ-Studio

Free, customizable DJ software for Windows. This project is under active development.

## Current version

- Two-deck performance layout
- Add local audio files to the library
- Search the library by filename
- Create, rename, and delete playlists
- Add tracks to playlists and remove tracks from the current view
- Load a selected library track into Deck A or Deck B
- Four selectable interface themes
- Windows build workflow using GitHub Actions

**Not implemented yet:** actual audio playback, scratching, beat detection, MIDI/controller support, mixer processing, effects, sampler, and recording. The deck controls are currently interface placeholders and do not play sound yet.

## Run locally

Install Python 3.10 or newer and run:

    python app/main.py

The app uses Python's standard library (Tkinter).

## Build for Windows

Open the repository's **Actions** tab and choose **Build Windows app**. A push to the main branch also starts a build. When it finishes, download the **DJ-Studio-Windows** artifact from the workflow run.

## Roadmap

1. Improve the interface and save user preferences
2. Add a real audio engine and playable decks
3. Add cue points, loops, pitch, waveform analysis, and beat matching
4. Add MIDI device detection and customizable mappings
5. Add mixer, effects, sampler, recording, and plugin support

Controller compatibility will depend on each device's MIDI/HID protocol and available drivers.
