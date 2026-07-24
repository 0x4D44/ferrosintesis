# MM-BUG-KILN-00060 — The ferrosintesis licence guide omits its default CC-BY Rhodes and dulcimer dependency

- **State:** Open
- **Priority:** Must
- **Severity:** Medium
- **Area:** packaging / licensing
- **Raised:** 2026-07-24
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol during the coverage-ledger review of `crates/ferrosintesis-samples-ccby/`)

## Observation

**Symptom.** The shipped `ferrosintesis` README presents the non-CC0 sample-bank
licensing inventory at `crates/ferrosintesis/README.md:191-221`, but it does not mention
`ferrosintesis-samples-ccby`, the Rhodes and dulcimer recordings, their two authors, or
their required CC-BY 4.0 notice.

**Expected.** A distributor following the parent crate's licensing guide can discover
and reproduce every required attribution for the default embedded sample set.

**Actual.** The default `embedded-samples` feature includes
`ferrosintesis-samples-ccby` at `crates/ferrosintesis/Cargo.toml:32-37`, with the
dependency declared at line 72. The parent package include list carries only its own
README and MIT/Apache licences. The dependency's correct `NOTICE` is packaged by the
asset crate, but it is not surfaced by the parent guide that downstream binary
distributors are most likely to follow. A distributor can therefore miss the required
credits.

This is a compliance risk, not a claim that
`crates/ferrosintesis-samples-ccby/NOTICE` itself is invalid.

## Fix

Add the CC-BY sample crate, both credited authors, and a link to its notice to the
parent README's licensing inventory. State explicitly which third-party notices binary
distributors must reproduce. Prefer generating or validating a consolidated
third-party notice from the default non-CC0 dependency set so a future sample crate
cannot be omitted silently.

## Notes

- The asset crate's own `Cargo.toml:10` correctly packages `NOTICE`,
  `PROVENANCE.md`, README, source, and samples.
- No existing bug or open requirement matched this specific attribution omission.
- No external legal conclusion was made; the review checked only repository contents.

