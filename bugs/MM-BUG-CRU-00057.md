# MM-BUG-CRU-00057 — Packaged-document link oracle treats a #fragment as part of the filename, so a valid README anchor link turns cargo test red

- **State:** Closed
- **Priority:** Must
- **Severity:** Medium
- **Area:** ferrosintesis / packaged-document link oracle
- **Raised:** 2026-09-13T19:22:41Z
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
- **State history:** Open (2026-09-13T19:22:41Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T19:48:20Z, deltic:auto role=fix run=fix-20260913T193602Z-fac72892 branch=task/bug-MM-BUG-CRU-00057-run-fix-20260913T193602Z-fac72892 code=9e87c96dc17ec76fec98a77ae665e337b98c602c gate=manual) -> Closed (2026-09-13T20:29:19Z, independent verify by Codex run=verify-20260913T202611Z-75cf2009: fragment links resolve against their path component)

## Observation

Split at independent verification of MM-BUG-KILN-00193 and MM-BUG-KILN-00258 (2026-09-13, trunk 8b6a6f86). inventory::tests::packaged_documents_never_link_outside_their_own_package (crates/ferrosintesis/src/inventory.rs, added by a6abb0c7 for KILN-00193) joins each link target, fragment included, onto the crate directory and checks it exists. Fix 5f4e6083 (KILN-00258) added the valid link README.md#lookup-keys in crates/ferrosintesis-samples-musescore/PROVENANCE.md; README.md:12 has the '## Lookup keys' heading. The oracle reports '1 packaged-document link error(s): ferrosintesis-samples-musescore/PROVENANCE.md links README.md#lookup-keys, which does not exist', failing cargo test -p ferrosintesis under both feature sets. Removing only the fragment turns it green. Expected: strip #fragment before the existence and include checks (optionally verify the anchor heading exists). Actual: a false positive holds the required gate red.

## Fix

`9e87c96dc17ec76fec98a77ae665e337b98c602c` (`fix(MM-BUG-CRU-00057): ignore fragments in packaged links`)
adds `local_link_path`, which excludes empty, anchor-only, and external links, then strips
`#fragment` before checking filesystem existence and Cargo `include` coverage. It keeps the
original target in diagnostics, so a valid `README.md#lookup-keys` link remains meaningful.

### Verification (closure) (2026-09-13, Codex, independent)

Compared the fix with the two same-code heads-up records: `MM-BUG-CRU-00065` scans
`inventory.rs` for a different validation-loop drift, while `MM-BUG-KILN-00190` concerns
the MuseScore provenance regeneration scope. Neither is this fragment-resolution defect.

The original packaged-document oracle and its focused helper both pass:
`cargo test -p ferrosintesis --lib inventory::tests::packaged_documents_never_link_outside_their_own_package`
and `local_link_path_strips_fragments_but_preserves_non_local_links` each passed.

As a negative control, I temporarily restored the pre-fix `Some(target)` behavior. The
packaged-document oracle then reproduced its recorded failure: `PROVENANCE.md` linked
`README.md#lookup-keys`, which it incorrectly reported as missing. Restoring the split made
both tests pass again; `cargo fmt --all -- --check` also passed.

The workspace gate reached 896 passed and 44 ignored, with 3 unrelated failures in the
inventory validation-loop oracle, public sample inventory prose, and the clavinet bank
parser. Clippy retains unrelated errors for two unused clavinet constants and existing
`repeat().take()` and `filter().next_back()` lints; the link oracle itself passes in both
gates.

## Notes
