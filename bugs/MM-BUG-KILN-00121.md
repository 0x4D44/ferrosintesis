# MM-BUG-KILN-00121 — Clavinet README implies every other sample crate is CC0

- **State:** Open
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
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, raised by Codex GPT-5.6-Sol during the coverage-ledger review of `crates/ferrosintesis-samples-clavinet/`)

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
