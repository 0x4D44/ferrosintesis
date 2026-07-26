# Changelog

All notable changes to `ferrosintesis` are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/) — with the pre-1.0 caveat that a minor bump may
break the API.

`ferrosintesis` has **not yet been published to crates.io**. Only a name-reservation stub
`0.0.0` exists there (2026-07-09); it contains no code. This file begins at the version
that will be the first real release, and older history lives in the repository's git log
and `wrk_journals/`.

## [Unreleased]

### Changed — BREAKING

- **Sample rate is `u32` throughout the public API.** `Options::sample_rate()` returned
  `f32` while `write_wav` and `RealtimeOptions` took `u32`, forcing an `as u32` cast at
  the seam. Sample rates are integers; the float was the odd one out. Taken deliberately
  before the first publish, when it costs nothing.

  Affects `Options::with_sample_rate`, `Options::sample_rate`, and the five loudness
  functions re-exported from `offline`: `momentary_lufs`, `integrated_lufs`,
  `true_peak_dbtp`, `limit_true_peak` and `normalize_loudness`. Renders are unchanged —
  verified byte-identical across all 124 catalog MIDIs.

### Changed

- **GM 40 violin, 41 viola and 110 fiddle now play the bowed waveguide**, joining the
  cello and contrabass. They rendered as a bandlimited sawtooth through three static peak
  biquads — a static harmonic stack, which is why the fiddle read as synthy. Each gets its
  own voicing of the `BowedString` stick-slip waveguide, with a measured loop-latency
  compensation, bow position, and level match to the voice it replaces. Every GM file using
  these programs renders differently; nothing else moves.

  The fiddle also gains `contact_noise` — broadband bow-hair noise radiated straight from
  the bow/string contact rather than coupled through the string — which is what makes it a
  violin bowed harder rather than a copy of GM 40. Its sampled onset now hands over at
  0.11–0.34 s rather than 0.08–0.28 s, because a waveguide takes time to build its limit
  cycle where the saw it replaced was instant-on.

  GM 44 tremolo strings deliberately stays on the older voice: tremolo is rapid bow-
  direction change and needs per-stroke re-articulation, not amplitude modulation of a
  sustained tone.

### Fixed

- **GM 42 cello keys 74 and 76 locked an octave up** whenever the per-note bow force drew
  near the top of its range — roughly one note in eight at the top two tones of its range,
  at +1203 cents with the level down ~60%. Bowing hard in a short loop drives the waveguide
  off its fundamental. Fixed with a bow-force ceiling over the cello's top few semitones.

  It had been invisible because the gate covering it used seeds 7/17/23, and the internal
  RNG is a raw-seeded xorshift32 whose first draw from a small seed is ≈ −1.0 — so all three
  collapsed bow force onto the bottom of its range and tested one bow three times. The
  replacement gates draw seeds the way the engine does.

### Added

- `ferrosintesis-samples-drumkit2`, carrying the four accent-cymbal banks (crash, sizzle
  crash, splash, china). This is a **packaging** split, not a musical one: the combined kit
  packaged at 15.8 MiB, over the crates.io 10 MiB per-crate limit. Renders are
  byte-identical. The `Bank` type stays single, in `-drumkit`; each bank carries a
  `BankSource` naming the crate that embeds its takes.
- `[package.metadata.docs.rs]` with `no-default-features`, so docs.rs does not attempt to
  compile ~104 MiB of embedded PCM and time out.
- `examples/quickstart.rs` is now packaged (`include`), so the published crate carries the
  example that keeps the README's code block honest.
- Payload oracles (`src/payload.rs`) deriving the embedded crate count, WAV count and byte
  total from the `embedded-samples` feature list, and failing the build when the shipped
  prose disagrees.

### Fixed

- Corrected the embedded-payload figures in the crate docs, README and NOTICE. They had
  drifted badly — the crate docs claimed "16.68 MiB … two first-party asset crates" and the
  README "~22 MiB" against a real 104.4 MiB across 24 crates, misleading anyone sizing a
  binary by roughly five times. The counts are now derived and oracle-checked rather than
  hand-maintained.
- The crate docs described GM 120–127 as "low-level noise fallbacks"; all eight sound
  effects are voiced, with GM 120 playing a round-robin bank of real finger-slide
  recordings.
- `ferrosintesis-samples-fretnoise` declared a `readme` file that did not exist, which made
  `cargo package` fail outright on it.
- `ferrosintesis-samples-drumkit` was missing `rust-version = "1.87"`, silently disabling
  clippy's `incompatible_msrv` lint for the largest asset crate.
