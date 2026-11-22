# Lantern Year — composer notes (the album bible)

Ten nights at a lighthouse across one year. Ten composers work **in parallel**,
one track each; this file is the whole shared contract. Read it, then
`material.py` (the album DNA + oracle kit, ~330 lines), then skim `engine.py`
(the toolkit: read the docstring index, then only the helpers you use). Do not
explore the rest of the repo — everything you need is here. One exemplar of the
module shape, if you want one: `../Slipstream/movements/t07_vapour.py` (skim
the first ~200 lines only; do not imitate its music).

**Host facts:** Python is **3.9** (keep `from __future__ import annotations`;
no `match`, no runtime `X | Y`). Standard library only.

## 0. Your job

Write ONE file: `movements/tNN_<stem>.py` (your registry row in
`conductor.REGISTRY` fixes NUMBER / TITLE / FILE / SEED). Make it a piece of
music somebody would choose to listen to twice: a real tune, harmony that
moves, a bass line with its own shape, counter-melody, a dynamic arc with a
true peak and a true hush, idiomatic articulation for every instrument, and an
ending that lands. **About five minutes**: the album window is 285–315 s.

You may write only: your module, and disposable renders under `audio/`. Do
**not** edit `engine.py`, `material.py`, `conductor.py`, `verify.py`,
`build.py`, `analyze.py` or another track; do not run plain `build.py`
(other modules may be mid-edit); do not use git. If you believe a shared file
is wrong, work around it and say so in your report.

## 1. The shared DNA (material.py)

- **THE BEAM** — degrees **1-5-6-5-8** (`material.BEAM_CELL`,
  `play_beam(sc, ch, t0, base, mode, stretch=…)`). The lamp swings out and
  comes home an octave up. Every track states it **at least 3 times**, first
  and last statement at least a third of the track apart, on the channels you
  list in `BEAM_CHANNELS`. The detector (`beam_statements`) is rhythm-free
  and transposition-free: five *consecutive single* note-ons on one channel
  with intervals +7, +s, −s, +5 (s = 1 or 2). So you may play it in any
  rhythm with your own `sc.note` calls — but nothing else may sound a new
  note on that channel between the five, and no chord may start on those
  ticks. Make it *musical* in your idiom (a riff, a jig figure, a bass
  ostinato, a horn call), not a pasted quote.
- **THE HYMN** — `material.HYMN`, 16 bars / 64 beats, one chord per bar
  (`HYMN_CHORDS`, `hymn_chord`), emitters `play_hymn` / `play_phrase`,
  detectors `hymn_statements` / `phrase_statements`. Track 1 states it
  plainly, track 10 crowns it. Tracks 2–9 **may** borrow one phrase (a nice
  touch when it fits — at any stretch, any transposition) but need not.
- **THE LAMP** — one tubular-bell stroke (`LAMP_PROGRAM` 14, `LAMP_PITCH`
  D4). Track 1's first sound, track 10's last. Others may let it toll once.
- **Oracle kit** — `note_ons`, `note_spans`, `cc_lane`, `sounding`,
  `energy(sc, t0, t1, channels=None)` (mean velocity mass per beat — the
  dynamic-arc proxy), `active_channels`, `CONSONANT`. Use these; do not
  re-type them.

## 2. Module contract (build.py / verify.py consume exactly these symbols)

```python
from __future__ import annotations
import sys
import conductor
import engine as en
import material

NUMBER = <int>; TITLE = "<registry>"; FILE = "<NN - Title.mid>"; SEED = <int>
COMMENT = "one-paragraph track description (goes in the MIDI file)"

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Name", t0, t1), ...],       # contiguous; last t1 = END
    tempo_map=[(0.0, BPM), ...],                # beats are QUARTER notes, always
    time_signatures=[(0.0, 4, 4), ...],
    keysigs=[(0.0, sharps, minor)],             # e.g. (0.0, 1, 1) = E minor
    channels=[(ch, "name", program, volume, pan, reverb), ...],
    program_changes=[(9, 0.0, 40)],             # optional: kit select / mid-track swaps
    extra_markers=[(beat, "text"), ...],        # optional
    bank_selects=[(ch, value), ...],            # optional CC0 at beat 0
)

BUILDERS = [_b_one_per_movement, ...]           # len == len(movements); each takes (sc)

BEAM_CHANNELS: set[int]          # where your BEAM statements live
PROGRAM_WHITELIST: set[int]      # exactly the programs you use (setup + changes)
CENTERED_CHANNELS: set[int]      # every channel that must hold CC10 64
NOTE_RANGES: dict[int, tuple[int, int]]   # per-channel [lo, hi] pitch bounds
GAP_WHITELIST: list[tuple[float, float]]  # scored silences (unscored cap 1.5 beats)
BEND_EXEMPT: set[int]            # channels with STATIC bend offsets (usually empty)
DURATION_WINDOW: tuple[float, float]      # FILE seconds, inside (285, 315); keep it tight (±4 s)
BOUNDS_WHITELIST: list[tuple[int, float, float]]  # (ch, lo, hi) seam carry-overs

def oracles(sc, info, spans) -> list[tuple[str, list[str]]]:
    results = material.album_oracles(sys.modules[__name__], sc)   # REQUIRED first
    results.append(("my_oracle_name", fails_list))                # then yours
    return results

def audio_checks(ctx) -> list[tuple[str, list[str]]]: ...        # 2-4 checks
```

