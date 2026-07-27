# The Spark
### an original cinematic-minimalist MIDI album in twelve parts · emotional arc from stillness to crest and release

Piano, strings, celesta, and sparse low percussion, shaped as an emotional arc:
quiet introspection, urban pressure, grief, urgency, and catharsis.

This is original material using broad film-music and contemporary-classical
vocabulary; it is not a direct imitation of any living composer or existing score.

The MIDI files are in **`midi/`**, numbered as an album. The score sources are in
**`tracks/`**, one entry point per track, with the shared generator in **`engine.py`**.

## Tracklist

| # | title | mood |
|---|-------|------|
| 01 | The Quiet Before Dawn | quiet, still, expectant |
| 02 | Windowlit Water | quiet, contemplative, slow-building |
| 03 | Letters in Winter Ink | tender, wounded, and restrained |
| 04 | First Alarm | urgent, tense, investigative |
| 05 | A City of Small Fires | restless, urban, intimate |
| 06 | Mercy of the Rail Line | propulsive, searching, relentless |
| 07 | Midnight Engine | luminous, patient, turning inward |
| 08 | A Door You Didn't Hear Close | quiet but dramatic, haunted |
| 09 | The Big Arc Begins | urgent, sweeping, resilient |
| 10 | Lightning Over Stone | fast, brilliant, triumphant |
| 11 | Chamber of Witness | massive, cathartic, expansive |
| 12 | After the Spark, You Return | quiet, reflective, unresolved |

## Layout

- `midi/` - numbered album MIDI files, named `NN - Title.mid`
- `tracks/` - numbered per-track source entry points
- `engine.py` - shared composition engine, MIDI writer, manifest writer, verifier
- `build.py` - rebuilds or verifies the album
- `ALBUM.md` - detailed track notes, roles, moods, and durations
- `album_manifest.json` - machine-readable metadata

## Regenerate / Verify

```powershell
python3 build.py
python3 build.py --verify
```

You can also rebuild individual tracks:

```powershell
python3 tracks/07_midnight_engine.py
```
