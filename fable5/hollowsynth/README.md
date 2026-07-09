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
| `--solo <list>` | all | render only the listed 0-based channels (e.g. `11` or `12,13`) — muted channels lose their notes but the tempo map stays, so the output lines up with the full mix; for verification stems |
| `-q` | — | quiet (no progress) |

MIDI pitch bend (±2 semitones by default, RPN-adjustable), RPN fine tune, CC1
(mod wheel: vibrato, or Leslie speed on organs), channel aftertouch, CC5/CC65
portamento, CC64 (sustain pedal), CC68 (legato/hammer-on-pull-off), CC74
(brightness/wah), CC93 (chorus send), CC94 (echo send) and CC0 (bank select —
an alternate orchestral bank, see Performance below) are all honoured — see below.

Output is peak-normalised to −1 dBFS, 16-bit PCM stereo with TPDF dither.

## The instrument models

| family | technique | GM programs |
|--------|-----------|-------------|
| **Pluck** | extended Karplus-Strong in **two polarizations** — a sustaining loop plus a faster-decaying, slightly detuned one, so notes decay fast-then-slow with a gentle beat, like a real string. The delay line is now **fractional-tap**, so pitch can *move* while a note rings: **MIDI pitch bend** glides it, and **CC68 legato** retunes an already-ringing string instead of re-picking it — hammer-ons and pull-offs, and slides on the fiddle/winds too (see "Performance" below). Tuned-delay allpass, in-loop damping, pick-position comb excitation, per-note round-robin variation. Acoustics get a **body resonator** (Helmholtz air mode + plate modes); electrics and basses get a **pickup-position comb**; basses also get an envelope-locked **sub-oscillator** for fundamental weight. GM 35 fretless adds an envelope-following mid formant that blooms open into the note's onset — the "mwah" rather than a static dark bass preset. A dedicated **palm-mute** preset (heavy damping, short decay) lives at program 28 | guitars 24–31 (28 = muted), basses 32–39, harp 46, sitar 104, banjo 105, shamisen 106, koto 107 |
| **Modal** | banks of decaying rotation-oscillator partials (no `sin()` in the loop) with strike noise; the partial bank retunes phase-continuously for pitch bend, RPN fine tune, portamento and aftertouch vibrato. GM 47 timpani adds a struck-head pitch settle, velocity-bright upper modes, per-strike balance variation, and note-off release that lets short hits ring | piano 0–7 (inharmonic partials, velocity-dependent brightness, detuned unisons, a **two-stage decay** — fast strike into a long singing aftersound — under an **LA sampled hammer strike**, 9 zones × pp/mf/f by velocity with **alternating round robins** so repeated notes don't clone), celesta 8, glockenspiel 9, music box 10, vibes 11, **wood bars 12–13** (marimba/xylophone with short key-scaled decays and band-passed mallet clicks), **tubular bells 14** (hand-tuned chime partials ≈ 2:3:4.2 with hum; strikes jitter so no two ring alike), timpani 47, crystal 96–103, kalimba 108 |
| **Organ** | additive drawbar bank + key click + attack chiff + tremulant, per-pipe level variation (+ soft overdrive for rock organ); pipes retune phase-continuously for pitch bend, RPN fine tune, portamento and aftertouch vibrato while CC1 remains Leslie speed | 16–23 |
| **SawStack** | detuned polyBLEP saw ensemble — **each layer with its own vibrato rate/phase and a slow random pitch drift**, so a section sounds like players, not one detuned synth. Strings and choir also answer authored **CC1 vibrato** and **CC68 legato**; pads keep their normal retriggering. The stack feeds a lowpass (strings, pads; the sweep pad's filter is LFO-swept) or a **vocal formant bank** that morphs open at the onset ("mm-ah"). Choir-pad 91 stays on the old pad path unless its channel authors CC70, then it uses the same vowel-morph formant bank. | strings 48–51, choir 52–54, pads 88–95 plus sustained FX 97/99/101/103 |
| **OrchHit** | one-shot orchestral stab: octave-stacked detuned saw ensemble, low thump, and a short noisy bite with fast decay | orchestra hit 55 |
| **Brass** | per-player lip-valve saws (2× oversampled) through a fixed bore/bell body, an envelope-tracked **"waa"** brightness that opens with loudness, an onset pitch **scoop** and flutter-tongue **growl**. **CC11 breath** opens the timbre, **channel aftertouch** adds growl; **CC1** vibrato and **CC68** legato as elsewhere. Section/synth-brass get section-width chorus | trumpet 56, trombone 57, tuba 58, muted trumpet 59, french horn 60, brass section 61, synth brass 62–63 |
| **Reed** | a band-limited **variable-duty pulse** source (a square for the clarinet's hollow odd spectrum, a narrow pulse for the double reeds' buzz) shaped by a tanh over-blow, a per-program **formant bank**, tongue **chiff** and breath onset, and control-rate vibrato. Velocity opens the timbre; saxes get a touch of slap echo. CC1/CC68 as elsewhere | soprano/alto/tenor/bari sax 64–67, oboe 68, english horn 69, bassoon 70, clarinet 71 |
| **Lead** | the SawStack voiced for a synth lead — **fast velocity-tracked attack, short release, a velocity-tracked filter** (harder = brighter), and a band-limited **square/pulse** oscillator for the square-lead class. No always-on vibrato: the **CC1 mod wheel** adds it, and **CC68 legato** slurs one note into the next. Per-program voicing (square, saw, calliope, chiff, charang, voice, fifths, bass+lead) via oscillator shape, count, detune and cutoff | synth leads 80–87 |
| **Wind** | sine + weak harmonics + band-filtered breath that rides the vibrato, chiff, and a pitch **scoop** into each note — under an **LA sampled attack** (real flute onset, 5 pitch zones); bends and CC68 legato slur the scoop instead of re-tonguing | flutes/whistles 72–79 |
| **Bowed** | polyBLEP saw → violin body resonances (280/610/1350 Hz); pitch scoop, bow noise concentrated in the attack, and **bow-pressure brightness** (the tone opens as the envelope swells) — under an **LA sampled attack** (real bow bite, 6 pitch zones × forte/piano by velocity); bends and CC68 legato give one bow stroke across several fingered notes | 40–45, 110 |
| **SFX noise** | low-level band-filtered noise bursts/washes used as safe, toneless fallbacks when MIDI asks for GM sound effects rather than instruments | sound effects 120–127 |
| **Drums** | parametric hits: decaying partials with pitch glide (membranes), **inharmonic bell-plate stacks** for cymbals/hats, a two-band snare (shell + wires); harder hits are brighter, and every strike is jittered. The kick now layers a beater knock over a **sub drop** (86→~45 Hz) for real chest weight. An opt-in **second kit (v2)** — crash with a sine tail, tom pitch-drop, static open-hat, snare rattle — is selected per channel 10 by a **non-zero Program Change** (GM2 kit variation); the standard kit (program 0) stays v1, so pre-v0.9 files are unchanged | GM channel 10 |

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
  on the fiddle, winds, strings and choir (the scoop or ensemble stack
  glides to the new pitch, no fresh bow/tongue/section attack). CC68 < 64
  returns to normal picking.
- **Program 28** is a dedicated palm-mute preset — heavy damping, a short
  decay, and a dull excitation — rather than just a quieter clean guitar.
- **CC1 mod wheel** adds expressive vibrato to the sustained melodic
  families (plucks, bowed strings, SawStack strings/choir, winds): an
  engine-level 5.3 Hz LFO whose depth follows the wheel up to ±35 cents,
  multiplied on top of the
  channel's pitch bend — so a bent-and-held note can bloom into vibrato,
  the way a guitarist's wail does. Drums, pianos, bells and the palm-mute
  are left alone. On **organs** the wheel is a Leslie speed control
  instead. The first CC1 event on a channel (any value) makes the wheel
  *authoritative*: from then on the tremulant rate is CC1 mapped across
  the full Leslie range — ~0.9 Hz (slow chorale) at CC1 = 0 up to ~6.8 Hz
  (fast) at CC1 = 127 — so a 0→127 ramp sweeps the rotor over its whole
  span, and CC1 = 0 *brakes to slow* rather than reverting to the program
  idle. The rate slews with a ~1.5 s rotor time constant (real
  spin-up/spin-down inertia), the base tremulant depth stays audible even
  at the slow rate, and the modulation deepens further as it spins up. A
  channel whose CC1 is never touched keeps its program's idle tremulant
  unchanged, so mod-free MIDI renders exactly as before.
- **CC64 sustain pedal** holds NoteOffs: a note released while the pedal is
  down keeps ringing until the pedal lifts (the piano's pooled washes).
  Pedal-held voices are past their NoteOff, so they are never candidates
  for CC68 legato retuning.
- **CC74 brightness** puts a resonant 2-pole lowpass (Q ≈ 1.4) on the
  channel's dry path, *before* the bus sends tap it — a wah sweep colours
  the reverb and echo too. 0..127 maps exponentially 300 Hz → 12 kHz, the
  cutoff is slewed per block so a CC74 LFO riding every 16th doesn't
  zipper, and 127 (or never sending CC74) is a true bypass — the filter is
  not in the path at all, and pre-v0.6 renders are bit-identical.
- **CC0 bank select — the alternate orchestral bank.** A channel that sends a
  non-zero **Bank Select MSB (CC0)** before its notes gets hollowsynth's earlier
  *v0.9* voicings for **strings (48–51)**, **choir (52–54)** and **bowed
  (40–45)** in place of the current defaults: envelope-tracked string brightness
  (the tone opens as the note swells), a consonant/breath choir onset with
  per-section SATB scatter, and per-instrument bowed bodies (distinct
  viola/cello/contrabass resonances). Everything else on the channel plays its
  normal voice. `CC0 = 0` — or never sending it, the default — keeps the standard
  bank, so existing files render byte-for-byte unchanged. Use it to A/B the two
  orchestral characters, or for tonal variety.

`material.py`'s `bend()`/`bend_ramp()` and `run()` helpers (in the *Hollow
Hill* composition engine) write these events for rapid-fire runs, wails
and hammered passages; see `part_one.py`'s Stormrise and `part_two.py`'s
reel for examples.

## The mix

- **Channel strips** honour CC7 (volume), CC11 (expression, smoothed — the
  album's swells depend on it; CC1 mod is smoothed the same way), CC64
  (sustain pedal), CC74 (brightness — the resonant lowpass described
  above, inserted ahead of the sends), CC91 (reverb send), CC93 (chorus
  send), CC94 (echo send) and CC10 pan — realised as equal-power gain
  **plus a Haas micro-delay** on the far channel, so panned sources
  localise like sources in a room rather than level tricks.
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

## Verification (this machine has no ears)

- `cargo test` (21 tests) — MIDI/tempo-map math including pitch-bend decode,
  envelopes, a zero-crossing check that a plucked A4 sounds at 440 Hz (the
  KS delay compensates the loop filter's phase delay, so tuning is
  cent-accurate), a bend test (A4 bent +2 semitones settles near B4), a
  hammer-on test (a ringing string retunes without re-picking), a palm-mute
  decay test, a check that the fiddle's onset scoop settles to true pitch,
  three LA-layer checks (bank parses, sampled attack agrees with the model
  on pitch through the crossfade, no level jump at handover), a bus-glue
  test (gain reduction on loud material, near-transparent on quiet
  material), and five v0.6 checks on real rendered audio: CC1 = 127 makes a
  bowed note's pitch wander far beyond its natural vibrato (zero-crossing
  analysis) while CC1 = 0 does not, an organ's tremulant rate measurably
  climbs over ~2 s after CC1 = 127 (Leslie inertia), CC74 = 20 strips the
  high-frequency energy from a bright pluck while CC74 = 127 is
  bit-identical to the unfiltered path, a note whose NoteOff falls under
  CC64 keeps ringing until pedal-up then dies, and `--solo` of an empty
  channel renders true silence. A full Part One render was also verified
  byte-identical between v0.5 and v0.6 binaries.
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