A 6/8 bar is 3 beats, a 12/8 bar 6 beats, a 7/8 bar 3.5, a 5/4 bar 5. Track
length in beats ≈ 5 × (quarter-note bpm).

**Oracle-first.** Before the music, write **at least five** track-specific
oracles that pin your brief's headline claims (form, the device, the dynamic
arc via `material.energy`, counterpoint consonance on structural downbeats,
mode purity, pulse/grid, etc.) — then compose until they pass. They must be
able to fail: break the music once and see the oracle go red. `info` is None
under `--check`.

Generic checks that run automatically (verify.py): structure (duration window,
track count = 1 + len(channels), file-vs-Score note parity, tempo/keysig grids,
movement markers), programs (whitelist), bank-select-before-program, pan
(CENTERED_CHANNELS emit only 64), ranges (drum keys must be in 35–81 unless you
declare ch9 in NOTE_RANGES), gaps (> 1.5 beats of total silence fails unless
whitelisted), same-pitch overlaps, bend hygiene (every bending channel
recentred ±0.02 at every movement boundary), movement bounds (each builder's
note-ons inside its own movement; CCs exempt).

## 3. Workflow (absolute paths — your shell does not start in the album)

```
python3 "/Users/md/worktrees/ferrosintesis/20261122-TSK-HUM-fable5-new-10-track-album/albums/fable5/Lantern Year/build.py" --track N --check     # in-memory oracles (fast loop)
python3 "/Users/md/worktrees/ferrosintesis/20261122-TSK-HUM-fable5-new-10-track-album/albums/fable5/Lantern Year/build.py" --track N             # writes midi/<FILE>
python3 "/Users/md/worktrees/ferrosintesis/20261122-TSK-HUM-fable5-new-10-track-album/albums/fable5/Lantern Year/build.py" --track N --verify    # file-backed + all oracles
"/Users/md/worktrees/ferrosintesis/20261122-TSK-HUM-fable5-new-10-track-album/target/release/ferrosintesis" "/Users/md/worktrees/ferrosintesis/20261122-TSK-HUM-fable5-new-10-track-album/albums/fable5/Lantern Year/midi/<FILE>" -o "/Users/md/worktrees/ferrosintesis/20261122-TSK-HUM-fable5-new-10-track-album/albums/fable5/Lantern Year/audio/<NN - Title>.wav" -q
python3 "/Users/md/worktrees/ferrosintesis/20261122-TSK-HUM-fable5-new-10-track-album/albums/fable5/Lantern Year/analyze.py" --track N           # click scan, mono check, your audio_checks
```

Order matters: edit → `build.py --track N` (writes) → `--verify` → render →
`analyze.py`. `--verify` never writes the file. The synth binary is already
built; do not run cargo. A verification stem for one channel:
`… --solo <channel 1-16> -o stem.wav`. **Done means:** `--verify` prints
`RESULT: PASS`, the render exists, and `analyze.py --track N` prints
`AUDIO: PASS` — and you have *listened with numbers* (see §6).

## 4. The synth (ferrosintesis) — what sounds good

All GM programs 0–127 are voiced. Catalog-proven colours:

- **Keys:** 0 piano (`bank_selects` CC0: 0 = our B1 upright, 2 = Salamander
  grand, 3 = Steinway B), 4 Rhodes, 5 FM EP, 7 clavinet, 8 celesta,
  9 glockenspiel, 10 music box, 11 vibraphone (motor tremolo), 12 marimba,
  13 xylophone, 14 tubular bells, 108 kalimba.
- **Organs / reeds:** 16–18 drawbar/rock organs (CC1 = Leslie speed —
  `en.leslie`), 19 church organ (CC0=2 → the cathedral pipe organ with its own
  long reverb), 20 harmonium, 21 accordion, 22 harmonica.
