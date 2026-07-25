# MM-BUG-KILN-00114 — Sample-family provenance rows are not enforced by their claimed oracle

- **State:** Open
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
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-core/`)

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
