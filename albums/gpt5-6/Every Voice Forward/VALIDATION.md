# Validation report

Generated from the deterministic score build and a secondary, non-authoritative General MIDI reference render.

## Structural and coverage results

`python3 build.py --verify` passes all five per-track oracle groups and the album-wide coverage group.

| # | Track | MIDI time | Note-ons | Parsed events | Programs heard | Bends | Channel pressure | Poly pressure |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | Daybreak Relay | 3:55 | 11,013 | 24,248 | 32 | 124 | 136 | 0 |
| 2 | Brighter Engines | 4:21 | 8,585 | 23,603 | 32 | 126 | 1,416 | 14 |
| 3 | Open-Sky Signal | 3:50 | 6,470 | 24,908 | 32 | 310 | 264 | 0 |
| 4 | The World in the Chorus | 4:29 | 7,540 | 25,644 | 32 | 423 | 15 | 0 |
| 5 | Every Voice Forward | 4:49 | 8,981 | 23,727 | 16 | 190 | 495 | 0 |

Album-wide assertions:

- Every melodic GM program **0–127** receives real notes; the first four tracks cover exact contiguous blocks.
- Every GM percussion key **35–81** sounds; track 4 uses a GS-assigned second rhythm part for keys 60–81.
- No stuck notes, unmatched note-offs, same-pitch overlaps, or Program Change events over active voices.
- Banked patches `(2,0,19)`, `(0,96,25)`, `(0,19,99)` and `(1,0,109)` all receive notes.
- Meaningful non-default gestures are present for CC1, 2, 5, 11, 64–68, 70, 71, 74, 84, 91, 93 and 94.
- Both RPN 0 and RPN 1 are authored; GM/GS/XG reset, XG Hall/Chorus/Amp Simulator and GS rhythm-part SysEx are parsed.
- The four tagged finale themes overlap for more than the verifier’s required 48-beat contrapuntal span.

## Reference-render sanity pass

These measurements use TimGM6mb through FluidSynth, not Ferrosintesis. They test timing, gross density, clipping and accidental silence only; they do **not** validate Ferrosintesis timbre, samples, bank variants, physical models or effect semantics.

| # | Peak | Clipped samples | Longest silence inside MIDI timeline | Stereo correlation |
|---:|---:|---:|---:|---:|
| 1 | 0.203 | 0.00000% | 1.5s | 0.826 |
| 2 | 0.219 | 0.00000% | 1.5s | 0.633 |
| 3 | 0.209 | 0.00000% | 1.5s | 0.831 |
| 4 | 0.200 | 0.00000% | 1.5s | 0.798 |
| 5 | 0.255 | 0.00000% | 2.0s | 0.633 |

No reference render clipped. The initial 1.5–2 seconds of intentional wake space is the longest silence in every track after the finale’s obsolete padded timeline was removed.

## Rebuild contract

Each output is built twice from a fresh score and must be byte-identical. Committed MIDI and `album_manifest.json` are then compared to the in-memory rebuild before any musical oracle is evaluated.