- **Guitars / basses:** 24 nylon, 25 steel (CC0=1 fingerstyle; **mandolin** =
  program 25 + `sc.cc(ch, 32, 96, 0.0)`), 26 jazz, 27 clean, 28 palm-mute,
  29 overdrive / 30 distortion (CC0=1 → the sustaining DRIVE_LEAD voice: give
  held notes a CC1 bloom, velocities 85+), 32 upright bass, 33 fingered,
  34 picked, 35 fretless, 38/39 synth bass.
- **Strings:** 40 violin, 41 viola, 42 cello, 43 contrabass, 110 fiddle
  (waveguide solo bows: CC68 legato slurs, bends work), 44 tremolo,
  45 pizzicato, 46 harp, 47 timpani, 48/49 string ensembles, 52 choir aahs /
  53 oohs (CC70 vowel: 0 = mm, ~45 = oo, ≥ 80 = ah — `en.vowel_curve`),
  55 orchestra hit.
- **Brass / reeds / winds:** 56 trumpet, 57 trombone, 58 tuba, 59 muted
  trumpet, 60 french horn, 61 brass section; 64–67 saxes, 68 oboe, 69 english
  horn, 70 bassoon, 71 clarinet; 72 piccolo, 73 flute, 74 recorder, 75 pan
  flute, 78 whistle, 79 ocarina. CC11/CC2 open brass and reed timbre; CC1 is
  vibrato; CC68 legato.
- **Synths:** leads 80 square / 81 saw (CC1 vibrato, CC68 legato,
  `en.portamento_on`), pads 88–95 (89 warm, 91 choir pad, 95 sweep), FX 96
  rain (a real recorded downpour), 98 crystal, 99 atmosphere, 102 echoes,
  103 sci-fi (a falling laser).
- **SFX (hold a key; pitch ignored):** 122 **seashore** (surf swell), 121
  breath, 123 bird tweet. Use sparingly and quietly as weather.
- **Percussion voices:** 112 tinkle bell, 114 steel drums, 115 woodblock,
  116 taiko, 117 melodic tom, 118 synth drum, 119 reverse cymbal.
- **Drums (ch 9):** default = the sampled acoustic kit (no program change).
  `program_changes=[(9, 0.0, 40)]` = **brush kit**; `24` = synth kit;
  `25` = the older parametric kit. GM keys: 35/36 kick, 37 side stick,
  38/40 snare, 39 clap, 41–50 toms, 42/44/46 hats, 49/57 crash, 51/59 ride,
  53 ride bell, 54 tambourine, 56 cowbell, 69 cabasa, 70 maracas, 75 claves,
  76/77 woodblocks, 80/81 triangle.
- **Controllers:** an unauthored controller is inert. CC7 volume, CC11
  expression (`en.expr_curve` — use it: swells are what make sustained
  voices live), CC10 pan, CC91 reverb, CC93 chorus, CC94 echo
  (`en.echo_throw`), CC74/71 filter cutoff/resonance (`en.cc_curve`,
  `en.wah`), CC64 sustain (`en.sustain`), pitch bend ±2 (`sc.bend`,
  `en.bend_ramp`, `en.vibrato`), `en.bend_range` for wider bends.

**Mix rules of thumb.** The render is loudness-normalised, so only *relative*
balance matters. Lead voices volume 100–118, beds 78–95. Keep bass, kick and
the main lead centred (list them in `CENTERED_CHANNELS`). Pan the rest inside
**34..94** — the synth's pan adds a Haas micro-delay, and hard-panned doubles
of the same line collapse in mono (analyze.py fails > 2 dB mono loss). Reverb
sends 20–45 for rhythm, 55–80 for beds and distance. Humanise: leave the
default `jt`/`jv` on unpinned lanes; use `jt=0` on anything an oracle
pins tick-exactly and on notes at movement edges.

## 5. Trip-wires (each one has already cost somebody a debug cycle)

1. **RNG stream**: every `sc.note` with jt/jv advances the shared seeded RNG.
   Emit in a deterministic order; never interleave emission conditionally on
   unordered data (iterate lists, not sets/dicts-of-sets).
2. **Jitter leaks across boundaries**: a jt>0 note at a movement edge can land
   outside the builder's window → check_movement_bounds fails. Use jt=0 at
   edges.
3. **Same-pitch overlaps** on one channel fail check_overlaps (pads + repeated
   notes are the usual culprit): shave the earlier note, or split lanes.
