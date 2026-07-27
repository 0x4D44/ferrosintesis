# MM-BUG-KILN-00154 — Orchestral2 public inventory omits most shipped families

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** orchestral2 / published metadata
- **Raised:** 2026-07-27
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
- **Held branch:** host-local:KILN:task/bug-MM-BUG-KILN-00154-run-fix-20260727T092502Z-p9812-n774387000-c66-code-1785144930278
- **Legacy fixed run:** -
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=gpt-5.6-sol@high) → Fixed (2026-07-27, deltic:auto role=fix run=fix-20260727T092502Z-p9812-n774387000-c66 branch=task/bug-MM-BUG-KILN-00154-run-fix-20260727T092502Z-p9812-n774387000-c66 code=75895ae12ee3 gate=cargo model=codex@xhigh)

## Observation

**Symptom.** The published crate front door presents five families as its
“Contents & provenance” inventory, but the package ships 14.

`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\crates\ferrosintesis-samples-orchestral2\README.md:13`
lists harp, timpani, recorder, ocarina, and banjo: 50 WAVs. The complete packaged
inventory at
`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\crates\ferrosintesis-samples-orchestral2\PROVENANCE.md:12`
contains 14 families and 132 WAVs. The omitted nine families are `eastpick`,
`eastpluck`, `glock`, `marimba`, `musicbox`, `tubular`, `vibes`, `viola`, and
`xylo`: 82 shipped assets.

`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\crates\ferrosintesis-samples-orchestral2\Cargo.toml:6`
repeats the same stale five-family description. Crate rustdoc at
`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\crates\ferrosintesis-samples-orchestral2\src\lib.rs:8`
directs provenance readers to the incomplete README and repository tooling
instead of the complete packaged `PROVENANCE.md`.

**Expected.** Exhaustive-looking published inventory surfaces match the package,
or state that they are examples and link the packaged authority.

**Actual.** crates.io consumers and auditors receive a false primary inventory
that omits 62% of the audio.

**Concrete fix.** Make `PROVENANCE.md` the named canonical public inventory,
update or remove the hand-maintained family list in the Cargo description, and
either derive the README table or label a short list as non-exhaustive. Extend
the inventory oracle to guard every surface that claims exhaustiveness.

## Fix

The crate now names packaged `PROVENANCE.md` as the canonical public inventory.
Its README delegates the complete family/count/source/licence table there, its
manifest description no longer embeds a partial family list, and its crate-level
documentation points provenance readers to the same packaged authority.

The shared inventory oracle now checks every sample crate. A README family table
must match the packaged WAV families exactly, or a contents section must delegate
to `PROVENANCE.md`. Manifest descriptions cannot present a substantial partial
family list, and crate docs cannot direct provenance readers only to unpackaged
repository material.

### Fix summary (2026-07-27, deltic:auto run=fix-20260727T092502Z-p9812-n774387000-c66 code=75895ae12ee3 gate=cargo)

Root cause: the complete packaged `PROVENANCE.md` inventory was already derived
and checked, but README, manifest, and rustdoc prose lived outside that oracle.
When orchestral2 grew from five to 14 families, those hand-maintained surfaces
drifted while still looking exhaustive.

Changed:
- `crates/ferrosintesis/src/inventory.rs`: added a derived public-inventory
  surface oracle plus fail/pass unit cases.
- `crates/ferrosintesis-samples-orchestral2/README.md`: replaced the stale
  five-family table with a canonical packaged-provenance delegation.
- `crates/ferrosintesis-samples-orchestral2/Cargo.toml`: removed the partial
  family list from the package description.
- `crates/ferrosintesis-samples-orchestral2/src/lib.rs`: pointed crate docs at
  packaged `PROVENANCE.md`.

Tests:
- The held pass observed the new public-surface regression fail against the stale
  orchestral2 metadata before applying the fix.
- `cargo test -p ferrosintesis inventory::tests -- --nocapture`: 17 passed.
- `cargo test -p ferrosintesis --no-default-features inventory::tests -- --nocapture`:
  17 passed.
- `cargo clippy -p ferrosintesis --all-targets -- -D warnings`: passed.
- `cargo clippy -p ferrosintesis --all-targets --no-default-features -- -D warnings`:
  passed.
- `cargo fmt -p ferrosintesis -- --check` and `git diff --check`: passed.
- No render comparison was required because the change affects published
  metadata and test-only inventory validation, not audio behavior.

## Notes

Current packaging, family counts, and licences are correct. This is the public
metadata residual left after MM-BUG-KILN-00069 added the complete packaged
provenance table.
