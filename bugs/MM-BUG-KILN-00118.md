# MM-BUG-KILN-00118 — PROGRAM_TRIM_DB has no committed residual baseline, so trim staleness can only ever be found by a manual re-derive

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth / instrument balance
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
- **State history:** Open (2026-07-25, raised by Claude Opus 5 (1M) @ high during the independent two-eyes verification of MM-BUG-KILN-00107; it is that report's own section-4 remedy, left unimplemented)

## Observation

MM-BUG-KILN-00107 exists because `PROGRAM_TRIM_DB` was calibrated on 2026-07-17
and nobody could say whether it was still valid. The 2026-07-25 closed-loop
re-derive answered that question for one moment in time — and left no artifact
that would answer it again.

The report's own section 4 states the remedy: "keeping a per-program residual
baseline in the repo and diffing against it, rather than reading each run
standalone". It was NOT implemented. The only residual data in the repo is prose
inside markdown reports. Its section-5 remedy (deriving `SHIPPED` from engine.rs)
WAS implemented in the same commit, ff31237 — so this is a skipped half, not an
oversight of the whole.

The existing oracles do not cover it. `crates/ferrosintesis/src/balance.rs:127`
and `:184` assert the trim table is APPLIED to the audio; neither asserts its
values are still CORRECT. Those are different properties, and only the first is
guarded.

So the same bug recurs on the next voice-work run: 165 commits of voice changes
landed between the 07-17 calibration and the 07-25 re-derive, and the only reason
anyone knew to check was a human raising MM-BUG-KILN-00107 by hand.

This also matters for MM-BUG-KILN-00108's lesson. The GM85 16 dB regression was
invisible to the residual oracle because a guard-excluded program is silently
dropped rather than reported — the regression was large enough to trip the
pitch-tilt guard, so it excluded itself from the check that would have caught it.
Only a CROSS-RUN drift comparison found it, which is exactly what a committed
baseline would make routine instead of exceptional.

## Suggested fix

Commit a per-program residual baseline (a small CSV or a Rust table) and add an
oracle that diffs the current derivation against it, failing on drift beyond a
stated bar. Two properties matter and are easy to get wrong:

1. A guard-EXCLUDED program must be REPORTED, not silently dropped — that is the
   hole MM-BUG-KILN-00108 fell through, and it is named in that bug's own "WHY
   NOTHING CAUGHT IT" section.
2. The baseline must record WHICH reference each figure came from and whether it
   was guard-excluded, or a re-run cannot tell "unmeasurable" from "fine". GM6 is
   the live example: excluded on both references, drifting +1.46 / -1.07 dB.

Note this needs mdmidiemu plus the SC-55 ROMs to regenerate, so the baseline is
the only thing that makes the check cheap enough to run routinely.

## Notes
