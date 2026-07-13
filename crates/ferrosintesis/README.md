# ferrosintesis

A General MIDI synthesizer in pure Rust with zero third-party dependencies.
Give it a `.mid` file, get stereo audio — no SoundFont required: the
instruments are physical and spectral models (Karplus-Strong strings, modal
partial banks, lip-valve brass, a cathedral pipe organ), and their attacks are
reinforced by an embedded bank of public-domain recorded transients.
`cargo add ferrosintesis` is the entire setup.

Most GM synthesis crates are SoundFont players: excellent if you have a good
`.sf2`, but you must bring one. ferrosintesis is for the other case — a MIDI
file in hand and nothing else on disk. It was built to render a catalog of
generative albums and voiced with corresponding care; it plays any GM file
faithfully.

## Quick start

```
cargo add ferrosintesis
```

```rust
use ferrosintesis::offline::{self, Options};
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let song = offline::load(Path::new("input.mid"))?;
    println!("{}: {:.1} s, {} events", song.title(), song.seconds(), song.events_len());

    // `Options` is #[non_exhaustive]; construct it from Default and refine
    // with the with_* builders.
    let opt = Options::default().with_reverb(0.25);

    // Interleaved stereo f32 at `opt.sr`, un-normalized.
    let (samples, stats) = offline::render(&song, &opt);
    eprintln!("{} voices, peak {:.3}", stats.voices_spawned, stats.peak);

    // Integrated loudness to -18 LUFS (BS.1770-4) under a -1 dBTP true-peak
    // ceiling, TPDF-dithered to 16-bit.
    let pcm = offline::normalize_loudness(&samples, opt.sr, -18.0, -1.0);
    offline::write_wav(Path::new("output.wav"), opt.sr as u32, &pcm)?;
    Ok(())
}
```

`offline::parse(&bytes)` is `load` for in-memory data. For long renders,
`offline::render_with_progress` takes a `FnMut(Progress)` callback — rendered
seconds, total seconds, active voices, and a `fraction()` helper. `Song`
exposes `title()`, `seconds()`, `initial_bpm()`, `events_len()` and
`markers_len()`. Errors are `MidiError`, a plain enum implementing
`std::error::Error`.

## The audio contract

`offline::render` returns `(Vec<f32>, Stats)`: **interleaved stereo** — left,
right, left, right — at `opt.sr`, un-normalized. `Stats` reports the absolute
peak, voices spawned, and maximum polyphony. Renders are deterministic: the
same MIDI, the same options and the same build produce byte-identical output.

Getting from that buffer to a file is two calls.
`normalize_loudness(&samples, sr, target_lufs, ceiling_dbtp)` measures
integrated loudness per BS.1770-4, gains to the target, true-peak-limits to
the ceiling (iterating, because limiting itself costs loudness), and
TPDF-dithers to `Vec<i16>`; `normalize_to_i16` is the plain peak-scaling
alternative. `write_wav` writes 16-bit PCM stereo. The measurement primitives
— `integrated_lufs`, `true_peak_dbtp`, `limit_true_peak` — are public if you
want your own gain staging.

## Options

| builder | field | default | meaning |
|---------|-------|---------|---------|
| `with_sample_rate` | `sr` | `44100.0` | output sample rate (Hz) |
| `with_reverb` | `wet` | `0.32` | reverb return level |
| `with_tail` | `tail` | `6.0` | seconds of reverb tail rendered past the last note |
| `with_echo` | `delay_s` | `0.375` | echo-bus delay in seconds; `0.0` disables the bus |
| `with_samples` | `samples` | `true` | the embedded attack-sample layer |
| `with_solo` | `solo` | `0xFFFF` | channel bitmask; notes on cleared channels are dropped, but the tempo map stays, so a solo stem lines up with the full mix |

The struct is `#[non_exhaustive]`, so a struct literal will not compile; the
fields stay `pub` for reading.

## Feature flags

`embedded-samples` (default) compiles two first-party asset crates into the
binary: 202 recorded attack transients, 16.68 MiB of PCM. The synth uses them
the way the Roland D-50 did — LA synthesis: play a real onset, crossfade into
the modeled body — because the ear judges an instrument mostly by its first
hundred milliseconds, and onsets (hammer strikes, bow bites, breath chiff,
brass articulation) are what synthesis fakes worst.

## The instrument models

