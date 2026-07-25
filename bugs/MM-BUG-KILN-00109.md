# MM-BUG-KILN-00109 — derive_trims.py's SHIPPED table is a stale hand-copy of PROGRAM_TRIM_DB and would undo shipped trims

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
- **State history:** Open (2026-07-25, raised via `deltic bugs new` model=claude-opus-5-1m@high) → Fixed (2026-07-25, Claude Opus 5 (1M) in `ff31237`; `SHIPPED` derived from `PROGRAM_TRIM_DB` via `load_shipped()`) → Closed (2026-07-25, independent verification by Claude Opus 5 (1M) @ high, fresh context; derivation proved live against engine.rs, WITH a correction to the fix note and two new defects raised — see the verification note below)

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

## Fix (2026-07-25)

Fixed in ff31237. `SHIPPED` is now parsed from `PROGRAM_TRIM_DB` in engine.rs at
tool start-up and raises rather than falling back to zeros - a silently-empty
table looks exactly like "nothing is trimmed yet" and would bias every proposal
the same way. There is no second list left to drift.

The fix exposed a second coupling of the same kind: the selftest was asserting
its expectations against the LIVE production table, so a shipped trim could turn
it red. Its fixture now carries its own `ST_SHIPPED`, deliberately independent.
`--selftest` passes.

NOT closed by its own fixer - the ledger's two-eyes rule applies.

### Verification summary (2026-07-25, independent second eyes)

Verified by a fresh-context Claude Opus 5 (1M) chain (one verifier plus two
adversarial refuters briefed to BLOCK closure), on trunk 802753c. Closed - the
reported defect is gone by derivation, which is the right layer.

WHAT WAS EXECUTED, not read off the fix note:

- Imported the module against the live `engine.rs`: `len(SHIPPED)=128`,
  `nonzero=54`, matching `engine.rs:1180-1195` row for row including every sign.
  fc1ef10's five previously-missed trims read back live and non-zero
  (GM5 +1, GM8 +3, GM14 -6, GM110 -6, GM119 +1), so they are back inside the
  residual oracle's watch predicate at `derive_trims.py:593`.
- The derivation is live, not decorative: editing `engine.rs` GM6 `6.0 -> -12.0`
  moved `SHIPPED[6]` to -12.0 while `ST_SHIPPED[6]` stayed 6.0, confirming the
  selftest fixture is genuinely independent (claim (c)).
- The fail-loud contract holds on four failure modes - rename, `[f32; 8]`
  reshape, a 129th entry, and a missing file - each raising with the named error
  and NO zeros fallback (claim (b)).
- A 20-case adversarial perturbation suite over the parser produced NO silent
  drops: whitespace, integer literals, `-0.0`, `-6.`, `1e0`, missing trailing
  comma, split entries, one-per-line rustfmt style, `//`-commented entries and a
  `]`-bearing comment all parsed correctly or raised.

CORRECTION TO THE FIX NOTE. Claim (e), "There is no second list left to drift",
is WITHDRAWN - it is false as written. `EAR_DECIDED = {0, 1, 3, 11}` at
`derive_trims.py:176` is still a hand-copy of the deliberate-zero pins at
`engine.rs:4384-4394`, and it is load-bearing on output at `derive_trims.py:593`
and `:651`. Raised as MM-BUG-KILN-00117.

The verification also found a defect INTRODUCED by this fix - the parser regex is
unanchored and unchecked for uniqueness, so a sibling declaration silently yields
a wrong table. Raised at Must as MM-BUG-KILN-00116. Neither blocks this closure:
the reported hand-copy is genuinely gone, and both are separate defects rather
than an unfinished half of it.

NO IN-SUITE REGRESSION TEST EXISTS for the reported instance, and that is stated
rather than glossed: nothing in the repo executes `derive_trims.py`,
`.deltic-integrate.toml` is cargo-only, and `--selftest` asserts against its own
`ST_SHIPPED` fixture and never touches `SHIPPED`, so it cannot detect a wrong
derived table. Protection today is structural (no copy left to go stale) plus the
loud-raise path. Closing on that basis is a deliberate judgment, not an oversight.

Ledger hygiene: this bug's Observation quotes fc1ef10's trims as GM8 +2 and
GM110 -5; trunk now holds +3 and -6, landed by ff31237 (the same commit as this
fix). The text is correct as history but misleads if read as current.
