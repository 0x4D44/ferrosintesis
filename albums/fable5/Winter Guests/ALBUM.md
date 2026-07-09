# Winter Guests — movement map

A two-part instrumental (9:26 + 9:02) in the Mike Oldfield idiom with two
guest sorties made to belong: **ABBA** (*The Visitors*' cold sequenced
arpeggios and paranoia; *Super Trouper*'s stacked-thirds choruses,
off-beat piano octave comping and the truck-driver gear change) and the
**Crash Test Dummies** (*Mmm Mmm Mmm Mmm*'s low wordless baritone hum).

The guests are *movements*, not pastiche — everything shares one DNA. There
is a single **Guest theme** that lives three lives, all machine-verified in
`material.py`: **hummed** low and wordless (CTD), stacked as a **parallel-
thirds pop chorus** (ABBA), and unwound as an **Oldfield guitar line** — all
three reducing to the same strong-beat skeleton `1 5 2 1 3 7 4 1`. The piece
opens in E minor and closes in E major (a parallel-major arc); the ABBA gear
change from D to E in Part Two is what carries the house from cold to warm.

## Part One — the cold half (E minor)

| Movement | Starts | Guest | What happens |
|----------|--------|-------|--------------|
| **Frost** | 0:00 | The Visitors | A cold sequenced arpeggio with a paired **filter + resonance sweep** (CC74 opening, CC71 rising), a pad that **swells from inside** on aftertouch, portamento fretless pedal-tones, an icy music box. At 176 the choir gives the **first low hum** (CC70 = "mm") — the guests knock. |
| **The Humming** | 2:46 | Crash Test Dummies | The heart. The theme hummed low over a **harmonium on the sostenuto pedal** and **una-corda piano**; a second choir joins a third above in "oo"; the humming syllables are written as **lyric events** players display. Warms a shade (dorian F♯), then ends on an **unresolved half-cadence**. |
| **Footsteps in the Hall** | 6:12 | The Visitors | 7/8 (3+2+2), relentless. A **portamento synth lead** with a **±12-semitone whammy** dives and screams (RPN bend-range), the hum turned anxious. Part One ends unresolved — the guests are inside. |

## Part Two — the warm half (D major → E major)

| Movement | Starts | Guest | What happens |
|----------|--------|-------|--------------|
| **Searchlight** | 0:00 | Super Trouper | Four-on-the-floor with the classic **off-beat piano octave comp**; the theme sung as a **chorus stacked in thirds** (CC70 = "ah") with glock doubling the hook; a breakdown holds "oo" under a long aftertouch crescendo — then the **ABBA gear change up to E major**, and the chorus blazes a tone higher. |
| **The Glass Ballroom** | 3:47 | the apotheosis | All three guises of the theme sound **at once**: tubular bells peal it augmented, the choir stacks the chorus, a low choir hums it, and the guitars figurate between — over a disco pulse, with a **fine-tuned double-tracked** lead hard-split L/R. The ballroom breathes at a breakdown, then the second peal and a big cadence. |
| **Last Light** | 7:35 | the farewell | Una-corda piano and nylon; the fretless slides; and the **final hum finally resolves to the tonic** Part One refused — "(goodnight)" in the lyrics. One warm bell, and a bare open fifth fades to silence. |

## The controller writing (v0.7 showcase)

Winter Guests exists partly to exercise ferrosintesis v0.7's new expression:

- **CC70 vowel morph** — the choir is an authorable wordless vocalist: "mm"
  for the CTD hum, "oo" for the inner harmony, "ah" for the ABBA choruses.
- **RPN 0 bend range** — ±12 on the Visitors synth lead for whammy dives,
  while everything else stays ±2.
- **RPN 1 fine-tune** — honest double-tracking (the ABBA lead is two takes
  a few cents apart) without spending the pitch-bend controller.
- **CC5 / CC65 portamento** — the icy lead glide and the fretless slides.
- **CC74 + CC71** — cutoff *and* resonance together: real analog sweeps.
- **Channel aftertouch** — crescendo *inside* a held note (pads, choir).
- **CC66 sostenuto** — the harmonium holds a pedal-point under moving chords.
- **CC67 una corda** — the soft, dark piano of the intimate verses.
- **Lyric metas** — the humming syllables, displayed by MIDI players.
- Plus the v0.6 vocabulary: violining swells, Leslie spin-up, echo throws,
  the reverb distance arc.

## Verification

`python build.py --verify` runs 14 oracles per part: structure, the
material's tri-guise/hummable/counterpoint promises, the controller
inventory (vowels, RPN well-formedness, pedals, portamento, aftertouch),
RPN-aware bend hygiene, ranges, the per-part dynamics arc, gaps, bounds,
lyric and key-signature presence. `python analyze.py <wav> --track N` then
measures each render. All green at commit time.
