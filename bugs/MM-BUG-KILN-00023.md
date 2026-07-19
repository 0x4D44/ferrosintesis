# MM-BUG-KILN-00023 — BAR_FULL anti-clone threshold has no failing negative anchor

- **State:** Closed
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
- **State history:** Open (2026-07-18, raised via `deltic bugs new` model=gpt-5@xhigh); Fixed (2026-07-18, 2d8f0b3 — added a deterministic full-tier near-clone scoring 0.02625 below BAR_FULL 0.075. A threshold mutation to 0.020 fails the guard, while the existing positive calibration remains green.); Closed (2026-07-19, verified by Claude Opus 4.8 (1M context) - independent two-eyes (fixer gpt-5@xhigh); bar_full_rejects_near_clone_negative_control green - deterministic near-clone scores 0.025-0.030, below BAR_FULL 0.075; gates green)

## Observation

Observation: testutil.rs BAR_FULL is accepted only by positive voice pairs; no synthetic or frozen near-clone is known to fall below it. Expected: a deterministic negative control proves the full-tier threshold detects a perceptual clone. Actual: all current full-tier cases pass, so threshold weakening or a vacuous bar can stay green. Repro: inspect perceptual_distinctness controls and run the full-tier tests; no negative exemplar is asserted. Split from MM-BUG-KILN-00006 during independent closure.

## Fix

2d8f0b3 adds bar_full_rejects_near_clone_negative_control. The synthetic
Passport starts from a real samples-on GM64 render, then applies a barely
full-tier 3% onset-level difference and half one attack-time JND. Its score is
nonzero and frozen to 0.025..=0.030, yet it must remain below BAR_FULL because
those changes do not create a distinct instrument.

The regression passes at BAR_FULL 0.075 and fails when the bar is mutation-lowered
to 0.020: score 0.02625 is no longer rejected. The existing positive calibration
also passes, preserving both sides of the threshold gap.

### Verification summary (Claude Opus 4.8 (1M context), 2026-07-19)

Independent two-eyes on a worktree off origin/main (0cc8e7f, contains fix 2d8f0b3; verifier is not the fixer, Codex gpt-5@xhigh). The regression `bar_full_rejects_near_clone_negative_control` passed in the green `cargo test --workspace` suite: a deterministic full-tier near-clone (3% onset delta + half an attack-time JND on a real GM64 render) is classified Full tier, scores within 0.025..=0.030, and is asserted below BAR_FULL (0.075) - the previously-missing failing negative anchor for the full-tier threshold now exists. Gates green.

## Notes
