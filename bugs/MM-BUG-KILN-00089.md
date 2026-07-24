# MM-BUG-KILN-00089 — The mandolin package still describes the retired two-dynamic bank and omits its legal text

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** mandolin sample package / documentation
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-mandolin/`)

## Observation

**Symptom.** The published package and maintainer documentation disagree with
the shipped bank and with one another:

- `crates/ferrosintesis-samples-mandolin/README.md:3-5` says the ten zones have
  two dynamic layers. The crate actually embeds one dynamic with four ordered
  round robins (`src/lib.rs:1-173`; `PROVENANCE.md:44-50`).
- `README.md:15-17` points readers to a retired layer-selection measurement and
  a “known weak point” that the current provenance file does not contain.
- `tools/ferrosintesis-samples/prepare.py:1001-1008` repeats the retired
  two-dynamic description.
- `crates/ferrosintesis/src/sampler.rs:2284-2287` says the worst intonation is
  +29 cents while current provenance establishes approximately +22 cents, and
  the test prose at `:4981-4997` still refers to twenty floats and `_p`/`_f`
  cross-layers instead of forty roots across four takes.
- `tools/ferrosintesis-samples/README.md:9-18` calls itself the full 254-transient
  inventory but omits the mandolin crate and its 40 onsets.
- Generated rustdoc at
  `crates/ferrosintesis-samples-mandolin/src/lib.rs:3-5` points to a nonexistent
  `NOTICE`. `Cargo.toml:10` packages neither a notice nor `LICENSE-CC0`, despite
  the repository asset-package contract requiring each published asset archive
  to carry its own legal text
  (`wrk_docs/2026.07.10 - HLD - ferrosintesis embedded sample crates.md:72-76`,
  `:203-204`).

**Expected.** Public package metadata, generator guidance, consumer test
documentation, inventory, provenance pointers, and packaged legal material all
describe the current one-dynamic/four-round-robin bank.

**Actual.** The 2026-07-24 replacement of the two dynamic layers with four
ordered takes updated the assets and core behavior, but left these package and
maintenance surfaces behind.

The CC0 dedication is explicit in `PROVENANCE.md`; this report does not claim an
external-law or attribution breach. The defect is the repository's own package
contract and the broken/stale published guidance.

## Fix

Update all listed descriptions in one migration sweep, derive the tooling
inventory/count where practical, add and package `LICENSE-CC0`, and make
`gen_crate_lib.py` cite only legal/provenance files the target crate actually
ships.

Add a package-content check that every CC0 asset crate includes its declared
legal-text file, plus a documentation/inventory check derived from the current
sample crates so the next bank cannot leave another retired count behind.

Estimated effort: Small.

## Notes

No asset-name or root-table drift was found. This bug covers documentation and
package contents only; it does not allege that the current WAV payloads are
wrong.

