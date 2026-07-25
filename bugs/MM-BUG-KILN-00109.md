# MM-BUG-KILN-00109 — derive_trims.py's SHIPPED table is a stale hand-copy of PROGRAM_TRIM_DB and would undo shipped trims

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** tooling / instrument balance
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
- **State history:** Open (2026-07-25, raised via `deltic bugs new` model=claude-opus-5-1m@high)

## Observation

`tools/instrument-balance/derive_trims.py` carries a hand-copied `SHIPPED` table
mirroring `PROGRAM_TRIM_DB` in `crates/ferrosintesis/src/engine.rs`. Commit
fc1ef10 applied five trims to engine.rs (GM5 +1, GM8 +2, GM14 -6, GM110 -5,
GM119 +1) and never updated the tool's copy. Nothing ties the two together —
no oracle, no test, no generator.

CONSEQUENCE, measured on the 2026-07-25 closed-loop re-derive over identical
data: the committed tool proposes

    GM14   0 -> -5      (undoing the shipped -6)
    GM110  0 -> -2      (a +3 dB move in the WRONG direction)

i.e. it would undo trims that are already in place. It also drops those five
programs out of the residual oracle's watch list, so the certificate that is
supposed to police them silently stops covering them.

The re-derive run had to work around this with a throwaway wrapper that patches
`SHIPPED` from engine.rs at run time; without it the run is invalid. That
workaround should not be needed.

FIX BY DERIVATION, NOT BY RE-COPYING. Parse `PROGRAM_TRIM_DB` out of engine.rs
at tool start-up (about eight lines). Re-copying the numbers reproduces the
defect the moment the next trim lands — this repo has the same failure mode
recorded three times over in CLAUDE.md's "Hand-maintained lists are the recurring
defect here — derive them".

## Fix

<unfixed — raised only>

## Notes
