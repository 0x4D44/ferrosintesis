# MM-BUG-KILN-00235 — FLAC decoder accepts forbidden 16-bit LPC coefficient precision

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis-flac / LPC validation
- **Raised:** 2026-08-16T20:59:26Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T192111Z-6af50691
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00235-run-verify-20260913T192111Z-6af50691
- **Owner base:** c26713ee50f0701718b8ec11c436f43f4c3d0696
- **Owner fingerprint:** sha256:f78de81794ed1dbc6a67d4512b0dd3e0e5869a3efbca0612cedb87ec9c2800af
- **Owner since:** 2026-09-13T19:21:11Z
- **Owner until:** 2026-09-13T21:21:11Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-16T20:59:26Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T16:19:25Z, deltic:auto role=fix run=fix-20260913T161644Z-cd762e67 branch=task/bug-MM-BUG-KILN-00235-run-fix-20260913T161644Z-cd762e67 code=2c585a27c51d4e0181419e9a72994e2f229b1f9a gate=manual)

## Observation

Observation: the four-bit LPC coefficient-precision field is incremented before validation. Forbidden field 0b1111 becomes precision 16, but the guard compares against MAX_LPC_PRECISION + 1 and accepts it. RFC 9639 permits at most 15 and explicitly forbids that bit pattern. Expected: the malformed subframe returns Err. Concrete fix: reject raw field 0b1111 or compare the resulting precision directly with MAX_LPC_PRECISION; add a focused forbidden-pattern regression. Source: crates/ferrosintesis-flac/src/lib.rs:58-62 and 650-663.

## Fix

<unfixed — raised only>

## Notes
