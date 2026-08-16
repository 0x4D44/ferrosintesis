# MM-BUG-KILN-00208 — Bass family selector fetches the unselected source archive

- **State:** Open
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
- **State history:** Open (2026-08-16T09:39:37Z, raised via `deltic bugs new`)

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

## Notes

Split the two archive ensures or pass the selected family set into the helper.
Retain complete shared-package output validation separately; source fetching follows
selection, while output validation follows package ownership. Add cold-cache
negative controls proving each selector never calls the other archive path.
Estimated effort: Small.

Static review only. No network request, generator, app, build, test, render,
package, or exploratory harness ran.
