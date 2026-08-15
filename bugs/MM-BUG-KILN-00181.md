# MM-BUG-KILN-00181 — Wrong-shaped archive cache manifests abort sample regeneration

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sample generation / archive cache reliability
- **Raised:** 2026-08-13T17:58:10Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260815T120422Z-p20252-n181203500-c1
- **Owner host:** NMI
- **Owner branch:** task/bug-MM-BUG-KILN-00181-run-fix-20260815T120422Z-p20252-n181203500-c1
- **Owner base:** 117cf0a87796863542cb8cea5ecb5390dff1f2aa
- **Owner fingerprint:** -
- **Owner since:** 2026-08-15T12:04:22Z
- **Owner until:** 2026-08-15T14:04:22Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-13T17:58:10Z, raised via `deltic bugs new`)

## Observation

Source-level reproduction: replace the archive member manifest with syntactically valid JSON null, an array, or a scalar, then invoke the grand-only regeneration path. cached_members_match parses the JSON and immediately calls manifest.get outside its exception handler, so the command raises AttributeError instead of treating the untrusted cache entry as a miss and rebuilding it. A schema-shaped manifest can also point a member at a directory: os.path.exists succeeds and sha256_file raises an uncaught OSError. Expected: every absent, malformed, wrongly typed, unreadable, or non-file cache entry returns False so the pinned archive is rebuilt. Actual: only missing files and JSON syntax failures degrade to a cache miss. Fix by validating that the manifest root and members are dictionaries, requiring each cached member to be a regular readable file, and containing hash/read failures. Add negative regressions for null, array/scalar roots, a non-mapping members field, a directory member, and an unreadable member. Static review only; no generator was run.

## Fix

<unfixed — raised only>

## Notes
