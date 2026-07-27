# The Long Turning
### a single 60-minute progressive MIDI movement

One uninterrupted track for guitars, bass, piano, organ, strings, whistle/flute,
bells, distant choir, and percussion. The piece uses a long-form progressive
folk-rock/classical collage vocabulary: recurring guitar cells, abrupt chapter
changes, pastoral whistle themes, organ beds, bell returns, and driving percussion.

This is original material. It is not a direct imitation or continuation of any
living artist's catalog or any existing recording.

## Layout

- `midi/` - the numbered album MIDI file
- `tracks/` - the numbered per-track source entry point
- `engine.py` - shared generator, MIDI writer, manifest writer, and verifier
- `build.py` - rebuilds or verifies the album
- `ALBUM.md` - the creative map and section list
- `album_manifest.json` - machine-readable metadata

## Regenerate / Verify

```powershell
python3 build.py
python3 build.py --verify
python3 tracks/01_the_long_turning.py
```
