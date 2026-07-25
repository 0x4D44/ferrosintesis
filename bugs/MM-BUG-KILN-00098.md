# MM-BUG-KILN-00098 — A 1–4 Hz WAV makes calmeter loop forever while growing memory

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/ferrosintesis-cli/examples/calmeter
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
read-only): give `calmeter` a small RIFF/WAVE containing at least one stereo
frame, a format chunk declaring a sample rate from 1 through 4 Hz, and a plan
row whose onset is frame 0.

`crates/ferrosintesis-cli/examples/calmeter.rs:102-145` validates the container,
channel count, and bit depth, but accepts the declared sample rate without a
lower bound. The one-frame note window reaches `momentary_lufs` at
`crates/ferrosintesis-cli/examples/calmeter.rs:203`.

In `crates/ferrosintesis/src/loudness.rs:124-140`, the 100 ms hop rounds to zero
at 1–4 Hz. The loop condition remains true, `start += hop` never advances, and
the function keeps appending blocks until the process is stopped or exhausts
memory.

Expected: reject an unsupported sample rate promptly.

Actual: a tiny input can make the development calibration tool nonterminating
and memory-growing.

## Fix

Not fixed in this review. Validate `sr` against the meter's documented supported
range in `calmeter::read_wav`. Also harden the public loudness primitive so a
rounded zero block or hop returns an error/empty result instead of looping,
protecting future callers.

Add a minimal 1 Hz RIFF regression that proves prompt rejection, plus boundary
coverage for the lowest supported rate.

## Notes

The tool is dev-only and normal calibration files are 44.1 kHz, which limits
exposure but does not change the deterministic nontermination.
