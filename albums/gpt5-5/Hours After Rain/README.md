# Hours After Rain
### an original cinematic-minimalist MIDI album in twelve parts · ~58 minutes

Piano, strings, celesta, and sparse low percussion, shaped as an emotional journey
through slow grief, rapid motion, pressure, introspection, tragedy, and release.

This is original material using broad film-music and contemporary-classical
vocabulary; it is not a direct imitation of any living composer or existing score.

The MIDI files are in **`midi/`**, numbered as an album. The score sources are in
**`tracks/`**, one entry point per track, with the shared generator in **`engine.py`**.

## Tracklist

| # | title | mood |
|---|-------|------|
| 01 | The City Holds Its Breath | slow, apprehensive, introspective |
| 02 | Glass on Wet Pavement | rapid, nervous, urban |
| 03 | Mercy in Three Notes | slow, tender, wounded |
| 04 | A Door Left Open | energetic, tense, investigative |
| 05 | Rooms That Remember Us | introspective, warm, haunted |
| 06 | Red Line Fugue | rapid, energetic, dangerous |
| 07 | A Quiet Arithmetic of Light | luminous, emotional midpoint |
| 08 | Newsprint Ashes | tragic, low, fatalistic |
| 09 | Borrowed Pulse | energetic, resilient, searching |
| 10 | The Hour Before Dawn | slow, suspended, fragile |
| 11 | No Witness Choir | tragic, climactic, expansive |
| 12 | Last Train, Empty Platform | quiet, final, unresolved |

## Layout

- `midi/` - numbered album MIDI files, named `NN - Title.mid`
- `tracks/` - numbered per-track source entry points
- `engine.py` - shared composition engine, MIDI writer, manifest writer, verifier
- `build.py` - rebuilds or verifies the album
- `ALBUM.md` - detailed track notes, roles, moods, and durations
- `album_manifest.json` - machine-readable metadata

## Regenerate / Verify

```powershell
python .\build.py
python .\build.py --verify
python .\tracks\07_a_quiet_arithmetic_of_light.py
```
