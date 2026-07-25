# MM-BUG-KILN-00114 — Sample-family provenance rows are not enforced by their claimed oracle

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample inventory / provenance oracle
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
- **State history:** Open (2026-07-25, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-core/`) → Fixed (2026-07-25, GPT-5.6 Codex on KILN-Windows — the oracle now parses one counted canonical row per packaged family from each crate's provenance alone)

## Observation

**Symptom.** The packaged provenance states:

> a family that ships without a row here fails the build

at
`D:\worktrees\midi-music\20260725-REV-CLA@KILN-code-review-212250\crates\ferrosintesis-samples-core\PROVENANCE.md:3-5`.
That is the durable guarantee claimed by the closed
`MM-BUG-KILN-00069` remediation.

The source does not enforce it. The inventory oracle:

1. concatenates `README.md`, `PROVENANCE.md`, and `NOTICE` at
   `D:\worktrees\midi-music\20260725-REV-CLA@KILN-code-review-212250\crates\ferrosintesis\src\inventory.rs:196-210`;
2. accepts a family when its bare prefix occurs anywhere in that combined text
   at
   `D:\worktrees\midi-music\20260725-REV-CLA@KILN-code-review-212250\crates\ferrosintesis\src\inventory.rs:212-237`;
3. separately proves only that a `PROVENANCE.md` exists and is named by the
   manifest at
   `D:\worktrees\midi-music\20260725-REV-CLA@KILN-code-review-212250\crates\ferrosintesis\src\inventory.rs:240-280`.

**Expected.** Removing a packaged family's provenance-table row fails the
inventory oracle, and a stale per-family file count is detected.

**Actual.** Removing the `piano_*`, `violin_*`, or `flute_*` row still leaves
the family named in
`D:\worktrees\midi-music\20260725-REV-CLA@KILN-code-review-212250\crates\ferrosintesis-samples-core\README.md:7-9`,
so the combined-document substring predicate remains satisfied. The oracle
also derives only unique prefixes, not per-family counts, so adding another
`piano_*` asset leaves the documented count of 54 untested.

This was confirmed by reading the complete predicate and both packaged
documents. The tracked tree was not mutated and the test was not run; as in
the recent licensing-oracle bugs, the adversarial mutation's result follows
directly from the source predicate.

## Fix

Parse each sample crate's `PROVENANCE.md` independently. Require exactly one
canonical inventory row such as ``| `family_*` |`` for every family derived
from packaged filenames, and compare the row's file count with the derived
count. Add an adversarial fixture that deletes a row while leaving the README
mention and regeneration command intact.

Estimated effort: Small–Medium.

## Notes

All three current core provenance rows and their counts are present. This is a
confirmed oracle/guarantee defect, not a claim that another family is currently
missing.

It is an incomplete-guard residual from closed `MM-BUG-KILN-00069`, but the
transactional review contract forbids modifying tracked files, so this pass
records the residual under a new ID. It is distinct from `MM-BUG-KILN-00110`
(credit-token quality) and `MM-BUG-KILN-00111` (licence self-exemption).

## Resolution — 2026-07-25

The inventory oracle now derives a count for every packaged WAV family and
parses each sample crate's `PROVENANCE.md` independently. It requires exactly
one canonical ``| `family_*` | FILES |`` row per family, rejects rows for
unpackaged families, and compares every documented count with the filesystem.
README and NOTICE text can no longer satisfy the provenance requirement.

All 25 sample crates now carry canonical rows for their 76 packaged families.
Existing stale counts in the MuseScore and orchestral provenance tables were
corrected to match the files those crates package.

## Verification — 2026-07-25

- The focused inventory suite passes all six tests. Its adversarial fixtures
  prove a README family mention cannot replace a provenance row and that wrong
  counts, duplicate rows, and rows for absent families all fail.
- `$null | cargo test --locked -p ferrosintesis`: **720 unit tests and 4 doc
  tests passed; 27 diagnostics ignored**.
- `$null | cargo test --locked -p ferrosintesis --no-default-features`: **619
  unit tests and 4 doc tests passed; 22 diagnostics ignored**.
- Strict all-target clippy passes with all features and with no default
  features. Formatting and `git diff --check` pass.
- No audio render inventory is required: the only changed Rust module is
  `#[cfg(test)]`, and the remaining changes are provenance documentation.
