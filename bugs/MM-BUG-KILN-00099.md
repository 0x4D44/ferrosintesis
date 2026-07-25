# MM-BUG-KILN-00099 — measure_wav meters every WAV as 44.1 kHz signed 16-bit stereo

- **State:** Open
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
- **State history:** Open (2026-07-25, raised by Codex GPT-5.6-Sol during the `crates/ferrosintesis-cli/` coverage review)

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

Not fixed in this review. Parse and validate RIFF/WAVE plus `fmt ` before
decoding: PCM format 1, 16 bits, two channels, a positive supported sample rate,
consistent block alignment, and complete `data`. Pass the parsed rate to both
meters.

Prefer sharing the WAV reader with `calmeter` so the two development tools do
not continue to diverge. Add fixtures for 44.1 and 48 kHz PCM stereo and
rejection cases for mono, float/non-PCM, missing/truncated `fmt `, and missing
`data`.

## Notes

`raw_dump` currently produces only 44.1 kHz float WAVs, but the shipping CLI
supports `--rate 48000` and the example describes itself as a WAV meter rather
than a raw-dump-only meter. Its purpose is to distinguish limiter defects from
meter defects, so authoritative-looking wrong measurements are a real
calibration risk.
