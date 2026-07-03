# hollowsynth

A zero-dependency Rust MIDI-to-WAV synthesizer, built to give *Hollow Hill*
a far better voice than a stock General MIDI wavetable. Every instrument is
modeled — with one deliberate exception: the piano, solo fiddle and
flute/whistle use **LA synthesis** (the Roland D-50 trick) — a short
public-domain PCM attack transient supplies the first ~200 ms of each note,
then crossfades into the modeled sustain. The ear judges an instrument
mostly by its onset; the hammer strike, bow bite and breath chiff are the
things synthesis fakes worst. The 44 transients (~2.4 MB, trimmed from
VSCO 2 Community Edition, CC0 — see `samples/README.md`) are embedded in
the binary, so the tool stays a single self-contained executable.

```powershell
cargo build --release
.\target\release\hollowsynth.exe "..\Hollow Hill\midi\01 - Hollow Hill, Part One.mid" `
    -o "..\Hollow Hill\audio\01 - Hollow Hill, Part One.wav"
```

Renders ~14 minutes of stereo 44.1 kHz audio in under 20 seconds.

## Options

| flag | default | meaning |
|------|---------|---------|
| `-o <file>` | input with `.wav` | output path |
| `--rate <N>` | 44100 | sample rate |
| `--wet <X>` | 0.32 | reverb return level |
| `--delay <MS>` | dotted quaver at the opening tempo | echo-bus time (`0` disables) |
| `--tail <S>` | 6 | seconds appended for the reverb tail |
| `--no-samples` | — | disable the LA attack-sample layer (pure modeling) |
| `-q` | — | quiet (no progress) |

MIDI pitch bend (±2 semitones) and CC68 (legato/hammer-on-pull-off),
CC93 (chorus send) and CC94 (echo send) are all honoured — see below.

Output is peak-normalised to −1 dBFS, 16-bit PCM stereo with TPDF dither.

## The instrument models

| family | technique | GM programs |
|--------|-----------|-------------|
| **Pluck** | extended Karplus-Strong in **two polarizations** — a sustaining loop plus a faster-decaying, slightly detuned one, so notes decay fast-then-slow with a gentle beat, like a real string. The delay line is now **fractional-tap**, so pitch can *move* while a note rings: **MIDI pitch bend** glides it, and **CC68 legato** retunes an already-ringing string instead of re-picking it — hammer-ons and pull-offs, and slides on the fiddle/winds too (see "Performance" below). Tuned-delay allpass, in-loop damping, pick-position comb excitation, per-note round-robin variation. Acoustics get a **body resonator** (Helmholtz air mode + plate modes); electrics and basses get a **pickup-position comb**; basses also get an envelope-locked **sub-oscillator** for fundamental weight. A dedicated **palm-mute** preset (heavy damping, short decay) lives at program 28 | guitars 24–31 (28 = muted), basses 32–39, harp 46, banjo 104–107 |
| **Modal** | banks of decaying rotation-oscillator partials (no `sin()` in the loop) with strike noise | piano 0–7 (inharmonic partials, velocity-dependent brightness, detuned unisons, a **two-stage decay** — fast strike into a long singing aftersound — under an **LA sampled hammer strike**, 9 zones × pp/mf/f by velocity with **alternating round robins** so repeated notes don't clone), celesta 8, glockenspiel 9, music box 10, vibes 11–13, **tubular bells 14** (hand-tuned chime partials ≈ 2:3:4.2 with hum; strikes jitter so no two ring alike), timpani 47, crystal 96–103 |
| **Organ** | additive drawbar bank + key click + attack chiff + tremulant, per-pipe level variation (+ soft overdrive for rock organ) | 16–23 |
| **SawStack** | detuned polyBLEP saw ensemble — **each layer with its own vibrato rate/phase and a slow random pitch drift**, so a section sounds like players, not one detuned synth → lowpass (strings, pads; the sweep pad's filter is LFO-swept) or → **vocal formant bank** that morphs open at the onset ("mm-ah") | 48–51, 52–54, 80–95 |
| **Wind** | sine + weak harmonics + band-filtered breath that rides the vibrato, chiff, and a pitch **scoop** into each note — under an **LA sampled attack** (real flute onset, 5 pitch zones); bends and CC68 legato slur the scoop instead of re-tonguing | flutes/whistles 72–79 |
| **Bowed** | polyBLEP saw → violin body resonances (280/610/1350 Hz); pitch scoop, bow noise concentrated in the attack, and **bow-pressure brightness** (the tone opens as the envelope swells) — under an **LA sampled attack** (real bow bite, 6 pitch zones × forte/piano by velocity); bends and CC68 legato give one bow stroke across several fingered notes | 40–45 |
| **Drums** | parametric hits: decaying partials with pitch glide (membranes), **inharmonic bell-plate stacks** for cymbals/hats, a two-band snare (shell + wires); harder hits are brighter, and every strike is jittered. The kick now layers a beater knock over a **sub drop** (86→~45 Hz) for real chest weight | GM channel 10 |

Timing realism: sustained families speak slower at low velocity, the way a
gently-bowed or gently-blown note actually starts.

The LA layer (`src/sampler.rs`) picks the nearest pitch zone, repitches it
to the exact target (each zone's root was measured by autocorrelation to
cent accuracy), and crossfades: the transient fades out over the same
window the model fades in, so the model's weaker synthetic onset is masked
by the real one. Targets too far outside the sampled range fall back to
the bare model. `--no-samples` turns the whole layer off. Pitch bend and
legato pass straight through the sample layer to the model underneath —
the sampled attack only ever plays once per slurred phrase.

Distorted guitar (programs 29/30) is handled the way a real rig would be: the
sustaining string voices are summed **per channel** and driven through a
`tanh` waveshaper + cabinet-style tone filter (now run at **2× internal rate**
to roll off the worst of the aliasing), so power chords get their
intermodulation grit.

## Performance: bends, hammer-ons, mutes

Real guitarists barely re-pick every note — they bend, slide, hammer-on and
pull-off. hollowsynth models this at the engine level, not just per-voice:

- **Pitch bend** (`0xEn`) sets a channel-wide frequency multiplier that's
  applied both to new notes and to everything already sounding on that
  channel, so a bend sweeps the whole chord.
- **CC68 ≥ 64** puts a channel into legato mode: a `NoteOn` that arrives
  while exactly one note is still ringing on that channel *retunes the
  ringing voice* instead of spawning a new one — a hammer-on/pull-off on
  guitars and bass (with a soft excitation tap, not a fresh pluck), a slur
  on the fiddle and winds (the scoop glides to the new pitch, no fresh
  bow/tongue attack). CC68 < 64 returns to normal picking.
- **Program 28** is a dedicated palm-mute preset — heavy damping, a short
  decay, and a dull excitation — rather than just a quieter clean guitar.

`material.py`'s `bend()`/`bend_ramp()` and `run()` helpers (in the *Hollow
Hill* composition engine) write these events for rapid-fire runs, wails
and hammered passages; see `part_one.py`'s Stormrise and `part_two.py`'s
reel for examples.

## The mix

- **Channel strips** honour CC7 (volume), CC11 (expression, smoothed — the
  album's swells depend on it), CC91 (reverb send), CC93 (chorus send),
  CC94 (echo send) and CC10 pan — realised as equal-power gain **plus a
  Haas micro-delay** on the far channel, so panned sources localise like
  sources in a room rather than level tricks.
- **Hall reverb**: Freeverb-style tank behind a 24 ms pre-delay and five early
  reflections — attacks stay clear of the wash, and the room has walls. Its
  send is now **highpassed at 150 Hz** so the low end stays dry and tight
  instead of washing out in the tank.
- **Chorus bus**: one modulated delay, quadrature L/R taps; strings, choir,
  organs and pads get ensemble width by program profile.
- **Echo bus**: ping-pong delay timed to a dotted quaver at the song's opening
  tempo, repeats darkening as they bounce — the classic delayed-lead sound on
  electric guitars, whistle and crystal.
- **Sympathetic resonance**: the piano channels feed twelve lightly-damped
  comb resonators (one per pitch class), returned quietly — the other
  strings ringing along, the thing that makes a real piano sound big rather
  than like notes in isolation.
- **Bus glue**: a slow, gentle 2:1 compressor (a dB or two of movement, not
  a squash) plus a whisper of tape-style saturation on the stereo mix, so
  the whole record couples together instead of sitting arithmetically flat.

## The mix

- **Channel strips** honour CC7 (volume), CC11 (expression, smoothed — the
  album's swells depend on it), CC91 (reverb send) and CC10 pan — realised as
  equal-power gain **plus a Haas micro-delay** on the far channel, so panned
  sources localise like sources in a room rather than level tricks.
- **Hall reverb**: Freeverb-style tank behind a 24 ms pre-delay and five early
  reflections — attacks stay clear of the wash, and the room has walls.
- **Chorus bus**: one modulated delay, quadrature L/R taps; strings, choir,
  organs and pads get ensemble width by program profile.
- **Echo bus**: ping-pong delay timed to a dotted quaver at the song's opening
  tempo, repeats darkening as they bounce — the classic delayed-lead sound on
  electric guitars, whistle and crystal.

## Verification (this machine has no ears)

- `cargo test` (16 tests) — MIDI/tempo-map math including pitch-bend decode,
  envelopes, a zero-crossing check that a plucked A4 sounds at 440 Hz (the
  KS delay compensates the loop filter's phase delay, so tuning is
  cent-accurate), a bend test (A4 bent +2 semitones settles near B4), a
  hammer-on test (a ringing string retunes without re-picking), a palm-mute
  decay test, a check that the fiddle's onset scoop settles to true pitch,
  three LA-layer checks (bank parses, sampled attack agrees with the model
  on pitch through the crossfade, no level jump at handover), and a bus-glue
  test (gain reduction on loud material, near-transparent on quiet material).
- Rendered output is checked numerically: RMS profile follows the score's
  dynamic arc, no DC offset, no unintended silence, and no discontinuities
  beyond genuine musical transients (verified by diffing click locations
  against a `--no-samples` render and inspecting raw sample values at
  flagged points).
- **Stereo width, honestly**: the quieter, sparser movements (Dawn, First
  Light) measure close to the pre-v0.5 baseline (correlation near 0). The
  louder, denser sections — Stormrise's chugging guitars and sub-reinforced
  kick, the piano's longer sampled attack — measure more centred than
  before (roughly +0.5 to +0.6 broadband in Part One, down from an initial
  +0.73 after two rounds of fixes: the bass sub-oscillator and piano
  crossfade were both dialed back, and the storm's two rhythm-guitar
  channels are now hard-panned). Some of this is a *correct* side effect of
  requested changes — real mixes keep sub-bass and kick mono/centred on
  purpose — but it's a genuine, not fully eliminated, tradeoff of the fuller
  sound, worth a human listen if the storm and summoning sections feel
  narrower than the rest.

What it has **not** had is a human listen — balance was set by construction
and measurement. All the knobs are named constants: instrument voicing at the
top of `src/voices.rs`, bus levels in `src/engine.rs`.
