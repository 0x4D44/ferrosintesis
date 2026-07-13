# Synth Feature Showcase

Five original, fast instrumental MIDI demos for ferrosintesis. The suite is
designed to exercise current instrument families, expressive MIDI controllers,
stereo staging, and accepted future synth seams.

Build:

```powershell
python build.py
python build.py --verify
```

Audio validation after rendering the MIDI files to `build/wav/`:

```powershell
python analyze.py
```

Rendered WAV files are scratch output and are not committed.

Listening copies (`.opus`) are git-ignored build output, produced from the repo root:

```powershell
python build.py
```
