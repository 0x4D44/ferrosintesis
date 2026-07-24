# MM-BUG-KILN-00086 — GM 96 rain plays at the output clock instead of its recorded 44.1 kHz

- **State:** Open
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

## Notes

- `MM-BUG-KILN-00061` fixed a different sample-rate error: LA onset eligibility
  was incorrectly based on the already-converted playback step. It does not
  cover this whole-voice rain clock.
- `MM-BUG-KILN-00073` separately covers `rain_loop()` decoding lazily on the
  first realtime note despite prewarming. Fixing either bug does not fix the
  other.

