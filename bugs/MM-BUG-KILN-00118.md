# MM-BUG-KILN-00118 — PROGRAM_TRIM_DB has no committed residual baseline, so trim staleness can only ever be found by a manual re-derive

- **State:** Fixed
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, raised by Claude Opus 5 (1M) @ high during the independent two-eyes verification of MM-BUG-KILN-00107; it is that report's own section-4 remedy, left unimplemented) → Fixed (2026-07-25, GPT-5.6 Codex on KILN-Windows — every panel run now checks a committed two-reference residual/guard baseline, including excluded programs)

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

## Resolution — 2026-07-25

`tools/instrument-balance/residual-baseline.csv` records all 128 programs for
both canonical references. Every row retains the residual, contemporaneous
shipped trim, and guard-excluded state; a blank residual explicitly means the
program/reference pair was unmeasurable. The seed is the complete, observed
2026-07-22 panel recorded in
`wrk_docs/2026.07.22 - M-CAL v3 reference-panel derivation report.md`.

Panel mode now compares all 256 rows by default. It fails on normalized residual
drift over 1.0 dB, measurability changes, missing rows, or guard-state changes.
The normalized quantity is `residual + shipped_db`, so an intentional scalar
trim change does not masquerade as voice drift. Guard-excluded rows remain in
the same comparison and failure path; they are never filtered out.

An explicit `--write-baseline PATH` mode writes a complete candidate after a
new SC-55/Yamaha capture run. It does not replace the accepted baseline unless
the caller deliberately names that path and reviews the result.

## Verification — 2026-07-25

- `python tools/instrument-balance/derive_trims.py --selftest` passes. It proves
  an intentional trim change cancels, an excluded GM6 residual drift still
  fails, guard/measurability transitions fail, and an incomplete baseline is
  rejected.
- The focused Rust balance suite passes six tests with one diagnostic ignored.
  Its ordinary-gate source/data oracle requires 256 unique program/reference
  rows, pins GM6 excluded on both references, and requires the comparison to
  remain on panel mode's exit path.
- `$null | cargo test --locked -p ferrosintesis`: **721 unit tests and 4 doc
  tests passed; 27 diagnostics ignored**.
- `$null | cargo test --locked -p ferrosintesis --no-default-features`: **620
  unit tests and 4 doc tests passed; 22 diagnostics ignored**.
- Strict all-target clippy passes for the workspace and for ferrosintesis
  without default features. Formatting, Python byte-compilation, and
  `git diff --check` pass.
- No audio render inventory is required: this pass changes the offline
  calibration tool, its baseline data, a Rust test oracle, and the bug ledger;
  it does not change rendered audio.
