# MM-BUG-KILN-00024 — GM 48/49 ensemble identity remains EarPending and unenforced

- **State:** Blocked
- **Priority:** Could
- **Severity:** Medium
- **Area:** testutil
- **Raised:** 2026-07-18
- **Owner:** Arthur
- **Owner role:** human
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
- **State history:** Open (2026-07-18, raised via `deltic bugs new` model=gpt-5@xhigh) → Blocked (2026-07-25, GPT-5.6 Codex on KILN-Windows — the oracle deliberately cannot decide whether GM48/49's shared-onset tail difference is perceptually sufficient; Arthur must supply the one planned same/different A/B verdict)

## Observation

Observation: perceptual_distinctness still carries GM 48/49 as an EarPending pair, so the oracle exerts no pass/fail force over whether string ensemble 1 and 2 are acceptably distinct. Expected: one human A/B adjudication records a durable verdict and converts it into an enforced positive or collapse expectation. Actual: the standing EarPending entry remains indefinitely non-binding. Repro: inspect the GM 48/49 adjudication and run print_perceptual_matrix. Split from MM-BUG-KILN-00006 during independent closure.

## Fix

The code already routes this exact pair through the design's human-adjudication
seam. The measured shared-onset tail score is 0.0602, below the frozen 0.76 bar,
but that metric only says numeric distinctness is unproven. It cannot decide
whether String Ensemble 1 and Slow Strings sound acceptably different.

### Blocker — 2026-07-25

Blocking owner: **Arthur**. Unblock after one level-matched, same-note A/B of
GM48 and GM49 at the oracle's two probe registers (keys 48 and 72) answers:

1. **Different enough:** record the pair as ear-accepted and add a positive
   assertion so it cannot collapse later.
2. **Too similar:** replace the `EarPending` entry with a voice-fix requirement
   for a durable Slow Strings identity, then implement and prove that change in
   a separate Build pass.

The listening question is specifically whether GM49's slower swell reads as a
real identity difference after its sampled-onset/model handover, not merely
whether the files differ numerically. Choosing either route unattended would
invent the product verdict this bug exists to preserve.

## Notes

- `crates/ferrosintesis/src/testutil.rs::print_perceptual_matrix` remains the
  metric diagnostic. Run it with
  `cargo test -p ferrosintesis print_perceptual_matrix -- --ignored --nocapture`
  when recording the adjudication.
- The original listening queue is
  `wrk_journals/2026.07.16 - JRN - round3 voice-quality build.md`, lines
  119–124. It explicitly calls for one same/different listen and then either an
  ear-accepted assertion or voice work.
