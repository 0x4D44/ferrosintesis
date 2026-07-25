# MM-BUG-KILN-00117 — EAR_DECIDED is a surviving hand-copy of engine.rs's deliberate-zero pins, so a fifth pin silently lets the tool re-litigate an ear decision

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
- **State history:** Open (2026-07-25, raised by Claude Opus 5 (1M) @ high during the independent two-eyes verification of MM-BUG-KILN-00109; it falsifies that bug's fix-note claim (e))

## Observation

MM-BUG-KILN-00109's fix note claims "There is no second list left to drift."
That claim is FALSE and has been withdrawn in that bug's verification summary.

`tools/instrument-balance/derive_trims.py:176` carries

    EAR_DECIDED = {0, 1, 3, 11}

which is a hand-copy of the "Deliberate ZEROS" pinned in
`crates/ferrosintesis/src/engine.rs:4384` (GM11) and `:4392-4394` (GM0/1/3) —
whose own comment says they are "pinned to stop a future derivation silently
re-litigating them". That is precisely what the drift enables.

It is load-bearing on output in two places:
- `derive_trims.py:593` — the residual-oracle watch predicate;
- `derive_trims.py:651` — `held = p in EAR_DECIDED`, commented "never auto-change it".

CONSEQUENCE. Add a fifth deliberate zero to `engine.rs` and the tool silently
re-proposes a change that an ear already ruled on — with no warning, because a
0.0 in the trim table is indistinguishable from "not yet trimmed". This is the
same class as the defect 00109 fixed (a hand-copy of engine.rs state going stale),
in the same file, and it survived that fix.

The pins carry real authority: MM-BUG-KILN-00107's verification found that GM8 and
GM110 were shipped 19 minutes after a report recommending Arthur hear them first,
so the mechanism protecting ear decisions is not theoretical safety margin.

## Suggested fix

`EAR_DECIDED` cannot be derived from the table's VALUES — 0.0 is ambiguous by
design, as the tool's own comment says. But it CAN be derived from the pinned-zeros
assert text in `engine.rs`, using the same file read `load_shipped()` already does.
Derive it, and raise if the parse finds nothing, matching the fail-loud contract
`load_shipped()` established.

Fix alongside MM-BUG-KILN-00116 — same file, same function, same defect class.

## Notes
