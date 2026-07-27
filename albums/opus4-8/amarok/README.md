# RIVERWAKE
### a single, unbroken ~60-minute track · after Mike Oldfield's *Amarok*

One continuous river of music — **59:50**, no track breaks — in the spirit of Oldfield's
1990 *Amarok*: restless acoustic folk/prog that never settles, forever shifting key,
tempo and mood, carried by interlocking acoustic guitars, hand percussion, tin whistle,
fiddle, glockenspiel and tubular bells, accordion and choir. It quotes a handful of
recurring themes but almost never repeats itself, and it keeps two of Amarok's jokes:
a **false ending**, and a **hidden Morse-code message**.

> The file is `midi/Riverwake.mid`. Play it through an acoustic/orchestral library for
> the intended sound; the General-MIDI defaults are a serviceable preview.

---

## The journey (one piece, twelve movements)

| from | movement | character |
|------|----------|-----------|
| 0:00 | **I · Awakening** | a D-dorian dawn; the bell theme and the main tune steal in over interlocking guitars |
| 8:00 | **II · First Dance** | reels and a jig, fiddle to the fore, modulating upward |
| 13:45 | **III · Procession** | the main theme in full — choir, bells, a wide major plateau |
| 18:45 | **IV · The Glade** | the river pools: ambient, a hush, then a whimsical waltz |
| 24:25 | **V · Drums of the River** | a hand-percussion jam — marimba, congas, polyrhythm, key shifts |
| 28:55 | **VI · The Chase** | restless interlocking guitars, rock-prog drive |
| 33:25 | **VII · Chant & Bells** | hypnotic, modal, building then opening out |
| 37:45 | **VIII · Pastoral Reprise** | the opening returns, transformed, in a new light |
| 41:20 | **IX · Storm** | the biggest energy — driving prog, tempo pushing, hard modulations |
| ~47:30 | *the false ending* | a grand cadence… a breath of silence… then it bursts back |
| ~48:10 | *…and a Morse-code message tapped on a woodblock* | (listen closely) |
| 48:15 | **X · Hymn** | the main theme, full-hearted: the summit |
| 54:00 | **XI · Homeward** | the river widens to the sea — a long wind-down to one last, luminous D-major chord |

Across the hour the music passes through ~46 sections and **44 tempo changes**
(60–156 bpm), wandering keys (D, G, A, C, F, B♭, E, B) and modes (dorian, mixolydian,
ionian, aeolian, phrygian) — the constant motion is the point.

## The recurring threads

- **The main theme** — a singing folk tune that arches to the octave and home; stated
  by whistle, developed by fiddle and glockenspiel, and crowned in the Hymn.
- **The bell motif** — a stately tubular-bells/glockenspiel figure (Oldfield's
  signature colour) that returns in several keys.
- **The dance motif** — a sprung figure that drives the reels, jigs and chases.

## The sound — a fixed acoustic orchestra

Sixteen GM channels, consistent across the hour so the timbre stays whole: nylon &
steel acoustic guitars (the interlocking heart), banjo, acoustic bass, glockenspiel,
tubular bells, flute/tin-whistle, fiddle, accordion, choir, strings, church organ,
clean electric guitar, pan flute, marimba — and a full hand-percussion/kit on the drum
channel (bodhrán, congas, bongos, shakers, toms, tambourine).

## How it's made

- **`folk.py`** — the engine (built on `../engine.py`): the fixed orchestra, percussion
  grooves, and idiomatic primitives — strum, *interlocking* picked guitars (A ascends
  while B descends, the Oldfield shimmer), bass riffs, an organic folk-melody generator,
  and ~13 section types (pastoral, folk-dance/jig, driving-prog, bells, ambient,
  percussion-jam, anthem, waltz, chase, chant, hush, transition, theme). Themes
  *develop* across long statements — each pass rotates lead voice and register rather
  than looping.
- **`riverwake.py`** — the 60-minute roadmap: the twelve movements, every section's key,
  mode, tempo and progression, the recurring themes, the false ending, the Morse egg,
  and the final chord. A single `SCALE` constant dials the exact running time.

```bash
python3 riverwake.py        # -> midi/Riverwake.mid, prints length + section count
```

## Reviewed & refined

After the first render the piece was put through an independent five-lens analytical
review (form/variety, Amarok-fidelity, harmony, instrumentation, transitions). Its
findings were applied: the chant choir now sounds real voice-led chords instead of a
collapsed octave; the false ending is a true ~3.2-second silence after a grand ringing
cadence (and the hole before the Hymn is closed with a held drone under the Morse); the
"interlocking guitars" are now genuine two-line counterpoint (moving modal hocket, not
one chord echoed); the drum palette is widened (ride, open hat, crash, cowbell,
triangle, claves); pitched parts are folded into their instruments' ranges; and the
key-journey is loosened so the wind-down passes through G-mixolydian and B-aeolian
rather than sitting in one tonic.

*Honest caveat:* this machine has no MIDI synth/SoundFont, so the piece was verified
**structurally** (length, tempo map, per-channel ranges & density, true-silence scan,
voice-leading & range checks, interlock-motion checks) rather than by ear. Audition
through a real acoustic library — it will reward a better fiddle, whistle and
nylon-guitar sound — and tell me what to adjust.
