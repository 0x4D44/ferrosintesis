# Listening Library

This tree holds the committed, tagged Opus listening copies.

Drag `listening/` into an audio player to browse the rendered albums by artist
and album. The source albums, MIDI files, manifests, and composition engines live
under `albums/`.

Regenerate these files from the repo root with:

```powershell
cargo build --release -p ferrosintesis-cli
python render_opus.py
```