| family | technique | GM programs |
|--------|-----------|-------------|
| **Pluck** | extended Karplus-Strong in **two polarizations** — a sustaining loop plus a faster-decaying, slightly detuned one, so notes decay fast-then-slow with a gentle beat, like a real string. The delay line is now **fractional-tap**, so pitch can *move* while a note rings: **MIDI pitch bend** glides it, and **CC68 legato** retunes an already-ringing string instead of re-picking it — hammer-ons and pull-offs, and slides on the fiddle/winds too (see "Performance" below). Tuned-delay allpass, in-loop damping, pick-position comb excitation, per-note round-robin variation. Acoustics get a **body resonator** (Helmholtz air mode + plate modes); electrics and basses get a **pickup-position comb**; basses also get an envelope-locked **sub-oscillator** for fundamental weight. GM 35 fretless adds an envelope-following mid formant that blooms open into the note's onset — the "mwah" rather than a static dark bass preset. GM 46 harp has its own broad soundboard resonances and skips the guitar wound-string key split. A dedicated **palm-mute** preset (heavy damping, short decay) lives at program 28; GM 7 clavinet uses a short bright pickup/comb pluck with a soft-clip string buzz. GM 6 harpsichord is a nearly velocity-insensitive quill pluck — fixed-energy excitation, no wound-string split, a jack thud on release. GM 15 hammered dulcimer re-voices the polarization pair as a true **double course** — two near-equal strings 0.42 % apart with near-zero bridge coupling, so every note carries the instrument's slow unison-shimmer beat under a wooden hammer knock | guitars 24–31 (28 = muted), basses 32–39, harp 46, harpsichord 6, clavinet 7, **hammered dulcimer 15**, sitar 104, banjo 105, shamisen 106, koto 107 |
| **Modal** | banks of decaying rotation-oscillator partials (no `sin()` in the loop) with strike noise; the partial bank retunes phase-continuously for pitch bend, RPN fine tune, portamento and aftertouch vibrato. Acoustic pianos GM 0–3 keep the inharmonic two-stage decay under the LA sampled hammer strike. GM 4 is a Rhodes-style tine EP, GM 5 a brighter FM/DX bell EP. GM 11 vibraphone adds the defining motor-fan amplitude tremolo. GM 47 timpani adds a struck-head pitch settle, velocity-bright upper modes, per-strike balance variation, and note-off release that lets short hits ring. GM 112–118 add modeled melodic percussion: bright tinkle bell, clanky agogo, tuned steelpan, dry woodblock, taiko, melodic tom and swept synth drum | acoustic pianos 0–3, electric pianos 4–5, celesta 8, glockenspiel 9, music box 10, **vibraphone 11** (metal bars with ~6 Hz motor tremolo), **wood bars 12–13** (marimba/xylophone with short key-scaled decays and band-passed mallet clicks), **tubular bells 14** (hand-tuned chime partials ≈ 2:3:4.2 with hum; strikes jitter so no two ring alike), timpani 47, crystal 96–103, kalimba 108, melodic percussion 112–118 |
| **Organ / free reed** | **GM19 defaults to a cathedral organ**: stable per-rank/per-key pipe identities, generated 1024-sample rank tables, an English full-organ registration, a 32-foot pedal foundation on low keys, wind-load interaction and a fixed-rate tremulant whose depth follows CC1. It feeds its own long cathedral reverb without filtering away the infrasonic weight. CC0 nonzero selects the former additive GM19 drawbar/pipe voice and Leslie path. GM16–18 retain that additive drawbar/Leslie family with key click, chiff, pipe variation and rock-organ overdrive. GM20/21/23 are bellows free reeds: harmonium and accordions. GM22 harmonica now lives in the **Reed** family (below) and takes CC1 as pitch vibrato. | 16–21, 23 |
| **SawStack** | detuned polyBLEP saw ensemble — **each layer with its own vibrato rate/phase and a slow random pitch drift**, so a section sounds like players, not one detuned synth. Strings and choir also answer authored **CC1 vibrato** and **CC68 legato**; pads keep their normal retriggering. The stack feeds a lowpass (strings, pads; the sweep pad's filter is LFO-swept) or a **vocal formant bank** that morphs open at the onset ("mm-ah"). Choir-pad 91 stays on the old pad path unless its channel authors CC70, then it uses the same vowel-morph formant bank. | strings 48–51, choir 52–54, pads 88–95 plus sustained FX 97/99/101/103 |
| **OrchHit** | one-shot orchestral stab: octave-stacked detuned saw ensemble, low thump, and a short noisy bite with fast decay | orchestra hit 55 |
| **Brass** | per-player lip-valve saws (2× oversampled) through a fixed bore/bell body, an envelope-tracked **"waa"** brightness that opens with loudness, an onset pitch **scoop** and flutter-tongue **growl**. Pushed loud, the naturals **"brass up"**: a progressive-steepening **rasp cascade** (a second lip-valve stage that *splits* the drive across two knees for a slower, shock-like harmonic rolloff — the cuivré edge) blooms in over forte and opens the radiated output so the edge escapes the bell. It is scaled per program by a **brassiness** constant (trumpet/trombone rip; horn stays mellow until fortissimo; tuba barely brasses) and derated in the top register so it stays under the 2× alias floor; the synth-brass pair is untouched. **CC11 breath** opens the timbre, **channel aftertouch** adds growl (and rasps harder); **CC1** vibrato and **CC68** legato as elsewhere. Section/synth-brass get section-width chorus | trumpet 56, trombone 57, tuba 58, muted trumpet 59, french horn 60, brass section 61, synth brass 62–63 |
| **Reed** | a band-limited **variable-duty pulse** source (a square for the clarinet's hollow odd spectrum, a narrow pulse for the double reeds' buzz) shaped by a tanh over-blow, a per-program **formant bank**, tongue **chiff** and breath onset, and control-rate vibrato. Bagpipe adds one persistent channel drone under the chanter; shanai uses a bright double-reed preset. GM 22 harmonica is a free-reed preset — wide-duty odd-harmonic pulse, prominent breath, and a slow draw-bend scoop into the note. Velocity opens the timbre; saxes get a touch of slap echo. CC1/CC68 as elsewhere | harmonica 22, soprano/alto/tenor/bari sax 64–67, oboe 68, english horn 69, bassoon 70, clarinet 71, bagpipe 109, shanai 111 |
| **Lead** | the SawStack voiced for a synth lead — **fast velocity-tracked attack, short release, a velocity-tracked filter** (harder = brighter), and a band-limited **square/pulse** oscillator for the square-lead class. No always-on vibrato: the **CC1 mod wheel** adds it, and **CC68 legato** slurs one note into the next. Per-program voicing (square, saw, calliope, chiff, charang, voice, fifths, bass+lead) via oscillator shape, count, detune and cutoff | synth leads 80–87 |
| **Wind** | sine + weak harmonics + band-filtered breath that rides the vibrato, chiff, and a pitch **scoop** into each note — under an **LA sampled attack** (real flute onset, 5 pitch zones); bends and CC68 legato slur the scoop instead of re-tonguing | flutes/whistles 72–79 |
| **Bowed solo strings** | program-specific polyBLEP bowed voices: violin, viola, cello and contrabass own register-correct body resonances, bow-pressure ceilings, onset speeds and natural-vibrato rates; fiddle uses a quicker, brighter, noisier violin-style bow. Violin/fiddle retain the **LA sampled attack** (6 pitch zones × forte/piano), while viola/cello/bass stay modeled rather than receiving a repitched violin transient. GM44 is a velocity-sensitive 6–9 Hz bow-tremolo proxy with reversal re-bites; GM45 is a decaying, bendable violin-body pizzicato pluck. Bends and CC68 legato keep one bow stroke across several fingered notes | violin/viola/cello/contrabass 40–43, tremolo/pizzicato 44–45, fiddle 110 |
| **ReverseCymbal** | fixed-length high-passed noise and inharmonic metal swell for the GM reverse-cymbal program. Written key is intentionally ignored; short melodic note-offs do not kill the pre-peak swell | reverse cymbal 119 |
| **SFX** | dedicated GM sound-effect voices. Sustained textures follow the key: **breath 121** (formant-shaped hiss, soft onset), **seashore 122** (surf wash + spray riding a ~0.09 Hz swell), **helicopter 125** (rotor noise chopped at ~11 Hz), **applause 126** (dense clap-grain cloud, ~360 claps/s) — all hold while the key is down and release on note-off. One-shots: **bird tweet 123** (four fast upward FM chirps), **telephone 124** (440+480 Hz ring, 0.9 s on / 0.45 s off cadence repeating while held), **gunshot 127** (broadband crack peaking above the piano, with a low boom). **Fret noise 120** keeps the original short toneless squeak transient. All ignore the written pitch | sound effects 120–127 |
| **Drums** | default V3 kit: parametric membranes with pitch glide, kick sub/body/click separation, toms that settle near table pitch, resonant snare wires, and dense **MetalPlate** cymbals with broadband wash instead of exposed sine tails. With samples on (the default), the whole acoustic kit — kick 35/36, side stick 37, snare 38/40, the six GM toms 41–50 (two sampled drums repitched along the modeled ladder), hi-hats 42/44/46, and all the cymbals — plays a CC0 **sampled drum kit** (Virtuosity Drums `mid` mic set + a Big Rusty 18" china): velocity layers and round robins from the source SFZ mappings, a per-hit ±40-cent rate + gain micro-variation against machine-gunning, and the engine's hi-hat choke group (closed/pedal chokes the open hat) intact; `--no-samples` keeps a fully modeled fallback. Channel-10 Program Changes are accepted as MIDI metadata, but no longer unlock a better kit because the best kit is already the default — with one exception: **Program 40 exactly selects the GM2 brush kit** (v0.12): brush tap 38 / slap 39 (strands land twice) / stir-swirl 40 (staggered noise swells with a slow 5 Hz wrist AM, outside the hat choke group) / darkened closed 42\|44 and open 46 hats / woody rim 37 / soft-beater kick 35\|36 with the sub drop intact. Every key the brush kit does not remap falls through to the V3 voices, and any other Program Change keeps the default V3 kit. | GM channel 10 |

## Controllers

| control | effect |
|---------|--------|
| pitch bend | channel-wide, applied to already-sounding notes, so a bend sweeps the chord; ±2 semitones by default, rescaled by RPN 0; RPN fine tune honoured |
| CC1 mod wheel | vibrato on the sustained melodic families; tremulant depth on the cathedral organ; Leslie speed on the drawbar organs |
| CC64, CC68 | sustain pedal; legato — a NoteOn while one note rings retunes the ringing voice (a hammer-on on guitars, a slur on bows and winds) instead of restarting it |
| CC74 | resonant lowpass on the channel's dry path, ahead of the sends; 127 — or never sending it — is a true bypass |
| CC7, CC11, CC10 | volume, smoothed expression, equal-power pan with a Haas micro-delay |
| CC91, CC93, CC94 | reverb, chorus and echo sends |
| CC5/CC65, aftertouch | portamento; channel and polyphonic pressure (vibrato, brass growl) |
| CC0 bank select | alternate voicings: a tam-tam at 14, a second percussion set at 112–119, the legacy drawbar GM 19, alternate strings and choir |

The rule throughout: an unauthored controller is inert. A channel that never
sends one renders exactly as if the feature did not exist.

## Realtime

`ferrosintesis::live` wraps the same engine for realtime use:
`RealtimeSynth::new(RealtimeOptions::default())`, feed raw MIDI bytes with
`write_byte`, and sum stereo blocks into your output buffer with
`render_add(frames, &mut out)`. It is the secondary surface — the crate is
offline-first — but it is the same voices and the same mix.

## Performance

Render in release. A release build (LTO) renders a dense, fully-orchestrated
track at roughly 5x realtime on a current desktop — a four-minute piece in
about fifty seconds — and sparser material considerably faster. Debug builds
are dramatically slower and are not worth timing.

## Sample provenance and licensing

The 202 embedded transients are trimmed from the VSCO 2 Community Edition
orchestral library and the FreePats Spanish classical guitar bank, both
CC0 1.0. The generator pins its sources — VSCO to an exact upstream commit,
FreePats to a SHA-256-verified archive — and the full inventory, provenance
and regeneration tooling live in the repository under
[`tools/ferrosintesis-samples/`](https://github.com/0x4D44/ferrosintesis/tree/main/tools/ferrosintesis-samples).
The two asset crates contain nothing but that PCM and `include_bytes!`. The
code is licensed MIT OR Apache-2.0; the samples are CC0-1.0.

## MSRV and dependencies

Rust 1.87. The dependency closure is this crate plus its two first-party
sample-asset crates — no third-party code, no build scripts, and
`#![forbid(unsafe_code)]` throughout.

## Design

The long version — how each instrument model works, what the LA-synthesis
layer is and why onsets matter most, the mix architecture bus by bus — is
[DESIGN.md](https://github.com/0x4D44/ferrosintesis/blob/main/crates/ferrosintesis/DESIGN.md).
