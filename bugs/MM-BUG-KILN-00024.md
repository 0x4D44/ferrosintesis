# MM-BUG-KILN-00024 — GM 48/49 ensemble identity remains EarPending and unenforced

- **State:** Open
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
- **State history:** Open (2026-07-18, raised via `deltic bugs new` model=gpt-5@xhigh)

## Observation

Observation: perceptual_distinctness still carries GM 48/49 as an EarPending pair, so the oracle exerts no pass/fail force over whether string ensemble 1 and 2 are acceptably distinct. Expected: one human A/B adjudication records a durable verdict and converts it into an enforced positive or collapse expectation. Actual: the standing EarPending entry remains indefinitely non-binding. Repro: inspect the GM 48/49 adjudication and run print_perceptual_matrix. Split from MM-BUG-KILN-00006 during independent closure.

## Fix

<unfixed — raised only>

## Notes
