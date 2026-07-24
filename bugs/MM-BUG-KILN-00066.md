# MM-BUG-KILN-00066 — A long-held GM76 note overflows its per-voice sample clock

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sampler / voice lifecycle
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol during the coverage-ledger review of `crates/ferrosintesis-samples-bottle/`)

## Observation

**Symptom.** `BottleLoopVoice` sustains until NoteOff but stores its rendered-sample
clock in a `u32`.

**Expected.** A valid indefinitely held realtime note should not panic or reset its
modulation state because an internal clock wraps.

**Actual.**
`D:\worktrees\midi-music\20260724-REV-CLA@KILN-code-review-065916\crates\ferrosintesis\src\sampler.rs:3385`
declares `t: u32`, line 3446 derives elapsed time from it, lines 3449 and 3457 use it
for vibrato bloom and drift scheduling, and line 3487 increments it with
`self.t += 1`.

The counter exhausts after:

- 27.05 hours at 44.1 kHz;
- 24.86 hours at 48 kHz;
- 12.43 hours at 96 kHz;
- 6.21 hours at 192 kHz.

Debug builds and consumers enabling overflow checks panic during audio rendering.
Ordinary release builds wrap to zero, abruptly remove vibrato for 0.2 seconds,
re-bloom it over 0.35 seconds, and force a drift-target update. The voice's sustain
envelope remains alive until NoteOff, so normal MIDI semantics can reach the wrap.

## Fix

Use a `u64` sample clock and keep the drift cadence calculation type-compatible.
Alternatively, separate a saturating onset/bloom clock from an explicitly wrapping
modulation scheduler. Add a unit test that initializes the private counter near its
boundary and proves rendering remains finite, non-panicking, and modulation-continuous.

## Notes

- The copied `SaxLoopVoice` clock has the same shape. A shared fix should cover both,
  but this pass independently confirmed the bottle path.
- Reliability, devil's-advocate, and team-lead source passes confirmed the arithmetic.
  No hours-long render was run.

