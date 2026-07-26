# MM-BUG-KILN-00117 — EAR_DECIDED is a surviving hand-copy of engine.rs's deliberate-zero pins, so a fifth pin silently lets the tool re-litigate an ear decision

- **State:** Closed
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, raised by Claude Opus 5 (1M) @ high during the independent two-eyes verification of MM-BUG-KILN-00109; it falsifies that bug's fix-note claim (e)) → Fixed (2026-07-25, GPT-5.6 Codex on KILN-Windows — the tool now derives every recorded zero decision from engine.rs in the same read as the shipped trim table) → Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: GPT-5.6 Codex on KILN-Windows), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree at b0b93d9: `cargo fmt --all --check`, `clippy --workspace --exclude amp-lab --all-targets -D warnings`, `clippy -p ferrosintesis --no-default-features --all-targets -D warnings`, `test -p ferrosintesis --no-default-features --locked` (628 passed) and `test --workspace --exclude amp-lab --locked` (731 passed) - 1461 tests, 0 failures. Original observation re-run by executing the parser, not by reading it. The literal `EAR_DECIDED = {0, 1, 3, 11}` is gone; `load_shipped()` (`derive_trims.py:209`) returns the shipped trim table and the derived pin set from ONE read of `engine.rs`, assigned jointly at `:218`. I imported the module and checked the behaviour directly: it derives exactly `[0, 1, 3, 11]` from the real `engine.rs`, matching the hand-copy it replaced; feeding it an `engine.rs` text with a FIFTH pin added (GM42) yields `[0, 1, 3, 11, 42]`, so the precise consequence the bug describes - a new deliberate zero being silently re-litigated - no longer occurs. The fail-loud contract holds on all three degenerate inputs I tried: no pins, a duplicate pin, and an out-of-range program each raise a named `SystemExit`. `derive_trims.py --selftest` and `trim_derivation_reads_one_exact_engine_state` are green.)

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

## Resolution — 2026-07-25

`derive_trims.py` no longer contains a literal program-number set. Its one
`engine.rs` load now returns both the shipped trim table and the programs named
by canonical ``assert_eq!(PROGRAM_TRIM_DB[P], 0.0);`` pins. A newly added pin
there immediately becomes held by the panel and monitored by the residual
oracle.

The parser fails loudly when it finds no pins, a duplicate pin, or a program
outside 0–127. A normal-gate Rust source oracle requires the parser safeguards
and exactly one joint `SHIPPED, EAR_DECIDED = load_shipped()` assignment, so a
future literal or second load recreates a test failure rather than drift.

## Verification — 2026-07-25

- `python tools/instrument-balance/derive_trims.py --selftest` passes. Its
  fixtures prove a fifth multiline pin is derived and that empty, duplicate,
  out-of-range, and nonzero pseudo-pins are rejected.
- The focused Rust balance suite passes five tests with one diagnostic ignored.
- `$null | cargo test --locked -p ferrosintesis`: **720 unit tests and 4 doc
  tests passed; 27 diagnostics ignored**.
- `$null | cargo test --locked -p ferrosintesis --no-default-features`: **619
  unit tests and 4 doc tests passed; 22 diagnostics ignored**.
- Strict all-target clippy passes with all features and with no default
  features. Formatting and `git diff --check` pass.
- No audio render inventory is required: the Rust change is `#[cfg(test)]`, and
  the Python derivation tool does not ship in the synth.
