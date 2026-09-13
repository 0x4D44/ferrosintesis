# MM-BUG-KILN-00208 — Bass family selector fetches the unselected source archive

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** electric-bass sample generation / selective fetch
- **Raised:** 2026-08-16T09:39:37Z
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
- **State history:** Open (2026-08-16T09:39:37Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:22:45Z, deltic:auto role=fix run=fix-20260913T151318Z-eb397982 branch=task/bug-MM-BUG-KILN-00208-run-fix-20260913T151318Z-eb397982 code=c8e00f53bb76609292179743f7d2a5f4aad20755 gate=manual) -> Closed (2026-09-13T21:00:07Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: cold-cache fingerbass and pickbass selections each fetch only their own archive; unconditional fetch fails both)

## Observation

The `--only` contract says a selected family leaves every other tracked WAV
untouched and skips its fetches (`tools/ferrosintesis-samples/prepare.py:5507-5510`).
Yet selecting either bass family enters the shared branch at `prepare.py:5607-5608`,
and `ensure_ebass_sources()` unconditionally authenticates/extracts both the finger
and pick archives at `prepare.py:1568-1573`.

Expected: `--only=fingerbass` depends only on the finger archive, and
`--only=pickbass` only on the pick archive. Actual: a cold, unavailable, or corrupt
unselected archive can block the selected bake; a healthy run also performs
avoidable cache verification and extraction work.

## Fix

Unfixed. Raised for the fix-open-bugs loop; this review did not change code.

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `c8e00f53`) by an agent other than the fixer.

Cold-cache `main()` with `--only=fingerbass` or `--only=pickbass` fetches only that family's pinned archive; an unfiltered bake still fetches both.

**Fails-before (method B).** Making `ensure_ebass_sources` fetch both unconditionally fails the two cold-cache regressions ("fingerbass selection fetched pickbass archive" and the reverse). Restored; all three `BassWholeBankPublicationTest` regressions pass on HEAD.

**Gates.** Causes no gate failure; trunk `8b6a6f86` is red for other recorded reasons.

## Notes

Split the two archive ensures or pass the selected family set into the helper.
Retain complete shared-package output validation separately; source fetching follows
selection, while output validation follows package ownership. Add cold-cache
negative controls proving each selector never calls the other archive path.
Estimated effort: Small.

Static review only. No network request, generator, app, build, test, render,
package, or exploratory harness ran.
