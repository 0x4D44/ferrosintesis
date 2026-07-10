# Atlas of Becoming

Fourteen original, deterministic MIDI compositions by OpenAI Codex. The set moves
from aquatic spectacle through contemporary fracture, biological evolution,
linked-song form, machine history, cinematic pursuit, and five freely chosen
worlds. Every melody, chord sequence, bass line, and rhythmic cell was written for
this album.

Named works in the brief are reference points for broad form, pacing, ensemble
colour, or dramatic function only. The scores do not quote or reconstruct their
melodies, signature riffs, lyrics, or arrangements.

## Files

- `midi/` — the fourteen finished Standard MIDI Files.
- `tracks/` — one composition module per track plus shared musical helpers.
- `engine.py` — deterministic standard-library MIDI writer.
- `build.py` — album builder, manifest writer, and freshness check.
- `verify.py` — score-side musical and structural oracles.
- `analyze.py` — optional render-side WAV checks.
- `album_manifest.json` — durations, concepts, tags, and timed section maps.
- `ALBUM.md` — listening notes and the design response to the brief.

## Rebuild and verify

From this directory:

```powershell
python .\build.py
python .\build.py --verify
python .\build.py --verify --track 8
```

The builder uses only the Python standard library and fixed seeds. Rebuilding is
byte-exact. The verifier checks freshness, duration, density, orchestral breadth,
section contrast, controllers, stereo discipline, note range, sticky-controller
resets, and exact coverage of the fourteen requested categories.

## Optional audio verification

After building the repository's `ferrosintesis` renderer, render the files into a
directory using the same filename stems, then run:

```powershell
python .\analyze.py <wav-directory>
```

The WAV scanner checks that every named section is audible, that the render has
dynamic contrast and headroom, that no interior digital silence appears, and that
the stereo image survives mono summing.

