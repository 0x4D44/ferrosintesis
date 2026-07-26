# MM-BUG-KILN-00121 — Clavinet README implies every other sample crate is CC0

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** sample licensing documentation
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
- **State history:** Open (2026-07-25, raised by Codex GPT-5.6-Sol during the coverage-ledger review of `crates/ferrosintesis-samples-clavinet/`) → Fixed (2026-07-26, GPT-5.6 Codex on KILN-Windows — the package now names the mixed CC0/MIT/CC BY licence set and links the derived distribution inventory) → Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: GPT-5.6 Codex on KILN-Windows), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree at b0b93d9: `cargo fmt --all --check`, `clippy --workspace --exclude amp-lab --all-targets -D warnings`, `clippy -p ferrosintesis --no-default-features --all-targets -D warnings`, `test -p ferrosintesis --no-default-features --locked` (628 passed) and `test --workspace --exclude amp-lab --locked` (731 passed) - 1461 tests, 0 failures. Original observation re-run at source: the parenthetical "unlike ferrosintesis's other, CC0, sample crates" is gone. `crates/ferrosintesis-samples-clavinet/README.md` now states "Some sibling banks are CC0, while others use MIT or CC BY" and links the authoritative inventory. I verified the link rather than assuming it: the target `#sample-provenance-and-licensing` resolves to the real `## Sample provenance and licensing` heading at `crates/ferrosintesis/README.md:192`, and the `0x4D44/ferrosintesis` repository URL is this crate's own declared `repository` field, used consistently across all 25 sample crates - not a typo for the enclosing repo. The reading that would tell a distributor the sibling banks need no attribution is no longer available. Both clavinet package tests and all seven derived licensing tests green.)

## Observation

`crates/ferrosintesis-samples-clavinet/README.md:13-14` describes this crate's
MIT samples as “unlike ferrosintesis's other, CC0, sample crates.” The commas
make `CC0` describe the other sample crates as a group.

The authoritative distribution table at
`crates/ferrosintesis/README.md:194-220` says that ten of the twenty-five
default sample crates require attribution. Nine other crates use MIT or CC BY
3.0/4.0, including `ferrosintesis-samples-musescore`,
`ferrosintesis-samples-grand`, and `ferrosintesis-samples-sax`.

**Expected.** The package README must distinguish this MIT bank from the CC0
banks without implying that every sibling bank is CC0, so distributors are
directed toward the complete notice inventory.

**Actual.** The summary can be read as saying the other sample crates are CC0
and therefore need no attribution. The target crate's own `NOTICE` is complete;
the defect is the inaccurate cross-crate summary.

## Fix

Rewrite the parenthetical as “unlike ferrosintesis's CC0 sample crates,” or
explicitly say that other banks also use MIT and CC BY licences. Link the
authoritative distribution table in `crates/ferrosintesis/README.md`.

Add or extend a documentation oracle only if it can derive this claim from the
licensing inventory; do not add another hand-maintained count.

## Notes

This read-only review did not run the application, tests, builds, or the
exploratory-test harness. The finding was confirmed from the target README and
the current manifest-derived licensing inventory.

## Resolution — 2026-07-26

The package README now states that sibling banks span CC0, MIT, and CC BY
licences. It links directly to the authoritative `ferrosintesis` distribution
inventory and keeps this bank's own `NOTICE` obligation explicit. The inaccurate
claim that every other sample crate is CC0 is gone.

No new count or wording oracle was added. The existing licence tests already
derive the attribution-bearing set from manifests and NOTICE files; duplicating
that set in a new documentation assertion would recreate the maintenance hazard
this record warns against.

## Verification — 2026-07-26

- The stale phrase no longer exists, and the new link's repository and Markdown
  anchor match the checked-in authoritative table.
- Both clavinet package tests pass.
- All seven derived licensing tests pass.
- `git diff --check` passes.