4. **DURATION_WINDOW includes the 2-beat end pad** at the final tempo, and the
   file ends at the last note-off, not at END — let the last notes ring to END.
5. **check_gaps is global**: any stretch with nothing sounding anywhere for
   > 1.5 beats must be in GAP_WHITELIST. A dramatic silence is fine — declare it.
6. **CC0 must precede the program change at the same tick** — `bank_selects`
   handles beat 0; don't author your own CC0 at tick 0.
7. **Bends**: zero every bending channel before each movement boundary.
8. **Sixteen channels, ch 9 is drums.** A mid-track instrument swap is a
   `program_changes` entry (and must be in the whitelist).
9. **Audio thresholds**: average RMS lies for sparse-but-loud passages —
   compare dB over trimmed inner windows and keep margins ≥ 3 dB.
10. **Presence in the MIDI is not audibility in the render.** A soft voice
    under a pad disappears. Check stems.

## 6. Listen with numbers

This box has no ears; you do the listening numerically. After rendering:
compare section loudness with `ctx.rms`/`ctx.db` in `audio_checks` (hush vs
peak ≥ 6 dB apart; second peak ≥ first), and solo your lead (`--solo`) to
confirm it is not buried: its stem should sit within ~12 dB of the full mix
in the passages where it leads. If the hook is inaudible, fix the mix, not
the oracle.

## 7. The ten nights

Each brief fixes key, tempo, meter, idiom and the headline device; everything
else is yours. Palettes are suggestions — the claims in **bold** are the ones
your oracles must pin.

**T1 — First Lighting** (January dusk; chamber folk). D dorian, ♩ = 92, 4/4.
Piano, cello, violin, clarinet, harp, fingerstyle steel guitar, soft strings,
upright bass; brushes only late if at all. **The album's first sound is the
LAMP bell alone; the first melodic notes are the BEAM, unaccompanied.** Then
the **complete HYMN, plainly, at stretch 1 in D dorian** (the listener must be
able to learn it here), a variation with a **verified counter-melody**, a
brighter middle that leaves the tune, and the **HYMN again, fuller and louder
than the first time**. End quietly, the lamp bell tolling — the year begins.
Intimate, warm, unhurried.

**T2 — Northeaster** (February storm; prog rock). E aeolian, ♩ = 150,
**7/8 verses (2+2+3) against 4/4 choruses**. Overdriven lead guitar (29,
CC0=1) and a distortion rhythm guitar (30), rock organ with Leslie, picked
bass, the acoustic kit at full stretch, brass-section stabs, timpani, a quiet
seashore bed, reverse-cymbal swells. The **BEAM is the 7/8 riff**. Two storm
peaks, **the second verifiably bigger**; between them **the eye of the storm**
— eight or more bars stripped to almost nothing; an organ solo and a guitar
solo with real bends. Ends on a slammed unison.

**T3 — Fog Signal** (March; ambient). C lydian, ♩ = 60, 4/4. Warm and sweep
pads, choir with slow vowel morphs, vibraphone, celesta/crystal droplets,
fretless bass, a bowed cello line, seashore breathing underneath throughout.
**The foghorn** — a low two-note horn/tuba call — **returns on a strict period
all the way through** (the one clock in the fog). **Nothing ever rises above
mezzo-piano** (a velocity ceiling), **harmony moves no faster than once every
8 beats**, **lydian purity** (F♯ featured, no F♮). The BEAM, very slow, in the
horn or cello. A Morse lane may tap `FOG`. No drum kit. Make stillness
interesting: long overlapping phrases of unequal length so nothing lines up
twice.

**T4 — The Mail Boat** (April; folk dance). G ionian, **6/8 at dotted-♩ = 108**
(tempo 162, 3 beats to the bar). Fiddle, accordion, mandolin, whistle, strummed
steel guitar, upright bass, tambourine/woodblock/hand-drum feel on the kit.
A set of **two jigs, each AABB with its repeats exact** — the first in G, the
second in a related mode (E dorian or D mixolydian) — then the first tune
back **a tone higher in A** for the last round. **The BEAM is the first jig's
opening figure.** **The tune is handed between at least three lead
instruments**; accompaniment thickens each round; a **strict jig grid** (every
onset on the eighth-note lattice). A slight accelerando into the final round;
ends on a stamped tonic. Pure joy.

