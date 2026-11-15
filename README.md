# DJ-Studio

Free, customizable DJ software for Windows. This repository is the start of the project.

## Current prototype

- Desktop window built with Python and Tkinter
- Two-deck interface mock-up
- Three selectable visual themes: Dark, VirtualDJ Grey, and Rekordbox Blue
- Initial Windows build workflow using GitHub Actions

**Important:** This is an early interface prototype. The deck buttons are placeholders; audio playback, mixing, MIDI controllers, effects, and library management are not implemented yet.

## Run locally

Install Python 3.10 or newer, then run:

```bash
python app/main.py
```

Tkinter is included with most standard Windows Python installations.

## Build for Windows

Open the repository's **Actions** tab. Run **Build Windows app** with **Run workflow**, or push a commit to `main`. Download the `DJ-Studio-Windows` artifact from the completed workflow.

## Planned development

1. Customizable interface and saved layouts
2. Audio engine and playable decks
3. MIDI device detection and mapping
4. Mixer, effects, sampler, and music library
5. Recording, plugins, and phone companion features

The goal is broad controller support, but compatibility will depend on each device's MIDI/HID protocol and available drivers.
