# hollowsynth

A zero-dependency Rust MIDI-to-WAV synthesizer, built to give *Hollow Hill*
a far better voice than a stock General MIDI wavetable. Every instrument is
modeled — with one deliberate exception: the solo fiddle and flute/whistle
use **LA synthesis** (the Roland D-50 trick) — a short public-domain PCM
attack transient supplies the first ~200 ms of each note, then crossfades
into the modeled sustain. The ear judges an instrument mostly by its onset;
the bow bite and breath chiff are the two things synthesis fakes worst.
The 17 transients (~950 KB, trimmed from VSCO 2 Community Edition, CC0 —
see `samples/README.md`) are embedded in the binary, so the tool stays a
single self-contained executable.

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

Output is peak-normalised to −1 dBFS, 16-bit PCM stereo with TPDF dither.

## The instrument models

| family | technique | GM programs |
|--------|-----------|-------------|
| **Pluck** | extended Karplus-Strong: tuned fractional delay (allpass), in-loop damping, pick-position comb excitation, body EQ — with per-note round-robin variation (pick position, brightness and decay jitter), so repeated notes never sound cloned | guitars 24–31, basses 32–39, harp 46, banjo 104–107 |
| **Modal** | banks of decaying rotation-oscillator partials (no `sin()` in the loop) with strike noise | piano 0–7 (inharmonic partials, velocity-dependent brightness, detuned unisons, and a **two-stage decay** — fast strike into a long singing aftersound), celesta 8, glockenspiel 9, music box 10, vibes 11–13, **tubular bells 14** (hand-tuned chime partials ≈ 2:3:4.2 with hum; strikes jitter so no two ring alike), timpani 47, crystal 96–103 |
| **Organ** | additive drawbar bank + key click + attack chiff + tremulant, per-pipe level variation (+ soft overdrive for rock organ) | 16–23 |
| **SawStack** | detuned polyBLEP saw ensemble — **each layer with its own vibrato rate/phase and a slow random pitch drift**, so a section sounds like players, not one detuned synth → lowpass (strings, pads; the sweep pad's filter is LFO-swept) or → **vocal formant bank** that morphs open at the onset ("mm-ah") | 48–51, 52–54, 80–95 |
| **Wind** | sine + weak harmonics + band-filtered breath that rides the vibrato, chiff, and a pitch **scoop** into each note — under an **LA sampled attack** (real flute onset, 5 pitch zones) | flutes/whistles 72–79 |
| **Bowed** | polyBLEP saw → violin body resonances (280/610/1350 Hz); pitch scoop, bow noise concentrated in the attack, and **bow-pressure brightness** (the tone opens as the envelope swells) — under an **LA sampled attack** (real bow bite, 6 pitch zones × forte/piano by velocity) | 40–45 |
| **Drums** | parametric hits: decaying partials with pitch glide (membranes), **inharmonic bell-plate stacks** for cymbals/hats, a two-band snare (shell + wires); harder hits are brighter, and every strike is jittered | GM channel 10 |

Timing realism: sustained families speak slower at low velocity, the way a
gently-bowed or gently-blown note actually starts.

The LA layer (`src/sampler.rs`) picks the nearest pitch zone, repitches it
to the exact target (each zone's root was measured by autocorrelation to
cent accuracy), and crossfades: the transient fades out over the same
window the model fades in, so the model's weaker synthetic onset is masked
by the real one. Targets too far outside the sampled range fall back to
the bare model. `--no-samples` turns the whole layer off.

Distorted guitar (programs 29/30) is handled the way a real rig would be: the
sustaining string voices are summed **per channel** and driven through a
`tanh` waveshaper + cabinet-style tone filter, so power chords get their
intermodulation grit.

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

- `cargo test` — MIDI/tempo-map math, envelopes, a zero-crossing check that a
  plucked A4 sounds at 440 Hz (the KS delay compensates the loop filter's
  phase delay, so tuning is cent-accurate), a check that the fiddle's
  onset scoop settles to true pitch, and three LA-layer checks: the bank
  parses, the sampled attack agrees with the model on pitch straight
  through the crossfade, and the handover happens without a level jump.
- Rendered output is checked numerically: RMS profile follows the score's
  dynamic arc, no DC offset, no unintended silence, zero click-level
  discontinuities, and stereo correlation ≈ 0.3/−0.2 (a genuinely wide image;
  a panned-mono mix sits near 0.9).

What it has **not** had is a human listen — balance was set by construction
and measurement. All the knobs are named constants: instrument voicing at the
top of `src/voices.rs`, bus levels in `src/engine.rs`.
