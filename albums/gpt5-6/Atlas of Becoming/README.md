# Atlas of Becoming

Fourteen deterministic MIDI compositions by GPT-5.6. The set moves
from aquatic spectacle through contemporary fracture, biological evolution,
linked-song form, machine history, cinematic pursuit, and five freely chosen
worlds. Every melody, chord sequence, bass line, and rhythmic cell was written for
this album.

Named works in the brief are reference points for broad form, pacing, ensemble
colour, or dramatic function. The brief asks for new material rather than
deliberate quotation or reconstruction; that intent is not a guarantee against
incidental similarity.

## Files

- `midi/` — the fourteen finished Standard MIDI Files.
- `tracks/` — one composition module per track plus shared musical helpers.
- `engine.py` — deterministic standard-library MIDI writer.
- `build.py` — album builder, manifest writer, and freshness check.
- `verify.py` — score-side musical and structural oracles.
- `analyze.py` — optional render-side WAV checks.
- `album_manifest.json` — durations, concepts, tags, and timed section maps.
- `ALBUM.md` — listening notes and the design response to the brief.
- `lyrics/` — exact-track UTF-8 listening guides embedded as multiline `LYRICS`
  tags in the `.opus` files produced by `python3 build.py` (git-ignored build
  output).

## Rebuild and verify

From this directory:

```powershell
python3 build.py
python3 build.py --verify
python3 build.py --verify --track 8
```

The builder uses only the Python standard library and fixed seeds. Rebuilding is
byte-exact. The verifier checks freshness, duration, density, orchestral breadth,
section contrast, controllers, stereo discipline, note range, sticky-controller
resets, and exact coverage of the fourteen requested categories.

## Optional audio verification

After building the repository's `ferrosintesis` renderer, render the files into a
directory using the same filename stems, then run:

```powershell
python3 analyze.py <wav-directory>
```

The WAV scanner checks that every named section is audible, that the render has
dynamic contrast and headroom, that no interior digital silence appears, and that
the stereo image survives mono summing.

