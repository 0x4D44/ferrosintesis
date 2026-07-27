# The Signal Fire — movement map

One continuous 16:52 instrumental. A beacon is lit at dusk, catches, blazes,
and is answered. Cross-bred from four corners of the Oldfield catalogue:
*Incantations Part IV* (the long guitar build), *The Songs of Distant Earth*
"Ascension" (ambient pools, the slow filter-opening, the major-mode lift),
*Tubular Bells III* (minor-key drive, four-on-the-floor under pealing bells)
and *The Millennium Bell* "Mastermind" (the funk engine: riff bass, wah
guitar, a Hammond whose Leslie spins up).

All material is original. The piece's DNA is deliberately small: **one bass
riff in three rhythmic guises** (its degree skeleton `1 8 7 5 6 4 5 ♭7 1` is
machine-checked identical across all three), and **three themes composed
over the same Am|G ground** so the finale can stack them in counterpoint —
also machine-checked, chord tones on every downbeat.

| # | Movement | Starts | Key / meter / tempo | What happens |
|---|----------|--------|---------------------|--------------|
| 1 | **Signal** | 0:00 | A aeolian→dorian, 4/4, 72 | Sweep pad opens its filter across the whole movement (CC74, the *Ascension* trick); pedalled piano pools; crystal sparks thrown into the echo; fretless bass slides the riff skeleton in slow motion; the whistle sings Theme A far away. At 1:20 the dorian F♯ is admitted and the light changes. A woodblock taps **CQ CQ CQ** in Morse — a beacon calling anyone. A kick-drum heartbeat accelerates the tempo into… |
| 2 | **Ignition** | 2:25 | A dorian, 4/4, 100 | The funk engine assembles one part per 8 bars: kit, riff bass (with ghost sixteenths), palm-mute chug left, **wah guitar** right (a CC74 LFO — the *Mastermind* sound), Hammond stabs whose **Leslie audibly spins up** into every peak (CC1). Theme B call-and-answer between organ and guitar, then antiphonal L/R guitar cells. A stripped break rebuilds into the first electric-lead wails — attackless volume swells. The bass pivots onto the 10/8 riff in D… |
| 3 | **The Lattice** | 5:27 | D dorian, 10/8 (3+3+2+2), 108 | The riff dissolved into **three interlocking guitars** — steel, nylon, clean each play an incomplete line; only together do they form the riff (*Incantations*). Cross-accents flip 3+3+2+2 / 2+2+3+3 by cycle. Tremolo mandolin doubles the accents, the fiddle re-phrases Theme B across the cycles, organ flutes hold Theme C beneath, and a 3-beat crystal loop drifts across the 5-beat metre, auto-panning as it realigns every 15 beats. Tutti build, then a bass walk D–C–B–A hands over… |
| 4 | **The Long Climb** | 8:25 | A dorian, 4/4, 92→112 | THE solo. Over an Am‖G ground (strummed steel, palm-mute roots, riff bass whose fills grow into a countermelody), the lead guitar climbs through **five waves**: lyrical Theme A paraphrase → unison bends against a second guitar → **+6-cent double-tracking hard left/right** with the first machine-gun runs → runs against held wails, choir and Leslie-fast organ → octave-doubled hammer-on chains to B6. Strings, choir, mandolin, flute and glockenspiel terrace in every 16 bars; the tempo creeps +2 bpm every 32 beats. A four-octave ascent, then the whole texture **bends up two semitones** into… |
| 5 | **Ascension** | 13:18 | A ionian, 4/4, 112 | Arrival. Four-on-the-floor, the riff augmented in half-time, and the **tubular bells peal Theme A** (augmented ×2) over strings and choir singing Theme C — the counterpoint the material was designed for — while two guitars interlock sixteenth figuration and the lead answers with Theme B wails harmonized in thirds and sixths. Second peal brighter than the first. A IV–V–I cadence with suspensions, then a full stop: one bell and the pad ring across the silence… |
| 6 | **Afterglow** | 15:48 | A ionian, 4/4, rit. 112→66 | The bookend. The sweep pad returns and its filter **closes**; nylon guitar restates Theme A intimately over fingerpicked steel; fretless slides; the whistle echoes the last phrase. The woodblock answers the opening beacon: **K** ("go ahead"). One final bell on A, three crystal pings, and a bare A–E fifth fades to silence. |

## The controller writing (why it sounds like Oldfield)

The MIDI leans hard on continuous controllers — the piece carries ~9,900
controller/bend events alongside its 16,539 notes:

- **CC11 violining** — the lead's first entries have no attack, only bloom.
- **Pitch-bend vocabulary** — slides into fretless notes, delayed vibrato,
  quarter-tone curls, unison bends, pre-bend releases, a +6-cent constant
  detune on the double-track channel, and one whole-texture bend at the
  M4→M5 seam.
- **CC68 legato** — hammer-on machine-gun runs (the synth retunes ringing
  strings instead of re-picking).
- **CC74 filter** — the M1 opening and M6 closing bookends; the M2 wah LFO.
- **CC1 mod wheel** — vibrato depth on leads; on the organ it morphs the
  tremulant, so the Leslie audibly spins up and down with the music.
- **CC64** — real pedalled piano pools.
- **CC91/CC94 rides** — the piece starts far away (reverb 80+) and arrives
  nearly dry at the climax (35); phrase-final notes are thrown into the
  ping-pong echo and pulled back.
- **CC10** — antiphonal call-answer pairs, the lattice spread 25/64/103,
  and the crystal's slow autopan.
- **Tempo as expression** — the ignition spin-up (72→100 under an
  accelerating heartbeat), the +2 bpm-per-32-beats creep through the Climb,
  the closing ritardando.

## Verification

`python3 build.py --verify` runs eight oracles: structure, the material's
counterpoint/skeleton promises, the controller inventory, bend hygiene,
note ranges, the six-movement dynamics arc (mean velocity strictly ordered
Signal < Afterglow < Lattice < Ignition < Climb < Ascension, density peaking
in Ascension), silence gaps, and per-movement bounds. `python3 analyze.py`
then measures the rendered WAV: RMS/correlation/centroid per movement,
click scan, silence scan. All green at commit time.
