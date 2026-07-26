# MM-BUG-KILN-00066 — A long-held GM76 note overflows its per-voice sample clock

- **State:** Closed
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol during the coverage-ledger review of `crates/ferrosintesis-samples-bottle/`) → Fixed (2026-07-26, GPT-5.6 Codex on KILN-Windows — widened both copied loop-voice clocks and pinned modulation continuity across the old boundary) → Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: GPT-5.6 Codex on KILN-Windows), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree at b0b93d9: `cargo fmt --all --check`, `clippy --workspace --exclude amp-lab --all-targets -D warnings`, `clippy -p ferrosintesis --no-default-features --all-targets -D warnings`, `test -p ferrosintesis --no-default-features --locked` (628 passed) and `test --workspace --exclude amp-lab --locked` (731 passed) - 1461 tests, 0 failures. Original observation re-run at source: `BottleLoopVoice::t` (`sampler.rs:4128`) and the copied `SaxLoopVoice::t` (`:3860`) are both `u64`; at 44.1 kHz that clock cannot exhaust in any real session. `loop_voice_clocks_cross_u32_boundary_without_modulation_reset` starts both voices 511 samples below the old `u32::MAX`, compares each against a reference aligned to the same drift-scheduler phase, and asserts byte-identical output PLUS `t > u32::MAX` - so the test proves the boundary was genuinely crossed rather than passing vacuously. I checked the one remaining `t: u32` (`:2695`) as a possible residual and it is NOT the same defect: it belongs to the bagpipe `LoopVoice`, which advances with an explicit `wrapping_add(1)` (so no debug overflow panic) and consumes `t` only through `is_multiple_of` for the drift cadence - it never derives elapsed time from it, so there is no vibrato bloom to reset. The resolution's decision to leave it alone is correct; no residual to split. Test green in debug and via the gate.)

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

## Resolution — 2026-07-26

`BottleLoopVoice::t` and the copied `SaxLoopVoice::t` are now `u64`. Their
drift-cadence check converts the shared `u32` period at the comparison site, so
the unrelated explicitly wrapping bagpipe `LoopVoice` scheduler stays
unchanged.

The new `loop_voice_clocks_cross_u32_boundary_without_modulation_reset`
regression starts both affected voices 511 samples below the old maximum. It
compares each against a settled reference with the same drift-scheduler phase,
renders across the boundary, and requires byte-identical output plus a clock
greater than `u32::MAX`.

## Verification — 2026-07-26

- Fail-first on the original `u32` clock reproduced the debug overflow panic at
  `sampler.rs:4228`.
- The boundary-crossing regression passes for bottle and sax in debug and
  release profiles; neither clock panics, wraps, or resets modulation.
- The complete default suite passed (728 tests, 27 ignored), the true
  model-only suite passed (626 tests, 22 ignored), and both doc-test sets passed
  (4 each).
- Strict workspace clippy and true model-only clippy passed with warnings
  denied; formatting and `git diff --check` passed.
- Fresh release binaries from exact baseline `9e08340`, full 124-MIDI inventory
  at 11.025 kHz: all 124 stayed byte-identical, with zero contamination and
  zero missed paths. Normal-duration renders remain exactly unchanged.

## Notes

- The copied `SaxLoopVoice` clock has the same shape. A shared fix should cover both,
  but this pass independently confirmed the bottle path.
- Reliability, devil's-advocate, and team-lead source passes confirmed the arithmetic.
  No hours-long render was run.

