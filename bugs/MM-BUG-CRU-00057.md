# MM-BUG-CRU-00057 — Packaged-document link oracle treats a #fragment as part of the filename, so a valid README anchor link turns cargo test red

- **State:** Fixed
- **Priority:** Must
- **Severity:** Medium
- **Area:** ferrosintesis / packaged-document link oracle
- **Raised:** 2026-09-13T19:22:41Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T202611Z-75cf2009
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00057-run-verify-20260913T202611Z-75cf2009
- **Owner base:** d676a08827b7486c047f3be22de16d22c5e9dcfe
- **Owner fingerprint:** sha256:2f6da3f1b1e1269e82456d7e6ca9e152084b8b934d5c0337c799a729bb910e6b
- **Owner since:** 2026-09-13T20:26:11Z
- **Owner until:** 2026-09-13T22:26:11Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:22:41Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T19:48:20Z, deltic:auto role=fix run=fix-20260913T193602Z-fac72892 branch=task/bug-MM-BUG-CRU-00057-run-fix-20260913T193602Z-fac72892 code=9e87c96dc17ec76fec98a77ae665e337b98c602c gate=manual)

## Observation

Split at independent verification of MM-BUG-KILN-00193 and MM-BUG-KILN-00258 (2026-09-13, trunk 8b6a6f86). inventory::tests::packaged_documents_never_link_outside_their_own_package (crates/ferrosintesis/src/inventory.rs, added by a6abb0c7 for KILN-00193) joins each link target, fragment included, onto the crate directory and checks it exists. Fix 5f4e6083 (KILN-00258) added the valid link README.md#lookup-keys in crates/ferrosintesis-samples-musescore/PROVENANCE.md; README.md:12 has the '## Lookup keys' heading. The oracle reports '1 packaged-document link error(s): ferrosintesis-samples-musescore/PROVENANCE.md links README.md#lookup-keys, which does not exist', failing cargo test -p ferrosintesis under both feature sets. Removing only the fragment turns it green. Expected: strip #fragment before the existence and include checks (optionally verify the anchor heading exists). Actual: a false positive holds the required gate red.

## Fix

<unfixed — raised only>

## Notes
