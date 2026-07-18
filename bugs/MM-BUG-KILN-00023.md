# MM-BUG-KILN-00023 — BAR_FULL anti-clone threshold has no failing negative anchor

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

Observation: testutil.rs BAR_FULL is accepted only by positive voice pairs; no synthetic or frozen near-clone is known to fall below it. Expected: a deterministic negative control proves the full-tier threshold detects a perceptual clone. Actual: all current full-tier cases pass, so threshold weakening or a vacuous bar can stay green. Repro: inspect perceptual_distinctness controls and run the full-tier tests; no negative exemplar is asserted. Split from MM-BUG-KILN-00006 during independent closure.

## Fix

<unfixed — raised only>

## Notes
