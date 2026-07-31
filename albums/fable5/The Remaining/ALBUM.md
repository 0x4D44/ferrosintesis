# The Remaining — track notes

An album by **Claude Fable 5** (2026). Five elegies for piano, strings, choir
and quiet electronics in the idiom of Max Richter's score for *The Leftovers*
— grief-laden piano ostinati, string suspensions, sub-bass drones, long
additive builds, sudden intimate drops. The brief asks for new material; the
album writes in the *vocabulary* of that idiom and quotes nothing. Five
tracks, ~27 minutes.

The story arc is machine-verified: an unexplained departure takes part of the
music away mid-phrase; the remaining voices carry on around the hole; the
final track brings the departed line home and finishes its interrupted
phrase. Four devices bind the record, all pinned in `material.py` and proven
by the oracles in each track's module:

- **THE GROUND** — Dm–B♭–F–C, one chord per bar, each entry *suspended* and
  sighing down by step (4-3/9-8). The finale turns it major (D–A–Bm–G) and
  the sighs invert to resolve upward.
- **THE VIGIL THEME** — six notes that never reach home: every statement in
  tracks 1–4 ends on degree 2, E, "the waiting tone". Only the finale may
  append the seventh note — the tonic the album withholds for 25 minutes.
- **THE DEPARTURE FIGURE and THE HOLES** — an eight-quaver broken-chord piano
  ostinato that loses quavers {3, 6} at the departure. T4 replays it still
  missing the same notes; T5 finally fills them.
- **THE DEPARTED LINE** — a 12-note violin II phrase cut off after note 7 in
  T1, mid-flight, no cadence. T5 states all 12 notes verbatim — the same
  pinned data — and the phrase is finished.

| # | Track | Time | |
|---|-------|------|---|
| 1 | **October the Fourteenth** | 5:26 | The departure itself. Solo-piano ostinato over the ground, then an additive build — cello, viola sighs, violin II beginning the departed line, violin I on the vigil theme — until, on a mid-bar quaver at ≈2:57, violin II is cut at note 7, the viola dies on an unresolved suspension, and 2.5 beats of total silence are scored. The piano resumes alone, holed. Vigil coda on a bare D–A fifth, the waiting tone held twenty beats. D minor, 66 bpm rubato. |
| 2 | **The Ninety-Eight** | 5:13 | Elegy for those who remain — a string chaconne with no piano until the coda. Contrabass and cello walk the ground for 90 unbroken bars beneath six variations: bare fifths, the suspensions blooming, the theme augmented ×2, a one-bar canon at the lower fifth, a descant peak, and a thinning — voices leaving one per cycle while the ground refuses to stop. The piano's only entrance: four un-holed figures, pp; then a lone violin holds E. D minor, 3/4, ≈60 bpm. |
| 3 | **Static** | 4:29 | The searching — the album's one pulse track, dry and close, deliberately metronomic (a single tempo event, 112 bpm). An unbroken synth-bass quaver pulse under a dry solo violin spinning the departure figure at double speed, phrases stretching 4→8→16; a woodblock taps `REMEMBER US` in Morse, twice, buried under the pulse. It ends interrupted mid-bar on quaver 6 — the violin caught on the theme's first three notes — one beat of nothing, then a single dry tap. A minor. |
| 4 | **The Empty House** | 4:42 | Memory, interior. The vigil theme inverted about its own third over left-hand tenths and a sostenuto-caught low D; a celesta music box playing the theme in diminution loses one note per repeat (6→3 — the waiting tone E is the first thing forgotten) over the piano's still-holed figure; a choir hums on closed vowels, never opening; and the last movement is a stopped clock — one repeated E decelerating 54→40 into irregular silence, then a lone bass D. D minor, heavy rubato. |
| 5 | **Homeward** | 7:19 | The return. A six-cycle additive procession over an organ pedal; one bare bar of open D with no third, and the ground turns major, its sighs resolving upward. Then the album's payoff, machine-verified: 44 downbeat-consonant bars of quadruple counterpoint — the piano figure with its holes filled, the theme in D major, augmented ×2 and diminished ÷2 — while violin II returns to finish all twelve notes of the departed line and the choir opens to "ah" for the first time. Everything falls away to solo piano and the album's single degree-1 arrival: A–G–F♯–G–F♯–E–**D**, into a D-major-add9 where the waiting tone is finally a consonance. D minor → D major, 63→72 bpm. |

Oracle-first, per the house method: every headline claim above exists as a
falsifiable check in the track's module (`movements/tNN_*.py`) — around a
hundred structural oracles across the album, plus per-track audio oracles
measured on the rendered waveforms. The pieces were composed *to pass them*.

See `README.md` for how to rebuild, verify, render and listen.
