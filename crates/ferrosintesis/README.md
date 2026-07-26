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
use ferrosintesis::offline::{self, Normalization, Options};
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let song = offline::load(Path::new("input.mid"))?;
    println!("{}: {:.1} s, {} events", song.title(), song.seconds(), song.events_len());

    // `Options` has private fields: build it from Default with the with_* builders.
    let opt = Options::default().with_reverb(0.25);

    // Bounded-memory render, -18 LUFS loudness normalization, -1 dBTP limit,
    // deterministic dither, and atomic WAV publication.
    let stats = offline::render_to_wav(
        &song,
        &opt,
        Path::new("output.wav"),
        Normalization::loudness(-18.0, -1.0),
    )?;
    eprintln!("{} voices, peak {:.3}", stats.voices_spawned, stats.peak);
    Ok(())
}
```

`offline::parse(&bytes)` is `load` for in-memory data. For progress,
`offline::render_to_wav_with_progress` takes a `FnMut(Progress)` callback — rendered
seconds, total seconds, active voices, and a `fraction()` helper. `Song`
exposes `title()`, `seconds()`, `initial_bpm()`, `events_len()` and
`markers_len()`. Errors are `MidiError`, a plain enum implementing
`std::error::Error`.

## The audio contract

`offline::render_to_wav` is the normal file path. It streams float audio to
scratch beside the output, measures loudness while rendering, applies exact
disk-backed normalization and true-peak limiting, then incrementally writes and
atomically publishes the WAV. Audio working memory does not grow with track duration.

`offline::render` remains the lower-level alternative. It returns `(Vec<f32>, Stats)`:
**interleaved stereo** — left, right, left, right — at `opt.sample_rate()`,
un-normalized. `normalize_loudness`, `normalize_to_i16`, and `write_wav` preserve the
buffer-first building blocks for callers that need them. The measurement primitives
— `integrated_lufs`, `true_peak_dbtp`, `limit_true_peak` — are public if you
want your own gain staging.

## Options

| builder | accessor | default | meaning |
|---------|----------|---------|---------|
| `with_sample_rate` | `sample_rate()` | `44100` | output sample rate (Hz), `u32` |
| `with_reverb` | `reverb()` | `0.32` | reverb return level |
| `with_tail` | `tail()` | `6.0` | seconds of reverb tail rendered past the last note |
| `with_echo` | `echo()` | `0.375` | echo-bus delay in seconds; `0.0` disables the bus |
| `with_samples` | `samples()` | `true` | the embedded attack-sample layer |
| `with_solo` | `solo()` | `0xFFFF` | channel bitmask; notes on cleared channels are dropped, but the tempo map stays, so a solo stem lines up with the full mix |

The fields are private: build with `Options::default()` plus the `with_*` methods, and
read them back with the matching accessors (`opt.sample_rate()`, `opt.echo()`, …). That
is what lets a later release add or rename a knob without breaking you.

## Feature flags

`embedded-samples` (default) compiles twenty-five first-party asset crates into
the binary: 1156 recorded WAVs -- attack transients, sustain loops, whole-voice
instruments and the sampled drum kit -- embedding ~111 MiB
of PCM. The synth uses them
the way the Roland D-50 did — LA synthesis: play a real onset, crossfade into
the modeled body — because the ear judges an instrument mostly by its first
hundred milliseconds, and onsets (hammer strikes, bow bites, breath chiff,
brass articulation) are what synthesis fakes worst.

## The instrument models

| family | technique | GM programs |
|--------|-----------|-------------|
| **Pluck** | extended Karplus-Strong in **two polarizations** — a sustaining loop plus a faster-decaying, slightly detuned one, so notes decay fast-then-slow with a gentle beat, like a real string. The delay line is now **fractional-tap**, so pitch can *move* while a note rings: **MIDI pitch bend** glides it, and **CC68 legato** retunes an already-ringing string instead of re-picking it — hammer-ons and pull-offs, and slides on the fiddle/winds too (see "Performance" below). Tuned-delay allpass, in-loop damping, pick-position comb excitation, per-note round-robin variation. Acoustics get a **body resonator** (Helmholtz air mode + plate modes), and the acoustic guitars 24–25 additionally feed an engine-level **sympathetic open-string bus** (sitar 104 gets its own bank of thirteen **tarab strings**); electrics and basses get a **pickup-position comb**; basses also get an envelope-locked **sub-oscillator** for fundamental weight. GM 35 fretless adds an envelope-following mid formant that blooms open into the note's onset — the "mwah" rather than a static dark bass preset. GM 46 harp has its own broad soundboard resonances and skips the guitar wound-string key split. A dedicated **palm-mute** preset (heavy damping, short decay) lives at program 28. GM 31 guitar harmonics is a true **flageolet** — the KS loop itself is retuned to the touched harmonic, so the note sounds at **2× the written pitch below E4 (key 64) and 3× from E4 up** (the multiple survives bends and legato retunes), and a line crossing the E4 boundary leaps by more than the written step, exactly as natural harmonics force a real player to. GM 7 clavinet is **sampled by default** since 2026.07 (a real clavinet from the MuseScore MS Basic soundfont, MIT) — the modeled short bright pickup/comb pluck with a soft-clip string buzz is now the `--no-samples` and CC0-nonzero alt-bank voice. GM 6 harpsichord is a nearly velocity-insensitive quill pluck — fixed-energy excitation, no wound-string split, a jack thud on release — and since 2026.07 plays under an **LA sampled attack** (a CC0 VCSL harpsichord, 10 pitch zones sounding C2–F6) that carries the real quill onset while the model keeps the slow-damped jangle. GM 15 hammered dulcimer re-voices the polarization pair as a true **double course** — two near-equal strings 0.42 % apart with near-zero bridge coupling, so every note carries the instrument's slow unison-shimmer beat under a wooden hammer knock; like the harp it skips the guitar wound-string key split, and since 2026.07 it plays under an **LA sampled hammer onset** (a CC-BY Freesound hammered dulcimer, 9 zones sounding C#4–D5), the pure model remaining the CC0-nonzero alt. Since 2026.07 the **harp 46** (CC0 VCSL concert harp), **sitar 104** (MIT MuseScore MS Basic) and **banjo 105** (CC0 ganjo 6-string guitar-banjo) also play under an **LA sampled pluck onset** over their Karplus-Strong model, exactly as the nylon/steel guitars do. **A MANDOLIN lives at GM 25 + bank-select LSB 96** (the XG cell — General MIDI has no mandolin program, and GM2/GS/XG all place one as a variation of the steel guitar): a short-scale, steel-strung, DOUBLE-COURSE model — two near-equal strings a few cents apart, the same mechanism the hammered dulcimer uses — under an owner-recorded LA onset bank of **ten zones × four round robins**. It is the one voice whose sampled attack is REPLAYED on a tremolo restrike rather than suppressed: rotating four genuinely different takes is what makes that safe, so every single-take bank keeps the original suppress-and-model behaviour | guitars 24–31 (28 = muted), basses 32–39, harp 46, harpsichord 6, clavinet 7, **hammered dulcimer 15**, sitar 104, banjo 105, shamisen 106, koto 107, **mandolin (25 + LSB 96)** |
| **Modal** | banks of decaying rotation-oscillator partials (no `sin()` in the loop) with strike noise; the partial bank retunes phase-continuously for pitch bend, RPN fine tune, portamento and aftertouch vibrato. Acoustic pianos GM 0–3 keep the inharmonic two-stage decay; 0/1/3 play under the LA sampled hammer strike and feed an engine-level **sympathetic soundboard bus**, while GM 2's CP-style electric grand — pickup, not soundboard — deliberately skips both. GM 4 is a Rhodes-style tine EP, GM 5 a brighter FM/DX bell EP. GM 11 vibraphone adds the defining motor-fan amplitude tremolo. GM 47 timpani adds a struck-head pitch settle, velocity-bright upper modes, per-strike balance variation, and note-off release that lets short hits ring — and since 2026.07 plays under an **LA sampled mallet strike** (CC0 VCSL Timpani, 5 zones A#1–F3) over that modeled body. GM 112–118 add modeled melodic percussion: bright tinkle bell, clanky agogo, tuned steelpan, dry woodblock, taiko, melodic tom and swept synth drum | acoustic pianos 0–3, electric pianos 4–5, celesta 8, glockenspiel 9, music box 10, **vibraphone 11** (metal bars with ~6 Hz motor tremolo), **wood bars 12–13** (marimba/xylophone with short key-scaled decays and band-passed mallet clicks), **tubular bells 14** (hand-tuned chime partials ≈ 2:3:4.2 with hum; strikes jitter so no two ring alike), timpani 47, kalimba 108, melodic percussion 112–118 |
| **Organ / free reed** | **GM19 defaults to the additive drawbar church organ** on the Leslie path — the round-2 audition preferred it over the CathedralOrgan pipe model, so the default and the CC0=1 alt are the same voice. **CC0=2 restores the cathedral pipe organ**: stable per-rank/per-key pipe identities, generated 1024-sample rank tables, an English full-organ registration, a 32-foot pedal foundation on low keys, wind-load interaction, a fixed-rate tremulant whose depth follows CC1 and a CC11 reed-rasp swell. That voice feeds its own long cathedral reverb without filtering away the infrasonic weight. GM16–18 share the additive drawbar/Leslie family with key click, chiff, pipe variation and rock-organ overdrive. GM20/21/23 are bellows free reeds: harmonium and accordions. GM22 harmonica now lives in the **Reed** family (below) and takes CC1 as pitch vibrato. | 16–21, 23 |
| **SawStack** | detuned polyBLEP saw ensemble — **each layer with its own vibrato rate/phase and a slow random pitch drift**, so a section sounds like players, not one detuned synth. Strings and choir also answer authored **CC1 vibrato** and **CC68 legato**; pads keep their normal retriggering. The stack feeds a lowpass (strings, pads; the sweep pad's filter is LFO-swept) or a **vocal formant bank** that morphs open at the onset ("mm-ah"). Choir-pad 91 stays on the old pad path unless its channel authors CC70, then it uses the same vowel-morph formant bank. | strings 48–51, choir 52–54, pads 88–95 |
| **Fx (synth FX)** | three cores wearing eight hats: an `Fx` wrapper voice that owns each preset's motion over either the frozen crystal Modal bell (96/98/100/102) or a pitch-stable detuned polyBLEP saw stack (97/99/101/103 — no per-layer vibrato or drift; the wrapper is the tone control). Each preset's identity sits on a different axis: **rain 96** a dense ~380-grain/s stochastic droplet wash (past the auditory-fusion edge) with the crystal bell trimmed to a faint pitched sparkle inside it — with samples on (the default) a real owner-recorded CC0 downpour loop replaces the synthetic gated-noise wash, sparkle intact, and `--no-samples` keeps the pure synthetic wash; **soundtrack 97** a dark-to-bright cinematic filter swell; **crystal 98** the inert preset, bit-identical to the pre-wrapper crystal bell; **atmosphere 99** the opposite, closing filter (bank-LSB 19 selects the XG Hollow Release variant — the same voice with a ~3 s lingering release); **brightness 100** a late one-shot monotone filter rise so the air blooms on top; **goblins 101** a fixed resonant formant under a random-walk pitch wobble that never settles; **echoes 102** a crisp droplet then a decaying in-voice ~0.22 s repeat train (deliberately independent of the engine echo bus); **sci-fi 103** pitch and a high-Q filter falling together — the classic laser | synth FX 96–103 |
| **OrchHit** | one-shot orchestral stab: octave-stacked detuned saw ensemble, low thump, and a short noisy bite with fast decay | orchestra hit 55 |
| **Brass** | per-player lip-valve saws (2× oversampled) through a fixed bore/bell body, an envelope-tracked **"waa"** brightness that opens with loudness, an onset pitch **scoop** and flutter-tongue **growl**. Pushed loud, the naturals **"brass up"**: a progressive-steepening **rasp cascade** (a second lip-valve stage that *splits* the drive across two knees for a slower, shock-like harmonic rolloff — the cuivré edge) blooms in over forte and opens the radiated output so the edge escapes the bell. It is scaled per program by a **brassiness** constant (trumpet/trombone rip; horn stays mellow until fortissimo; tuba barely brasses) and derated in the top register so it stays under the 2× alias floor; the synth-brass pair is untouched. **CC11 breath** opens the timbre, **channel aftertouch** adds growl (and rasps harder); **CC1** vibrato and **CC68** legato as elsewhere. Section/synth-brass get section-width chorus | trumpet 56, trombone 57, tuba 58, muted trumpet 59, french horn 60, brass section 61, synth brass 62–63 |
| **Reed** | a band-limited **variable-duty pulse** source (a square for the clarinet's hollow odd spectrum, a narrow pulse for the double reeds' buzz) shaped by a tanh over-blow, a per-program **formant bank**, tongue **chiff** and breath onset, and control-rate vibrato. Bagpipe (GM 109) is **sampled by default** since 2026.07 (a CC0 FreePats G-pipe: looped drone + chanter); this modeled reed with one persistent channel drone is now its **CC0 alt-bank** voice. Shanai uses a bright double-reed preset. GM 22 harmonica is a free-reed preset — wide-duty odd-harmonic pulse, prominent breath, and a slow draw-bend scoop into the note. Velocity opens the timbre; saxes get a touch of slap echo. CC1/CC68 as elsewhere | harmonica 22, soprano/alto/tenor/bari sax 64–67, oboe 68, english horn 69, bassoon 70, clarinet 71, bagpipe 109, shanai 111 |
| **Lead** | the SawStack voiced for a synth lead — **fast velocity-tracked attack, short release, a velocity-tracked filter** (harder = brighter), and a band-limited **square/pulse** oscillator for the square-lead class. No always-on vibrato: the **CC1 mod wheel** adds it, and **CC68 legato** slurs one note into the next. Per-program voicing (square, saw, calliope, chiff, charang, voice, fifths, bass+lead) via oscillator shape, count, detune and cutoff | synth leads 80–87 |
| **Wind** | sine + weak harmonics + band-filtered breath that rides the vibrato, chiff, and a pitch **scoop** into each note — under an **LA sampled attack**; bends and CC68 legato slur the scoop instead of re-tonguing. Each wind carries its OWN onset bank: flute/piccolo 72–73 (real flute onset, 5 zones), recorder 74 (CC0 VCSL Baroque recorders), ocarina 79 (CC0 VCSL), and pan flute 75 / shakuhachi 77 (MIT MuseScore MS Basic) — smearing one transverse-flute transient across all of them destroyed their identity, so each gets its own bank or none. **Blown bottle 76** is the exception in this family: instead of a modeled body under an onset it is a **whole-voice CC0 recording** (Freesound 349867 "Blown Bottle Two" by Terry93D, CC0 1.0) — the recorded blow played through into a pitch-synchronous loop of the plateau body (`BottleLoopVoice`, built exactly like the sax), with the modeled Wind bottle kept as the `--no-samples` voice and the fallback when the repitch falls outside the 0.5–2.05× window. **Only whistle 78 stays model-only** (no usable melodic-whistle source), with a bespoke chiff | flutes/whistles 72–79 |
| **Solo bowed strings (waveguide)** | the crate's most elaborate string model, and since 2026.07.26 the voice of EVERY solo bowed string: a stick-slip digital **waveguide** with an STK-style friction table — not polyBLEP, not model-only. Each program is a distinct voicing of it, with register-correct body resonances, its own MEASURED loop-latency compensation and natural-vibrato rate, and its own **arco sample bank** crossfaded into the waveguide sustain: cello and contrabass have their own recordings (`cello_bank`/`contrabass_bank`, not a repitched violin transient), viola its own dedicated bank (VSCO Viola Section susvib, 7 zones × forte/piano), and violin and fiddle share a 6-zone × forte/piano solo-violin bank. The fiddle is a violin bowed harder: a quicker, brighter, noisier stroke with broadband bow noise radiated straight from the bow/string contact. Bends and CC68 legato keep one bow stroke across several fingered notes | violin 40, viola 41, cello 42, contrabass 43, fiddle 110 |
| **Tremolo / pizzicato strings** | GM44 is a velocity-sensitive 6–9 Hz bow-tremolo proxy with reversal re-bites, built on the older polyBLEP bowed voice — the one bowed program not yet on the waveguide, because tremolo needs per-stroke re-articulation rather than amplitude modulation. GM45 is a decaying, bendable violin-body **pizzicato pluck** — a pluck, not a bow | tremolo 44, pizzicato 45 |
| **ReverseCymbal** | fixed-length high-passed noise and inharmonic metal swell for the GM reverse-cymbal program. Written key is intentionally ignored and short melodic note-offs do not kill the pre-peak swell — default bank only: the CC0 alt-bank 119 (percussion set B) key-tracks its metal base at half a semitone per semitone and swells to a hard stop at note-off | reverse cymbal 119 |
| **SFX** | dedicated GM sound-effect voices. Sustained textures follow the key: **breath 121** (formant-shaped hiss, soft onset), **seashore 122** (surf wash + spray riding a ~0.09 Hz swell), **helicopter 125** (rotor noise chopped at ~11 Hz), **applause 126** (dense clap-grain cloud, ~360 claps/s) — all hold while the key is down and release on note-off. One-shots: **bird tweet 123** (four fast upward FM chirps), **telephone 124** (440+480 Hz ring, 0.9 s on / 0.45 s off cadence repeating while held), **gunshot 127** (broadband crack peaking above the piano, with a low boom). **Fret noise 120** is, by default, a round-robin one-shot of real finger-slide recordings (owner-recorded Eastman E1D, CC0); `--no-samples` falls back to the original toneless squeak burst. All ignore the written pitch | sound effects 120–127 |
| **Drums** | default V3 kit: parametric membranes with pitch glide, kick sub/body/click separation, toms that settle near table pitch, resonant snare wires, and dense **MetalPlate** cymbals with broadband wash instead of exposed sine tails. With samples on (the default), the whole acoustic kit — kick 35/36, side stick 37, snare 38/40, the six GM toms 41–50 (two sampled drums repitched along the modeled ladder), hi-hats 42/44/46, and all the cymbals — plays a CC0 **sampled drum kit** (Virtuosity Drums `mid` mic set + a Big Rusty 18" china): velocity layers and round robins from the source SFZ mappings, a per-hit ±40-cent rate + gain micro-variation against machine-gunning, and the engine's hi-hat choke group (closed/pedal chokes the open hat) intact; `--no-samples` keeps a fully modeled fallback. Channel-10 Program Changes are accepted as MIDI metadata, but no longer unlock a *better* kit because the best kit is already the default — with three GM2 exceptions, a small kit-bank ladder. **Program 40 exactly selects the GM2 brush kit** (v0.12): brush tap 38 / slap 39 (strands land twice) / stir-swirl 40 (staggered noise swells with a slow 5 Hz wrist AM, outside the hat choke group) / darkened closed 42\|44 and open 46 hats / woody rim 37 / soft-beater kick 35\|36 with the sub drop intact; every key the brush kit does not remap falls through to the V3 voices, sampled kit included. **Program 24 exactly selects the modeled "synth kit"** (v0.18, the GM2 Electronic slot): the V3 voicing with the sampled replacement layer off — byte-identical to `--no-samples` V3. **Program 25 exactly selects the original V1 kit** (v0.19): the drum voices from before the Jul 2026 "kit-v2" realism overhaul, held byte-stable by `v1_drum_render_signatures_are_stable`. Any other Program Change keeps the default V3 kit. | GM channel 10 |

The kalimba's lamella bank lives under GM 108, grouped with the Modal chromatic-percussion row above (not a gap in the table: 108 was previously missing from an earlier draft of this doc, now covered). If your material leans on GM 120–127 sound effects, all eight are now voiced: 120 fret noise plays a sampled finger-slide bank by default (modeled squeak under `--no-samples`), and 121–127 are dedicated modeled voices per the SFX row above.

## Controllers

| control | effect |
|---------|--------|
| pitch bend | channel-wide, applied to already-sounding notes, so a bend sweeps the chord; ±2 semitones by default, rescaled by RPN 0; RPN fine tune honoured |
| CC1 mod wheel | vibrato on the sustained melodic families; Leslie speed on the drawbar organs 16–19; tremulant depth on the CC0=2 GM19 cathedral organ; inert on the free reeds 20/21/23 |
| CC70 | vowel morph ("mm"–"ah" formant anchors) on choir 52–54; choir-pad 91 joins the same formant path once it authors this |
| CC64, CC68 | sustain pedal; legato — a NoteOn while one note rings retunes the ringing voice (a hammer-on on guitars, a slur on bows and winds) instead of restarting it |
| CC66, CC67 | sostenuto — notes sounding at pedal-down hold through it, later notes are unaffected; una corda softens the acoustic-piano strike (GM 0/1/3, velocity ×0.75) |
| CC74, CC71 | resonant lowpass on the channel's dry path, ahead of the sends, so it colours the reverb and echo too; CC71 is its resonance (Q 0.7–8, default 1.4). Never sending either keeps the filter out of the circuit entirely, and a first CC74 of 127 never inserts it |
| CC7, CC11, CC10 | volume, smoothed expression, equal-power pan with a Haas micro-delay |
| CC2 breath | a second expression lane with CC11's squared taper: scales the channel gain and, on brass, reeds and winds, opens the timbre with it |
| CC91, CC93, CC94 | reverb, chorus and echo sends. Drums take CC91 like any channel; the kit's fixed drum-room reverb is a separate send that no controller moves |
| CC5, CC65, CC84 | portamento: exponential glide time (5 ms–0.6 s), legato-glide on/off, and portamento control — a one-shot glide from an explicit source key that works even with CC65 off |
| aftertouch | channel pressure adds vibrato and a gentle swell on the sustained families, growl on brass; polyphonic key pressure does the same to just the pressed note |
| CC0 bank select | alternate voicings, latched per channel: selectable piano recordings on GM 0–1; the CathedralOrgan pipe model at GM 19 CC0=2 (the default GM 19 is the Leslie drawbar); a sustaining driven-guitar lead on 29/30; the frozen v0.9 bowed 42–45, strings 48–51 and choir 52–54; a tam-tam at 14 (CC0=2 a recorded gong ageng, CC0=3 the pure bell model); **three steel-string acoustics at GM 25** (CC0=0 the default Eastman E1D picked, CC0=1 the same guitar fingerstyle, CC0=2 the Martin HD28, CC0=3 the pure model); a second percussion set at 112–119; and the pre-sampling pure models under many sampled-by-default voices (clavinet 7, bagpipe 109, nylon guitar 24, brass 56–61, reeds 68–71, EP 4, celesta 8, music box 10, vibraphone 11, dulcimer 15, basses 32–35); 127 declares the channel an XG drum part |
| CC32, CC120/121/123 | XG bank-LSB variation voices at note-on (undefined banks play the base GM voice, as real XG hardware does) — **LSB 96 on program 25 is the mandolin**, the one variation with its own sample bank; all sound off; reset all controllers (bank select persists); all notes off |
| NRPN 0x30 | **score-authored amp** on the driven guitars 29/30 — see below |

The rule throughout: an unauthored controller is inert. A channel that never
sends one renders exactly as if the feature did not exist.

### GM 0 piano recordings (CC0 bank select)

Bank-select MSB picks which recording voices GM 0 Acoustic Grand. Bank 0 is what
a channel that never sends CC0 hears. Each recording carries its own onset
calibration, so a slot's number never changes how its bank was baked.

| selector | recording |
|----------|-----------|
| CC0=0 | B1 upright |
| CC0=1 | VSCO upright |
| CC0=2 | Salamander |
| CC0=3 | Steinway B |
| CC0=4 | Headroom |
| CC0=5 | dark-Salamander |

Bank 0 became **our own Yamaha B1 upright** on 2026.07.26; the previous line-up
shifted down one slot intact, so the VSCO upright that used to be the default is
now bank 1. A CC0 value past the end plays the model alone. This table is checked
against the code by `gm0_cc0_table_in_the_readme_matches_the_source`, so it cannot
drift from the shipped routing the way the crate docs once did.

### Score-authored amp (driven guitars 29/30)

A file can shape the driven-guitar amp and cabinet per channel, so two channels
can be two different rigs. Address the six knobs by NRPN — MSB (CC99) = `0x30`,
LSB (CC98) = the index below, value on Data Entry MSB (CC6):

| LSB | knob | what it moves | at the extremes |
|-----|------|---------------|-----------------|
| 0 | Drive | pedal gain (both clip stages) | g1 ×0.25 … ×3.91 — near-clean to heavy. **Changes level** as a real gain control does (a static makeup trim cannot fully cancel a level shift that also depends on how hard you play); use CC7 to balance. |
| 1 | Tone | pre-clip voice EQ — pedal "tone" | −12 … +12 dB. **Dynamics-dependent**: a pre-clip control is largely swallowed by the saturator, so it colours strongly on quiet notes and subtly under a hard pick. For a level-independent tone, use Cab Tone. |
| 2 | Tightness | pre-shaper high-pass corner | ×0.54 … ×1.87, capped 200 Hz — focus vs woolly |
| 3 | Body | cabinet low-mid | −15 … +15 dB |
| 4 | Presence | cabinet presence | −15 … +15 dB |
| 5 | Cab Tone | cabinet high-frequency corner, **downward only** | full … ×0.30 (a 4000 Hz cliff closing to 1200 Hz). The main "which cabinet" axis, and the widest-moving knob; level-independent. Values above 64 are inert (it can only darken, never brighten past the shipped cliff). |

Every value is a **signed offset from the shipped voicing, with 64 = as-shipped**,
so the offset composes with whatever GM29/GM30 already sound like. The base
voicing differs by program (29 overdrive vs 30 distortion) and by bank (the CC0
alt bank is a lead amp), so the same NRPN value lands on four different starting
points — the offset is relative to each. The shipped base for each is:

| | pre-HPF | Tone centre | Body (cab) | Presence (cab) | HF cliff |
|---|---|---|---|---|---|
| 29 main | 90 Hz | 800 Hz +4 dB | 500 Hz −3 dB | 2600 Hz +5 dB | 4000/3800 Hz |
| 30 main | 90 Hz | 650 Hz −5 dB | 500 Hz −3 dB | 2600 Hz +5 dB | 4000/3800 Hz |
| 29 alt (lead) | 120 Hz | 1000 Hz +4 dB | 600 Hz +2.5 dB | 2800 Hz +5 dB | 4000/3800 Hz |
| 30 alt (lead) | 120 Hz | 650 Hz −4.5 dB | 600 Hz +4.5 dB | 2600 Hz +3 dB | 4000/3800 Hz |

Notes: the parameters are inert on any channel not playing GM29/30; changing a
knob mid-note is click-free (smoothed); and a channel that authors no amp NRPN
renders exactly as the program voicing does. The values are channel state — they
survive Program Change, CC0 and CC121, and reset only on GM System On.

The driven-guitar shaper runs at **4× oversampling**. That is what makes these
ranges possible: the `tanh` stages generate harmonics above the internal Nyquist
which fold back into the audible band, and at 2× that fold-back consumed the
whole alias budget with Drive alone at maximum, forcing every knob to stay narrow.
4× buys about 10 dB of margin for roughly 0.5 % of a CPU core per driven channel.

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

The code is licensed **MIT OR Apache-2.0**. The embedded PCM is not: it comes from
twenty-five first-party asset crates, and while most of them are **CC0 1.0** and need
no credit, ten are not. The asset crates contain nothing but that PCM and
`include_bytes!`; the per-crate inventory, provenance and regeneration tooling live
under
[`tools/ferrosintesis-samples/`](https://github.com/0x4D44/ferrosintesis/tree/main/tools/ferrosintesis-samples),
which is the authority on what each bank contains.

### If you distribute a binary

A build with default features embeds all twenty-five banks. **You must reproduce the
notices of the ten attribution-bearing banks below.** Each ships the exact required
text in its own crate's `NOTICE` file — concatenating those ten files satisfies
every licence here. The remaining fifteen banks are CC0 and require nothing.

| Crate | Licence | Supplies | Credit required |
|---|---|---|---|
| `ferrosintesis-samples-clavinet` | MIT | GM 7 clavinet | MuseScore "MS Basic" (MuseScore_General lineage): FluidR3 by Frank Wen, FluidR3Mono by Michael Cowgill, adaptation by S. Christian Collins |
| `ferrosintesis-samples-musescore` | MIT | GM 104 sitar, GM 75/76/77 pipe onsets | same MS Basic lineage as above |
| `ferrosintesis-samples-musescore-grand` | MIT | GM 0 grand (MF velocity tier) | MuseScore_General "Grand Piano", adaptation by S. Christian Collins, derived from FluidR3 by Frank Wen |
| `ferrosintesis-samples-grand` | CC BY 3.0 | GM 0 grand (Yamaha C5) | "Salamander Grand Piano V3" by Alexander Holm |
| `ferrosintesis-samples-dark-salamander` | CC BY 3.0 | GM 0 grand, darkened voicing | "Salamander Grand Piano V3" by Alexander Holm — **modified** (high-shelf EQ cut) |
| `ferrosintesis-samples-ydp-grand` | CC BY 3.0 | GM 0 grand (Disklavier Pro) | "YDP Grand Piano" by roberto@zenvoid.org for FreePats; underlying samples Zenph Studios / One Laptop Per Child |
| `ferrosintesis-samples-gong` | CC BY 3.0 | tam-tam gong | "CdM Gamelan Sample Library" by Digitópia / Casa da Música |
| `ferrosintesis-samples-headroom` | CC BY 4.0 | GM 0 grand (Yamaha C3) | "Headroom Piano" / "Intimate Piano" recorded by Bengt Nilsson; SFZ mapping by kinwie |
| `ferrosintesis-samples-sax` | CC BY 4.0 | GM 64-67 saxophones | MTG good-sounds dataset (Music Technology Group, Universitat Pompeu Fabra); "MTG Solo Saxophones" SFZ by kinwie |
| `ferrosintesis-samples-ccby` | CC BY 4.0 | GM 4 Rhodes, GM 15 hammered-dulcimer onsets | "C_S Fender Rhodes Mark II" by tim.kahn; "Multi-sampled Hammered Dulcimer" by iternetcone |

This table is not maintained by hand. `licensing.rs` derives the attribution-bearing
set from the `embedded-samples` feature list and each bank's own `license` field, and
fails the build if a bank is missing here or ships without a packaged `NOTICE` — so a
new CC-BY bank cannot land silently uncredited, which is exactly how five of these ten
came to be omitted before (MM-BUG-KILN-00060). It caught the B1 upright the same way
back when that first-party bank still declared MIT OR Apache-2.0: "we own it" is not
an exemption the derivation recognises — correctly, since a downstream distributor has
no way to know that. The B1 was re-dedicated **CC0 1.0** on 2026.07.25 and so has left
this table entirely. That is the point: it is the declared `license` field that moves a
bank in or out here, never who happens to own it.

### The CC0 banks

The remaining fifteen need no attribution: **our own Yamaha B1 acoustic upright**
(the GM 0 default recording since 2026.07.26 — Arthur's instrument, performance and
recording, dedicated to the public domain), the VSCO 2 Community Edition orchestral
library (violin, flutes, brass, reeds, string sections), the FreePats Spanish
classical guitar bank, **our own recordings of an Eastman E1D steel-string acoustic**
(the GM 25 default bank in two articulations, picked and fingerstyle — first-party and
CC0-dedicated, so there is no upstream to pin), the Discord SFZ GM Bank's Martin HD28
steel-string acoustic (which held that default slot until 2026.07.23 and is now the
GM 25 CC0=2 alternate),
the Versilian Community Sample Library (harpsichord, concert harp, timpani, Baroque
recorders, ocarina — in `ferrosintesis-samples-orchestral2`), the VCSL Steinway and
Kawai grands, sfzinstruments/ganjo, and the Freesound recording "Blown Bottle Two"
(349867, by Terry93D) that is the whole GM 76 blown-bottle voice
(`ferrosintesis-samples-bottle`). The generator pins every source — VSCO and VCSL to
exact commits, FreePats and the Martin to SHA-256-verified archives, ganjo and
MTG.SoloSax to commits, the MuseScore soundfont to a commit + SHA-256, and the
Freesound bottle to a committed SHA-256-verified source.

## MSRV and dependencies

Rust 1.87. The dependency closure is this crate plus its first-party
sample-asset crates — no third-party code, no build scripts, and
`#![forbid(unsafe_code)]` throughout.

## Design

The long version — how each instrument model works, what the LA-synthesis
layer is and why onsets matter most, the mix architecture bus by bus — is
[DESIGN.md](https://github.com/0x4D44/ferrosintesis/blob/main/crates/ferrosintesis/DESIGN.md).
