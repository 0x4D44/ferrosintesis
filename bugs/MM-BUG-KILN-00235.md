# MM-BUG-KILN-00235 — FLAC decoder accepts forbidden 16-bit LPC coefficient precision

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis-flac / LPC validation
- **Raised:** 2026-08-16T20:59:26Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260913T161644Z-cd762e67
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00235-run-fix-20260913T161644Z-cd762e67
- **Owner base:** 43b6f008eb9decf34a39ae97dd09649b35eda283
- **Owner fingerprint:** -
- **Owner since:** 2026-09-13T16:16:44Z
- **Owner until:** 2026-09-13T18:16:44Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-16T20:59:26Z, raised via `deltic bugs new`)

## Observation

Observation: the four-bit LPC coefficient-precision field is incremented before validation. Forbidden field 0b1111 becomes precision 16, but the guard compares against MAX_LPC_PRECISION + 1 and accepts it. RFC 9639 permits at most 15 and explicitly forbids that bit pattern. Expected: the malformed subframe returns Err. Concrete fix: reject raw field 0b1111 or compare the resulting precision directly with MAX_LPC_PRECISION; add a focused forbidden-pattern regression. Source: crates/ferrosintesis-flac/src/lib.rs:58-62 and 650-663.

## Fix

<unfixed — raised only>

## Notes
