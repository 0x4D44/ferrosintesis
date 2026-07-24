# MM-BUG-KILN-00086 — GM 96 rain plays at the output clock instead of its recorded 44.1 kHz

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth / GM 96 sampled rain
- **Raised:** 2026-07-24
- **Owner:** -
- **Owner role:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner fingerprint:** -
- **Owner since:** -
- **Owner until:** -
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-rain/`)
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). `Fx`'s rain head is now a fractional `f64`
  advanced by `44100 / sr` and read with wrapped cubic interpolation; new oracle
  `fx_o8_rain_96_bed_plays_at_its_recorded_44100_clock` measures the RENDER at 44.1 / 48 /
  96 kHz. Fails-before / passes-after and a byte-identical 44.1 kHz render-diff are recorded
  under "Fix landed" below. Awaits independent two-eyes closure.)

## Observation

`rain_loop.wav` is mono PCM recorded at 44.1 kHz. The decoder explicitly
requires that rate (`crates/ferrosintesis/src/sampler.rs:43-58`), and the
committed WAV contains 202,860 source frames: 4.6 seconds at 44.1 kHz.

The GM 96 voice stores `rain_pos` as an integer, initializes it to zero, and
increments it by exactly one for every output frame
(`crates/ferrosintesis/src/voices.rs:11753-11761`, `:11913-11918`, and
`:11980-11990`). It never applies the required source-to-output step
`44_100 / output_sample_rate`.

Both public render paths accept non-44.1-kHz output rates
(`crates/ferrosintesis/src/engine.rs:1707-1712` and
`crates/ferrosintesis/src/live.rs:57-62`). Consequently:

- at 48 kHz, the 4.6-second recording loops every 4.226 seconds, 8.8% fast;
- at 96 kHz, it loops every 2.113 seconds, 2.18x fast;
- at 22.05 kHz, it loops every 9.2 seconds, half speed.

Expected: changing the output rate changes only the output clock; the rain
recording keeps its original temporal and spectral character. Actual: GM 96's
sampled bed speeds up or slows down with the requested output rate. The default
44.1-kHz path is unchanged because source and output clocks happen to match.

This pass did not run the application, tests, or an audio render. The clock
error and durations are source-confirmed; the audible impact is unverified.

## Fix

Store a fractional source position and advance it by
`44_100.0 / output_sample_rate`. Read the loop with wrapped interpolation, using
the existing rate-converting `LoopVoice` pattern at
`crates/ferrosintesis/src/sampler.rs:2561-2600`. Preserve exact integer reads at
44.1 kHz so the default render remains unchanged.

Add a derived rate-invariance oracle at 44.1, 48, and 96 kHz. After the same
wall-clock duration, each voice must have advanced through the same amount of
source material modulo the loop length. Also compare a rate-converted rendered
window against the 44.1-kHz control so the test proves playback, not only a
stored step value.

## Fix landed (2026-07-24)

**Code** (`crates/ferrosintesis/src/voices.rs`, `Fx`). `rain_pos` became an `f64` read head
and gained `rain_step = 44100 / sr`; the bed is read with the `LoopVoice` idiom — wrapped
4-point cubic interpolation — and wraps on the source length. At 44.1 kHz the step is
exactly 1.0, so `frac` is exactly 0.0 and an explicit branch reads the original integer
sample: the default render is untouched by construction, not merely by tolerance.

**Regression oracle** — `fx_o8_rain_96_bed_plays_at_its_recorded_44100_clock`
(`voices.rs`, `#[cfg(feature = "embedded-samples")]`). It measures the render, not the
stored step, and derives the loop length from the committed asset:

- (a) the bed's own loop period is wall-clock invariant — a 1.5 s window correlated against
  itself one `len(rain_loop)/44100` = 4.600 s later, at 44.1 / 48 / 96 kHz;
- (b) an 88.2 kHz render decimated by 2 reproduces the 44.1 kHz control.

**Fails before / passes after.** With the head forced back to one source frame per output
frame (the pre-fix behaviour), the loop-lag NCC is 0.998 at 44.1 kHz but **−0.003 at
48 kHz** — the test fails naming the rate. With the fix: 0.998 / 0.998 / 0.998 and 1.000
for the decimation check.

**Blast radius — render-diff inventory.** A program-change census of all 141 committed
`albums/**` + `demos/**` MIDIs finds GM 96 in exactly two files (both demos; no album):
`demos/ferrosintesis_reference/midi/04 - FX, World, Percussive, Noise.mid` and
`demos/synth_feature_showcase/midi/02 - Cathedral Mechanica.mid`. Rendered with a baseline
binary built at `0d8ae49` and with the fixed binary, both are **byte-identical at 44.1 kHz**
(`cmp`), and the same demo rendered at `--rate 48000` **differs** — the positive control
proving the change reaches the render. No other program can reach this code.

**Gates.** `cargo test --release -p ferrosintesis` 655 passed / 0 failed / 26 ignored (+4
doc-tests); `cargo clippy --release -p ferrosintesis --all-targets -- -D warnings` clean;
`cargo fmt --check` clean; `cargo check -p ferrosintesis --no-default-features` adds no new
warnings (the two `CLAVINET_*` dead-code warnings are pre-existing, tracked by
MM-BUG-KILN-00070).

**Not addressed here.** `rain_loop()`'s absence from `prewarm()` (MM-BUG-KILN-00073) is
untouched — that is a lazy-decode / realtime-deadline defect, independent of the clock.

## Notes

- `MM-BUG-KILN-00061` fixed a different sample-rate error: LA onset eligibility
  was incorrectly based on the already-converted playback step. It does not
  cover this whole-voice rain clock.
- `MM-BUG-KILN-00073` separately covers `rain_loop()` decoding lazily on the
  first realtime note despite prewarming. Fixing either bug does not fix the
  other.

