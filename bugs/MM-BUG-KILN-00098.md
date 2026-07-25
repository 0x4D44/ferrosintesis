# MM-BUG-KILN-00098 — A 1–4 Hz WAV makes calmeter loop forever while growing memory

- **State:** Fixed
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
- **State history:** Open (2026-07-25, raised by Codex GPT-5.6-Sol during the `crates/ferrosintesis-cli/` coverage review) → Fixed (2026-07-25, Codex GPT-5.6-Sol; calmeter rate validation and zero-hop loudness hardening landed with regression coverage; awaiting independent two-eyes verification)

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

`calmeter::read_wav` now documents and enforces an 8 kHz minimum input rate,
which is the lowest conventional PCM rate with enough bandwidth for its
BS.1770 K-weighting filter. A one-frame 1 Hz RIFF is rejected immediately, and
an 8 kHz boundary fixture is accepted.

The shared loudness block builder now computes and validates its rounded 400 ms
block and 100 ms hop before allocating or filtering. A zero block or hop returns
an empty momentary series; integrated loudness consequently returns negative
infinity. Coverage exercises every rate from 0 through 4 Hz, while the existing
44.1/48 kHz EBU calibration and all other loudness tests remain green.

The 1 Hz calmeter regression failed before the fix because `read_wav` accepted
the file. The complete calmeter example suite, all loudness tests, and focused
clippy pass after the fix.

## Notes

The tool is dev-only and normal calibration files are 44.1 kHz, which limits
exposure but does not change the deterministic nontermination.
