# ferrosintesis

A pure-Rust MIDI-to-WAV synthesizer with no third-party Rust code dependencies,
built around modeled instruments rather than a stock wavetable. Each melodic
program routes to a modeled body or sustain. The default **LA synthesis** layer
adds recorded PCM attacks or bodies, then crossfades into those models where
applicable. This adds recorded onset detail while retaining model-based sustain
and controller behaviour.

The default feature embeds the first-party `ferrosintesis-samples-*` asset crates.
Their recordings include CC0, MIT, and attribution-required material; the public
README and each asset crate's `NOTICE` state the distribution obligations. Cargo
retrieves and caches each package once, and the linker embeds referenced bytes in
the final executable. Full provenance and regeneration instructions live in
[`tools/ferrosintesis-samples/README.md`](https://github.com/0x4D44/ferrosintesis/blob/main/tools/ferrosintesis-samples/README.md).
The published CLI remains a single self-contained renderer.

The default `embedded-samples` Cargo feature enables the embedded-sample voicing. Consumers
that set `default-features = false` get the modeled-only synth and do not download
or compile the asset crates. That compile-time choice differs from the runtime
`--no-samples` option, which disables samples already embedded in the executable.

> **This is the design essay.** For the public API, the quick-start example, the
> feature flags and the GM-coverage table, see
> [README.md](README.md) — the crates.io landing page. This document is the long
> version: how each model works and why.

## Rendering an album MIDI from the repo

```powershell
cargo build --release -p ferrosintesis-cli
.\target\release\ferrosintesis.exe "albums\fable5\Hollow Hill\midi\01 - Hollow Hill, Part One.mid" `
    -o "target\demo\01 - Hollow Hill, Part One.wav"
```

```sh
cargo build --release -p ferrosintesis-cli
./target/release/ferrosintesis "albums/fable5/Hollow Hill/midi/01 - Hollow Hill, Part One.mid" \
    -o "target/demo/01 - Hollow Hill, Part One.wav"
```

One development-machine measurement on 2026-07-13 rendered Big Weather's dense
"First Light Freeway" in 46.8 seconds for 245.8 seconds of audio with an LTO
build. This is a dated data point, not a portable benchmark: speed varies with
the MIDI, features, compiler target, and CPU. Measure representative material
on the target machine.

The sample bytes are resolved by Cargo and embedded at compile time. The library
does not download assets at build time or runtime.

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
(mod wheel: vibrato, cathedral tremulant, or Leslie speed), channel aftertouch, CC5/CC65
portamento, CC64 (sustain pedal), CC68 (legato/hammer-on-pull-off), CC74
(brightness/wah), CC93 (chorus send) and CC94 (echo send) are all honoured —
see below. CC0 bank select is honoured too: a non-zero value selects the
alt-bank voicings — the frozen v0.9 strings 48–51, choir 52–54 and bowed 42–45
(the 40/41 alts were scrapped 2026.07.18; they fall through to the default voice
byte-identically), selectable GM 0/1 piano recordings, the GM 19 CC0=2 cathedral
organ (default and CC0=1 are the Leslie drawbar), the 29/30 sustaining
DRIVE_LEAD, and the pre-sampling pure models for the sampled-by-default programs
(clavinet 7, bagpipe 109, guitars 24–25, brass 56–61, reeds 68–71, EP 4,
celesta 8, music box 10, vibraphone 11, dulcimer 15, basses 32–35); CC0=127
declares an XG drum kit. GM 0 is the one exception to "non-zero selects an
alt-bank": its CC0 indexes a table of six piano recordings with CC0=0 as the
default (the B1 upright), so every value including zero picks a specific
recording rather than falling back to a shared default voice. On GM 14 the
alt bank is a **tam-tam / gong ageng** — a
deep 65–124 Hz strike whose shimmer partials bloom in over 0.3–0.7 s and ring
6–15 s under a short bright splash — while the default bank keeps tubular
bells; CC0=2 with samples available swaps in the recorded gong-ageng one-shot,
and CC0=3 keeps the pre-sampling pure tubular-bell model. GM 112–119 get a second **percussion set B** voicing on the alt bank:
a fast-fading tinkle bell, dry clang agogo, octave-twin steel pan (a
~4.7 Hz shimmer beat at C4), short woodblock, overshoot-settle taiko,
key-tracked melodic tom, zap-glide synth drum and a reversed-decay reverse
cymbal that swells to a hard note-off stop — the default-bank 112–119
voices are untouched.

Output is **loudness-normalised** (since v0.16): BS.1770-4 integrated loudness is
measured, a single scalar gain takes it to −18 LUFS, a true-peak limiter holds it
under −1 dBTP, and the result is TPDF-dithered to 16-bit PCM stereo. Because limiting
itself removes loudness, the gain/limit pair iterates until it converges from below.
The CLI exposes `--lufs` and `--tp-ceiling` to move those targets, and
`--peak-normalize` to opt back into the legacy peak-to-−1-dBFS behaviour.

## The instrument models

| family | technique | GM programs |
|--------|-----------|-------------|
| **Pluck** | extended Karplus-Strong in two polarizations: a sustaining loop plus a faster-decaying, slightly detuned one. Fractional taps support pitch bend and CC68 legato retuning. Program voicings add body resonators, pickup combs, sympathetic-string buses, damping, and sampled attacks where documented in the public README. GM 31 retunes to a touched-harmonic approximation; GM 15 uses a two-course approximation | guitars 24–31 (28 = muted), plucked basses 32–37, harp 46, harpsichord 6, clavinet 7, hammered dulcimer 15, sitar 104, banjo 105, shamisen 106, koto 107 |
| **SynthBass** | GM 38/39 are *synthesizer* basses, not plucked strings, and are modeled as such: one or two polyBLEP saws plus a sine sub-oscillator through an envelope-swept resonant lowpass, the filter opening with velocity. GM 39 ("synth bass 2") adds a second saw detuned a few cents for beating. No delay line, no string | synth basses 38–39 |
| **Modal** | banks of decaying rotation-oscillator partials (no `sin()` in the loop) with strike noise; the partial bank retunes phase-continuously for pitch bend, RPN fine tune, portamento and aftertouch vibrato. Acoustic pianos GM 0–3 keep the inharmonic two-stage decay; 0/1/3 play under the LA sampled hammer strike (GM 2's pickup-voiced electric grand deliberately skips it). GM 4 is a Rhodes-style tine EP, GM 5 a brighter FM/DX bell EP (GM 6 harpsichord is a quill **Pluck** — see that row). GM 11 vibraphone adds the defining motor-fan amplitude tremolo. GM 47 timpani adds a struck-head pitch settle, velocity-bright upper modes, per-strike balance variation, and note-off release that lets short hits ring, and plays under an **LA sampled mallet strike** (CC0 VCSL Timpani) over that modeled body. GM 112–118 add modeled melodic percussion: bright tinkle bell, clanky agogo, tuned steelpan, dry woodblock, taiko, melodic tom and swept synth drum | acoustic pianos 0–3, electric pianos 4–5, celesta 8, glockenspiel 9, music box 10, **vibraphone 11** (metal bars with ~6 Hz motor tremolo), **wood bars 12–13** (marimba/xylophone with short key-scaled decays and band-passed mallet clicks), **tubular bells 14** (hand-tuned chime partials ≈ 2:3:4.2 with hum; strikes jitter so no two ring alike), timpani 47, kalimba 108, melodic percussion 112–118 |
| **Organ / free reed** | **GM19 defaults to the additive drawbar church organ** on the Leslie path — the round-2 audition preferred it over the CathedralOrgan pipe model, so the default and the CC0=1 alt are the same voice. **CC0=2 restores the cathedral pipe organ**: stable per-rank/per-key pipe identities, generated 1024-sample rank tables, an English full-organ registration, a 32-foot pedal foundation on low keys, wind-load interaction, a fixed-rate tremulant whose depth follows CC1 and a CC11 reed-rasp swell. That voice feeds its own long cathedral reverb without filtering away the infrasonic weight. GM16–18 share the additive drawbar/Leslie family with key click, chiff, pipe variation and rock-organ overdrive. GM20/21/23 are bellows free reeds: harmonium and accordions (CC1 is inert on them). GM22 harmonica lives in the **Reed** family and takes CC1 as pitch vibrato. | 16–21, 23 |
| **SawStack** | detuned polyBLEP saw ensemble — **each layer with its own vibrato rate/phase and a slow random pitch drift**, so a section sounds like players, not one detuned synth. Strings and choir also answer authored **CC1 vibrato** and **CC68 legato**; pads keep their normal retriggering. The stack feeds a lowpass (strings, pads; the sweep pad's filter is LFO-swept) or a **vocal formant bank** that morphs open at the onset ("mm-ah"). Choir-pad 91 stays on the old pad path unless its channel authors CC70, then it uses the same vowel-morph formant bank. | strings 48–51, choir 52–54, pads 88–95 |
| **Fx (synth FX)** | an `Fx` wrapper voice owning each preset's motion (filter swells, formant wobble, in-voice echo train, laser fall) over one of two cores: the frozen crystal Modal bell (96/98/100/102) or a pitch-stable detuned saw stack (97/99/101/103). Rain 96 swaps in a real recorded downpour loop when samples are on; crystal 98 is the inert preset, bit-identical to the pre-wrapper bell. See the README family table for the per-preset map | synth FX 96–103 |
| **OrchHit** | one-shot orchestral stab: octave-stacked detuned saw ensemble, low thump, and a short noisy bite with fast decay | orchestra hit 55 |
| **Brass** | per-player lip-valve saws (2× oversampled) through a fixed bore/bell body, an envelope-tracked **"waa"** brightness that opens with loudness, an onset pitch **scoop** and flutter-tongue **growl**. Pushed loud, the naturals **"brass up"**: a progressive-steepening **rasp cascade** (a second lip-valve stage that *splits* the drive across two knees for a slower, shock-like harmonic rolloff — the cuivré edge) blooms in over forte and opens the radiated output so the edge escapes the bell. It is scaled per program by a **brassiness** constant (trumpet/trombone rip; horn stays mellow until fortissimo; tuba barely brasses) and derated in the top register so it stays under the 2× alias floor; the synth-brass pair is untouched. **GM 61 layers a dedicated ten-zone MIT MS Basic ensemble onset and early body over the section model**, with the pure model retained for `--no-samples` and alternate banks. **CC11 breath** opens the timbre, **channel aftertouch** adds growl (and rasps harder); **CC1** vibrato and **CC68** legato as elsewhere. Section/synth-brass get section-width chorus | trumpet 56, trombone 57, tuba 58, muted trumpet 59, french horn 60, brass section 61, synth brass 62–63 |
| **Reed** | a band-limited **variable-duty pulse** source (a square for the clarinet's hollow odd spectrum, a narrow pulse for the double reeds' buzz) shaped by a tanh over-blow, a per-program **formant bank**, tongue **chiff** and breath onset, and control-rate vibrato. The saxes 64–67 are **sampled by default** since 2026.07 (CC BY 4.0 MTG good-sounds solo takes played into pitch-synchronous sustain loops), the modeled reed remaining the `--no-samples` voice. Bagpipe (GM 109) is likewise **sampled by default** (a CC0 FreePats G-pipe: looped drone + chanter); its modeled reed — one persistent channel drone under the chanter — is the CC0 alt. GM 22 harmonica is a free-reed preset with a slow draw-bend scoop; shanai uses a bright double-reed preset. Velocity opens the timbre; saxes get a touch of slap echo. CC1/CC68 as elsewhere | harmonica 22, soprano/alto/tenor/bari sax 64–67, oboe 68, english horn 69, bassoon 70, clarinet 71, bagpipe 109, shanai 111 |
| **Lead** | the SawStack voiced for a synth lead — **fast velocity-tracked attack, short release, a velocity-tracked filter** (harder = brighter), and a band-limited **square/pulse** oscillator for the square-lead class. No always-on vibrato: the **CC1 mod wheel** adds it, and **CC68 legato** slurs one note into the next. Per-program voicing (square, saw, calliope, chiff, charang, voice, fifths, bass+lead) via oscillator shape, count, detune and cutoff | synth leads 80–87 |
| **Wind** | sine + weak harmonics + band-filtered breath that rides the vibrato, chiff, and a pitch **scoop** into each note; bends and CC68 legato slur the scoop instead of re-tonguing. Flute/piccolo 72–73, recorder 74, pan flute 75, shakuhachi 77, and ocarina 79 use program-specific **LA sampled onsets**. **Blown bottle 76** is a **whole-voice CC0 recording** (Freesound 349867) played into a pitch-synchronous loop, with the modeled bottle used by `--no-samples` and outside the supported repitch window. **GM 78 whistle stays model-only**, with a bespoke chiff. Program-specific banks kept the families more distinct in project auditions | flutes/whistles 72–79 |
| **Solo bowed strings (waveguide)** | a stick-slip digital **waveguide** with an STK-style friction table, used by violin 40, viola 41, cello 42, contrabass 43, and fiddle 110. Each program has its own voicing, body resonances, measured loop-latency compensation, natural-vibrato rate, and **arco sample bank** crossfaded into the waveguide sustain. GM44 remains a velocity-sensitive bow-tremolo proxy on the older voice; GM45 is a decaying, bendable pizzicato pluck. Bends and CC68 legato keep one bow stroke across several fingered notes | violin 40, viola 41, cello 42, contrabass 43, tremolo 44, pizzicato 45, fiddle 110 |
| **ReverseCymbal** | fixed-length high-passed noise and inharmonic metal swell for the GM reverse-cymbal program. Written key is intentionally ignored and short melodic note-offs do not kill the pre-peak swell — default bank only: the CC0 alt-bank 119 (percussion set B) key-tracks its metal base and swells to a hard stop at note-off | reverse cymbal 119 |
| **SFX** | dedicated GM sound-effect voices. Sustained textures follow the key hold: breath 121, seashore 122, helicopter 125, applause 126; one-shots: bird tweet 123, telephone 124 (ring cadence repeats while held), gunshot 127. Fret noise 120 plays a round-robin one-shot of real finger-slide samples by default (owner-recorded Eastman E1D, CC0), falling back to the original toneless squeak burst under `--no-samples`. All ignore the written pitch | sound effects 120–127 |
| **Drums** | V3 is the default kit. With samples enabled, its acoustic keys use a CC0 sampled bank with velocity layers, round robins, per-hit rate/gain variation, and hi-hat choking; `--no-samples` uses modeled voices. Channel-10 Program Changes select three alternatives: Program 40 the brush kit, Program 24 the modeled V3 "synth kit", and Program 25 the byte-stable original V1 kit. Other Program Changes keep V3 | GM channel 10 |

Timing behaviour: sustained families use slower attacks at low velocity.

The LA layer (`src/sampler.rs`) picks the nearest pitch zone, repitches it
to the exact target (each zone's root was measured by autocorrelation to
cent accuracy), and crossfades: the transient fades out over the same
window the model fades in, so the model's weaker synthetic onset is masked
by the real one. Targets too far outside the sampled range fall back to
the bare model. `--no-samples` turns the whole layer off. Pitch bend and
legato pass straight through the sample layer to the model underneath —
the sampled attack only ever plays once per slurred phrase.

Distorted guitar (programs 29/30) is handled the way a real rig would be: the
string voices are summed **per channel** and driven through a two-stage amp —
program-voiced EQ, a power-supply **sag** compressor (fast-attack/slow-release,
so pick transients pass and decaying tails are held in saturation), two
cascaded `tanh` stages with an interstage tilt, and the cabinet filter, all at
**2× internal rate** — so power chords get their intermodulation grit and held
notes bloom instead of dying. Electric presets also carry a **pickup coil
resonance** (the RLC peak that reads "electric": jazzbox 26 warm at 2.4 kHz,
clean 27 bright at 4.2 kHz), and the CC0 alt-bank DRIVE_LEAD adds an **e-bow sustainer**:
once a held 29/30 note decays to 0.6 of its spoken level, a band-limited
saturating driver at the string's fundamental holds it there indefinitely —
release decays naturally. The default-bank 29/30 has no hold: it is a decaying
overdriven pluck, kept deliberately distinct from the sustaining alt lead.
GM 26 (jazz hollowbody, neck pickup) and 27 (bright single-coil platform) are
distinct presets as of v0.15. Each channel keeps at most eight unreleased GM
29/30 voices across both programs. A ninth note releases the oldest voice,
including one deferred by sustain or sostenuto, so malformed or heavily layered
MIDI cannot grow the sustainer without bound while ordinary chords remain intact.

## Performance: bends, hammer-ons, mutes

Real guitarists barely re-pick every note — they bend, slide, hammer-on and
pull-off. ferrosintesis models this at the engine level, not just per-voice:

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
  are left alone. On the **GM19 CC0=2 cathedral organ**, the wheel controls
  the depth of a channel-wide 5.5 Hz tremulant; its rate and phase stay fixed so
  an entire division breathes together. On GM16–18 and GM19's default and CC0=1
  banks (the Leslie drawbar), the wheel is a Leslie speed control instead. The first CC1 event on one of
  those Leslie channels (any value) makes the wheel
  *authoritative*: from then on the tremulant rate is CC1 mapped across
  the full Leslie range — ~0.9 Hz (slow chorale) at CC1 = 0 up to ~6.8 Hz
  (fast) at CC1 = 127 — so a 0→127 ramp sweeps the rotor over its whole
  span, and CC1 = 0 *brakes to slow* rather than reverting to the program
  idle. The rate slews with a ~1.5 s rotor time constant (real
  spin-up/spin-down inertia), the base tremulant depth stays audible even
  at the slow rate, and the modulation deepens further as it spins up. A
  channel whose CC1 is never touched keeps its program's idle Leslie speed.
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
- **Cathedral reverb**: the GM19 CC0=2 cathedral organ bypasses that low-cut
  send and feeds a dedicated eight-line feedback-delay network behind a 40 ms
  pre-delay. Its
  frequency-dependent decay runs roughly 5–7 seconds, preserves the 32-foot
  rank's room pressure, and uses a 10 Hz return blocker as a final safety rail.
- **Chorus bus**: one modulated delay, quadrature L/R taps; strings, choir,
  Leslie organs and pads get ensemble width by program profile. The cathedral
  organ stays out of chorus unless the MIDI explicitly authors CC93.
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
