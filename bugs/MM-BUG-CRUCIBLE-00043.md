# MM-BUG-CRUCIBLE-00043 — Packaged licence-evidence copies are bound to no oracle, so the published legal evidence can silently diverge from its attested SHA-256

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** sample asset crates / provenance oracles
- **Raised:** 2026-08-18T06:59:48Z
- **Discovery source:** Agent
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
- **State history:** Open (2026-08-18T06:59:48Z, raised via `deltic bugs new` model=claude-fable-5)

## Observation

Static inspection (code-review pass over `crates/ferrosintesis-samples-ccby/`). The
MM-BUG-KILN-00193 fix (`a6abb0c`, 2026-08-15) copied the retained Freesound licence
manifests into the published packages so the cited evidence travels with the crate:

- `crates/ferrosintesis-samples-ccby/licence-evidence/_readme_and_license_3957.txt`
- `crates/ferrosintesis-samples-ccby/licence-evidence/_readme_and_license_19445.txt`
- `crates/ferrosintesis-samples-orchestral2/licence-evidence/_readme_and_license_44539.txt`

No oracle reads any of these copies. The guards each cover something else:

- `crates/ferrosintesis/src/provenance.rs` (`every_committed_source_is_pinned_by_a_packaged_document`,
  `the_retained_freesound_licence_manifests_are_present`) hashes and asserts only the
  `tools/ferrosintesis-samples/freesound-src/` originals.
- `crates/ferrosintesis/src/inventory.rs` (`packaged_documents_never_link_outside_their_own_package`)
  checks only that the crate-local link target exists and is named by `include`.
- `crates/ferrosintesis/src/licensing.rs` never opens the evidence files.

So the copy each PROVENANCE.md actually links beside its recorded SHA-256
(`crates/ferrosintesis-samples-ccby/PROVENANCE.md:39-40`,
`crates/ferrosintesis-samples-orchestral2/PROVENANCE.md:71`) is a hand-maintained
duplicate with no binding to the attested bytes. Repro: change one byte (or the licence
lines) in a crate-local `licence-evidence/*.txt`; `cargo test --workspace` stays green,
and the next publish ships evidence that no longer matches the SHA-256 printed beside
it — the exact failure KILN-00193 was raised to close, reintroduced one copy away. A
future pack's evidence copy also lands unguarded by construction. Today the copies are
byte-identical to the originals (verified: both pairs share git blob IDs, and the
committed blobs hash to the recorded `5b6e87bc…` / `5de6b40b…`), so this is a missing
guard, not present drift — the same class as MM-BUG-KILN-00071/00073.

Expected: packaged licence evidence is bound to the attested hashes the same way the
`freesound-src/` originals are. Concrete fix: extend the provenance oracle to hash every
`crates/ferrosintesis-samples-*/licence-evidence/*` file and require that hash to appear
in the same crate's packaged PROVENANCE.md (equivalently: assert byte-identity with the
`freesound-src/` original where one exists), enumerated from the filesystem so a new
evidence file cannot land outside the sweep — plus the adversarial self-test proving a
mutated copy turns it red.

## Fix

<unfixed — raised only>

## Notes
