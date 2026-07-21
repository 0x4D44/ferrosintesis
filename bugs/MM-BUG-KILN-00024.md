# MM-BUG-KILN-00024 — GM 48/49 ensemble identity remains EarPending and unenforced

- **State:** Blocked
- **Priority:** Could
- **Severity:** Medium
- **Area:** testutil
- **Raised:** 2026-07-18
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
- **State history:** Open (2026-07-18, raised via `deltic bugs new` model=gpt-5@xhigh) → Blocked (2026-07-21, Claude Opus 4.8 — the bug's resolution requires "one human A/B adjudication" of GM48/49 string-ensemble distinctness; a human ear verdict is a hard external dependency, not an unattended code fix.)

## Observation

Observation: perceptual_distinctness still carries GM 48/49 as an EarPending pair, so the oracle exerts no pass/fail force over whether string ensemble 1 and 2 are acceptably distinct. Expected: one human A/B adjudication records a durable verdict and converts it into an enforced positive or collapse expectation. Actual: the standing EarPending entry remains indefinitely non-binding. Repro: inspect the GM 48/49 adjudication and run print_perceptual_matrix. Split from MM-BUG-KILN-00006 during independent closure.

## Fix

<blocked — needs a human A/B ear adjudication>

## Notes

- Blocked 2026-07-21 (Claude Opus 4.8) during a bug-drain pass. The defect is by
  construction ear-gated: converting the standing GM48/49 `EarPending` entry into an
  enforced positive/collapse expectation *is* recording a human A/B listening verdict.
  An unattended agent (this box has no ears) cannot produce that verdict without
  fabricating it. **Missing input to unblock:** Arthur's A/B adjudication of string
  ensemble 1 vs 2, after which the enforced oracle is a small mechanical follow-up.