**T5 — Glass Calm** (midsummer; mallet minimalism). A ionian, ♩ = 132, 4/4.
Two marimbas, vibraphone, glockenspiel, celesta, Rhodes, harp, a string swell,
flute, soft bass; no kit beyond a shaker or brushed pulse. **The process:**
both marimbas play the same short cell **built from the BEAM's pitches**; one
of them slips ahead by an eighth every few bars until, after a full cycle,
**they are back in unison** — every stage tick-verified. Over it, the harmonic
field turns slowly (A → F♯m → D → E), and a **long-breathed melody** (flute,
then strings) floats in notes far longer than the pulse. **An unbroken
eighth-note pulse** for most of the track; one great swell and a clear return.
Bright, weightless, hypnotic — and it must still *go somewhere*.

**T6 — False Lights** (July, no moon; 5/4 noir). F♯ phrygian, ♩ = 104,
**5/4 (3+2)**. Fretless bass ostinato, muted trumpet, baritone sax, vibraphone,
jazz guitar, cello, low piano, tremolo strings, the **brush kit**. Wreckers on
the headland show a lantern to lure ships in: **the BEAM appears first
corrupted — its fifth flattened to a tritone (+6, +s, −s, +6) — at least
twice, and the true BEAM is withheld until after them**; when the true cell
finally arrives it should feel like the real light cutting through. The
phrygian ♭2 (G♮) leans on the tonic throughout. A trumpet solo over the
ostinato; a tense tutti; an unresolved fade. Smoky, patient, dangerous.

**T7 — Perseids** (August meteor shower; electronica). B aeolian, lifting to
D major for the peak, ♩ = 126, 4/4. Saw and square leads (portamento, CC1
bloom), synth bass, pads, crystal arpeggios, echo throws, CC74 filter sweeps,
the **synth kit** (program 24). **The BEAM is the arpeggio's seed.**
**Meteors** — fast falling runs (glockenspiel/crystal/sci-fi) at irregular
moments — **grow in density to a verified peak** during the second drop.
Build → drop → breakdown → bigger build → **bigger drop (verified)** →
afterglow. Four-on-the-floor in the drops, broken beats elsewhere. Wide-eyed,
propulsive, shimmering.

**T8 — Equinox Gale** (September; orchestral scherzo). C aeolian with the
raised leading tone at cadences, **3/4 one-in-a-bar, ♩ = 174**. Full
orchestra: strings (ensemble, solo violin, cello, contrabass, pizzicato,
tremolo), trumpet, horns, trombone, tuba, piccolo/flute, oboe, clarinet,
bassoon, timpani, harp, orchestral percussion on the kit (bass drum, snare,
cymbals — no rock beat). **Scherzo – Trio – Scherzo – Coda**: the trio is
calmer and in the major (**verifiably quieter**), and there the horns **quote
a phrase of the HYMN**; the scherzo's return is **bigger than its first
statement**; the coda presses the tempo up. **Hemiolas** (2-against-3 across
bar pairs) at verified cadence points. The BEAM as a brass call and in the
basses. Ferocious, exact, exhilarating.

**T9 — The Long Watch** (November, small hours; slow blues). B♭, **12/8 at
dotted-♩ = 56** (tempo 84, 6 beats to the bar; a 12-bar chorus is 72 beats).
Rhodes, tenor sax, drawbar organ with Leslie, walking upright bass, brush kit,
jazz-guitar comping, muted trumpet, vibraphone. Intro, then **choruses on a
verified 12-bar form** (bass roots on the bar lines: I-IV-I-I / IV-IV-I-I /
V-IV-I-V), **each chorus led by a different soloist**, one **stop-time
chorus**, a last chorus with everyone, and a tag ending on a rich B♭ chord.
**Everything sits on the triplet lattice.** Blue notes (♭3, ♭5, ♭7) in the
solos; the BEAM is the turnaround lick (the major sixth is right at home in a
blues). Tired, tender, unhurried — the best playing at the lowest volume.

**T10 — Last Lighting** (December; the finale). D dorian **turning to D major
(ionian)**, ♩ = 88 rising to 96, 4/4. The lamp bell and piano from T1;
cathedral organ (19, CC0=2), choir with vowels, strings, horns and brass
section, timpani, harp, a soaring overdriven lead guitar (29, CC0=1), the full
kit. Open as T1 opened (**the LAMP bell, then the BEAM**), state the **HYMN
complete in D dorian**, quietly, on the organ; build; **turn the key signature
to D major** and crown the **HYMN complete in D ionian, tutti** — verifiably
the loudest music of the track — with a **descant counter-melody consonant on
every bar line**. A last BEAM climbing through the octaves, and **the final
sound of the album is the LAMP bell alone**, as the first was. Earn the
ending.
