# Seven Kinds of Sunlight

An upbeat, through-written SONG (3:54, one track) — verse /
pre-chorus / chorus / middle-eight architecture with odd meters and a
gear-change finale.  D major at 138 bpm; the title is a nod to the 7/8
verses.

## Form

| time | section | meter | what happens |
|------|---------|-------|--------------|
| 0:00 | Intro | 4/4 | the riff alone, filter opening; the band falls in |
| 0:13 | Verse 1 | 7/8 | hummed melody over the 3+2+2 engine |
| 0:38 | Pre-Chorus 1 | 6/8 | the rising lift, toms climbing the kit |
| 0:48 | Chorus 1 | 4/4 | HOOK + counter A + counter B, full voice |
| 1:16 | Turnaround | 4/4 | two bars of the riff |
| 1:20 | Verse 2 | 7/8 | + piano canon, wah funk guitar, detuned double |
| 1:44 | Pre-Chorus 2 | 6/8 | choir II joins the climb |
| 1:54 | Chorus 2 | 4/4 | + the snapped descant, organ, autopan |
| 2:22 | Middle Eight | 5/4 | flute/lead counterpoint, portamento glide |
| 2:40 | Guitar Solo | 7/8 | RPN bend range 12, hammer-ons, whammy dive |
| 3:04 | Drum Break | 7/8→4/4 | band stabs, then the fill library alone |
| 3:13 | Final Chorus | 4/4 | **E major**: the whole stack at once |
| 3:41 | Outro | 4/4 | riff out, stop-time punches, one long ring |

## The machine-verified DNA (`material.py`)

- **A three-voice chorus counterpoint.**  The vocal HOOK (anthem
  skeleton `5 7 6 6 5 5 4 3` over I-V-vi-IV), COUNTER A (the 8th-note
  riff, also the intro/turnaround/outro hook) and COUNTER B (the slow
  inner line) are proven **pairwise consonant on every strong beat**
  (interval set inversion-symmetric — the oracle caught a major 2nd
  hiding as a "consonant" minor 7th during composition, and the notes
  were fixed, not the check).  The final chorus stacks all three plus
  a snapped descant and a sung vocalise — `check_stack` proves every
  layer actually sounds there.
- **A verse canon.**  Verse 2's piano answers the melody one 7/8 bar
  late, a diatonic 4th below, consonant at every downbeat overlap.
- **A middle-eight counterpoint pair** (flute vs gliding lead) in 5/4,
  the two voices trading places at the half-bar, consonant on beats 0
  and 3 of every bar.
- **Driving bass, certifiably**: ≥ 2 note-ons per beat and 5 distinct
  pitches per bar in the chorus cell; the verify layer re-checks the
  written MIDI — ≥ 1.8 notes/beat in every chorus and the ground
  root's pitch class sounding on every chorus bar line (gear change
  respected).
- **The +2 gear change** (D → E) is one argument through the section
  writers; transposition preserves every certified interval.

## The drums

`drums.py` is a groove + fill engine: meter-native grooves for 4/4,
7/8 (3+2+2), 6/8 and 5/4 (3+2), ghost-note snare work, and a five-style
fill library (tom cascade, 32nd ruffs, flams, kick/snare 16th
interplay, scattered kit) rotated through every fourth bar and seeded
through the Score RNG — no two fills identical, every build
byte-identical.  The Drum Break leaves the drummer alone with all five
styles between band stabs; `check_drums` requires tom fills in every
chorus and ≥ 6 distinct drum pitches at ≥ 3 hits/beat in the break.

## MIDI effects inventory

CC70 vowel morph (verses hummed closed-mouth, choruses full "ah" —
A/B-measured at 7× formant openness on identical content), RPN 0 bend
range 12 for the solo (unison bends + a −7 semitone whammy dive,
measured at −6.9 on the rendered stem), RPN 1 fine-tune (the verse-2
lead double sits −5 cents against the ooh choir), CC5/65 portamento
(middle-eight glide lead; the outro bass slide home), channel
aftertouch (pad and hook swells), CC1 (solo vibrato wheel; the
final-chorus organ Leslie spin-up), CC74 wah LFO (verse-2 funk
guitar) + risers (CC74/71 on the sequencer) + the outro pad filter
close, CC64 piano pools, CC68 legato bass runs, echo throws, autopan,
and lyric-lane chorus syllables ("oh", "oh-oh", "ah", "whoa-oh").

## Regenerate / verify / listen

```powershell
python3 build.py             # rebuild midi + album_manifest.json
python3 build.py --verify    # 19 oracles, incl. meters, driving bass,
                            # drums, the counterpoint stack, RPN/bend
                            # hygiene, vowels, dynamics, bounds
```

Listen by rendering with `python3 build.py` (or [ferrosintesis](../../../crates/ferrosintesis/README.md)
directly); that produces the git-ignored build output `listening/Claude Fable 5/Seven Kinds of Sunlight/01 - Seven Kinds of Sunlight.opus`.  Audio verified
numerically: section RMS follows the form (final chorus loudest at
−20.2 dB), no dead air, no discontinuities beyond kick onsets; stem
measurements confirm the dive (−6.9 semis), the gear change (+1.81
semis on the bass fundamental), the Leslie (~5.8 Hz spun up, 15× the
modulation power), the vowel contrast (7×), and the bass drive (1.5×
envelope flux, chorus vs verse).

The brief asks for a new composition rather than a reconstruction of a
named piece. That intent is not a guarantee against incidental similarity.
