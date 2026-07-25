# MM-BUG-KILN-00099 — measure_wav meters every WAV as 44.1 kHz signed 16-bit stereo

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/ferrosintesis-cli/examples/measure_wav
- **Raised:** 2026-07-25
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
- **State history:** Open (2026-07-25, raised by Codex GPT-5.6-Sol during the `crates/ferrosintesis-cli/` coverage review) → Fixed (2026-07-25, Codex GPT-5.6-Sol; strict shared WAV parsing and sample-rate propagation landed with regression coverage; awaiting independent two-eyes verification)

## Observation

Source-level reproduction at `2d90376` (not executed because the review pass is
read-only): render a valid 48 kHz, 16-bit stereo WAV with the shipping CLI, then
pass it to the `measure_wav` example.

`crates/ferrosintesis-cli/examples/measure_wav.rs:14-33` finds only the `data`
chunk. It never reads or validates the `fmt ` chunk, channel count, bit depth,
or declared sample rate. Lines 35–38 decode every pair of bytes as signed
16-bit PCM, and lines 39–40 always pass 44,100 Hz to the loudness and true-peak
meters.

Expected: a valid 48 kHz WAV is decoded as 48 kHz stereo PCM, and unsupported
layouts are rejected.

Actual: 48 kHz audio is evaluated with 44.1 kHz K-weighting coefficients and
400/100 ms block geometry. Mono, float, 24-bit, or other layouts are silently
reinterpreted as interleaved 16-bit stereo. The tool prints plausible numeric
results even when its interpretation is wrong.

## Fix

`measure_wav` and `calmeter` now use one bounded RIFF/WAVE reader. It validates
the container and declared RIFF extent, chunk sizes and padding, `fmt ` metadata,
supported sample rate, byte rate, block alignment, complete frames, and required
`data`. The meter selects strict 16-bit stereo PCM mode; calmeter retains its
existing mono/stereo PCM and float support.

`measure_wav` passes the parsed sample rate to both loudness and true-peak
meters. Regression fixtures prove 44.1 and 48 kHz propagation, strict mono and
float rejection, non-PCM and unsupported-rate rejection, and malformed or
missing `fmt ` and `data` handling. The focused tests and clippy pass on the
native toolchain and the declared Rust 1.87 floor.

## Notes

`raw_dump` currently produces only 44.1 kHz float WAVs, but the shipping CLI
supports `--rate 48000` and the example describes itself as a WAV meter rather
than a raw-dump-only meter. Its purpose is to distinguish limiter defects from
meter defects, so authoritative-looking wrong measurements are a real
calibration risk.
