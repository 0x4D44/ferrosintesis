# Every Voice Forward

**Five upbeat, uplifting and deliberately ambitious MIDI compositions written for Ferrosintesis.**

The suite is both an album and an instrument showcase. The first four tracks divide the complete General MIDI program map into four musical families; every program is given notes, time and a recognisable role. The finale then forgets the catalogue order and recombines fifteen favourite voices into one large-form anthem.

- **All 128 GM melodic programs** are sounded and machine-verified.
- **All 47 GM percussion keys, 35–81**, are sounded in a musical parade.
- Ferrosintesis-specific voices include the **cathedral organ** (MSB 2 / program 19), **mandolin** (LSB 96 / program 25), **Hollow Release** (LSB 19 / program 99), and the modeled alternate **bagpipe** (MSB 1 / program 109).
- The scores author pedals, breath, expression, Leslie/mod wheel, legato, portamento, vowel morphing, resonant filtering, reverb/chorus/delay sends, pitch bend, channel and polyphonic pressure, RPN bend range and fine tuning, plus GM/GS/XG SysEx.

The compositions are original. They use broad progressive-pop, cinematic, electronic, funk-rock and world-music vocabulary without reconstructing a named piece.

## Track list

| # | Track | Time | Instrument territory |
|---:|---|---:|---|
| 1 | **Daybreak Relay** | 3:55 | Programs 0–31: keys, mallets, organs, accordions and guitars |
| 2 | **Brighter Engines** | 4:21 | Programs 32–63: basses, strings, ensembles, choir and brass |
| 3 | **Open-Sky Signal** | 3:50 | Programs 64–95: reeds, pipes, synth leads and pads |
| 4 | **The World in the Chorus** | 4:29 | Programs 96–127, the banked mandolin/bagpipe and every GM drum key |
| 5 | **Every Voice Forward** | 4:49 | Fifteen-voice finale, four themes, 7/8 ascent and a B-major lift |

**Total: 21:24.** Detailed listening notes are in [`ALBUM.md`](ALBUM.md); the exact expressive feature map is in [`CONTROL_MAP.md`](CONTROL_MAP.md).

## Build and verify

The generator is deterministic and uses only the Python standard library.

```bash
python3 build.py             # regenerate all MIDI and album_manifest.json
python3 build.py --verify    # rebuild in memory, compare bytes, run every oracle
python3 build.py --summary   # compact score statistics
python3 build.py --track 5   # rebuild one track while composing
```

A successful verification ends with:

```text
RESULT: PASS — deterministic files and all composition oracles are green
```

The oracles do not merely count Program Change messages. They parse the written SMFs and require each target program to receive real note-ons and sounding time. They also reject stuck notes, unmatched note-offs, same-pitch overlaps, and patch changes over active voices; prove that the full drum map sounds; inspect bank selections and SysEx; require non-default controller ranges; and verify that the finale’s four tagged themes overlap for a sustained contrapuntal span.

## Render with Ferrosintesis

Placed at `albums/gpt5-6/Every Voice Forward/` in the Ferrosintesis repository, the album follows the existing catalogue layout. From the repository root:

```bash
cargo run --release -p render-catalog -- --album "Every Voice Forward"
```

That produces the normal tagged listening copies under `listening/`. The committed `.mid` files are the source of truth; rendered audio remains build output.

## Files

- `engine.py` — dependency-free SMF writer, musical helpers and structural parser.
- `material.py` — four original themes and harmonic material shared across the suite.
- `tracks.py` — the five arrangements.
- `build.py` — deterministic rebuild, manifest generation and command-line entry point.
- `verify.py` — score, MIDI, controller, bank, SysEx and counterpoint oracles.
- `VALIDATION.md` — measured coverage plus the non-authoritative reference-render sanity report.
- `album_manifest.json` — catalogue metadata and measured score statistics.
- `midi/` — committed type-1 Standard MIDI Files at 480 PPQ.

## Music licensing

The repository’s software licence does not automatically cover album music or MIDI. Choose and record an album-specific music licence before external redistribution.
