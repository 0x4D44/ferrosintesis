# MM-BUG-KILN-00089 — The mandolin package still describes the retired two-dynamic bank and omits its legal text

- **State:** Closed
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-mandolin/`) → Fixed (2026-07-26, GPT-5.6 Codex on KILN-Windows — aligned the mandolin package with its shipped bank and made every CC0 sample crate carry legal text) → Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: GPT-5.6 Codex on KILN-Windows), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree at b0b93d9: `cargo fmt --all --check`, `clippy --workspace --exclude amp-lab --all-targets -D warnings`, `clippy -p ferrosintesis --no-default-features --all-targets -D warnings`, `test -p ferrosintesis --no-default-features --locked` (628 passed) and `test --workspace --exclude amp-lab --locked` (731 passed) - 1461 tests, 0 failures. Original observation re-run at source and by packaging. The mandolin README now reads "one dynamic with four ordered round robins per zone"; a repo-wide grep for the stale strings the bug lists - "two dynamic layers", "+29 cents", "254-transient" - returns nothing under `crates/` or `tools/`. `cargo package --list --allow-dirty -p ferrosintesis-samples-mandolin` includes `LICENSE-CC0`, `PROVENANCE.md` and `README.md`, so the rustdoc pointer is no longer dangling and the asset-package contract is met. I audited the legal-text claim rather than trusting the count: `every_cc0_sample_crate_ships_its_legal_text` derives the CC0 set from each manifest's `license` field (not a grep), requires the file to exist AND to appear in `include`, and carries a `checked > 10` non-vacuity floor. All 16 crates declaring `license = "CC0-1.0"` ship `LICENSE-CC0`; the nine without it declare MIT or CC-BY, where it would be wrong. My own first pass grepped for "CC0" in PROVENANCE and over-matched at 24 crates - the manifest-derived predicate is the correct one. All 8 inventory tests green.)

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

## Resolution — 2026-07-26

The mandolin README, generated crate documentation, preparation recipe, sampler
comments, and test prose now describe the shipped one-dynamic, four-round-robin
bank and its measured approximately +22-cent worst detuning. The tool README no
longer freezes a repository-wide transient total; it points to the existing
derived crate inventory and now documents the mandolin package explicitly.

All 15 CC0 sample crates now carry their own `LICENSE-CC0`, and every affected
package manifest includes it. `gen_crate_lib.py` derives its documentation links
from legal and provenance files that the target manifest actually packages.
The filesystem-derived inventory oracle checks both legal-text presence and
package inclusion across every CC0 sample crate, with a negative regression for
missing and unpackaged text.

## Verification — 2026-07-26

- The focused inventory suite passed all 8 tests, including both legal-text
  regressions; the focused mandolin root-table test and both mandolin sample
  crate tests passed.
- The preparation tool's 33 Python unit tests passed. Both Python generators
  compile, and stale two-dynamic, +29-cent, twenty-float, `_p`/`_f`, and global
  transient-count descriptions are absent.
- `cargo package --list --allow-dirty -p ferrosintesis-samples-mandolin`
  includes `LICENSE-CC0`, `PROVENANCE.md`, and `README.md`.
- The complete default suite passed (730 tests, 27 ignored), the true
  model-only suite passed (628 tests, 22 ignored), and both doc-test sets passed
  (4 each).
- Strict workspace clippy and true model-only clippy passed with warnings
  denied; formatting and `git diff --check` passed.
- Fresh release binaries from exact baseline `a083682`, full 124-MIDI inventory
  at 11.025 kHz: all 124 stayed byte-identical, with zero contamination and
  zero missed paths.

## Notes

No asset-name or root-table drift was found. This bug covers documentation and
package contents only; it does not allege that the current WAV payloads are
wrong.

