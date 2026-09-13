# MM-BUG-KILN-00235 — FLAC decoder accepts forbidden 16-bit LPC coefficient precision

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis-flac / LPC validation
- **Raised:** 2026-08-16T20:59:26Z
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
- **State history:** Open (2026-08-16T20:59:26Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T16:19:25Z, deltic:auto role=fix run=fix-20260913T161644Z-cd762e67 branch=task/bug-MM-BUG-KILN-00235-run-fix-20260913T161644Z-cd762e67 code=2c585a27c51d4e0181419e9a72994e2f229b1f9a gate=manual) -> Closed (2026-09-13T19:25:30Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: forbidden 0b1111 LPC precision rejected; old off-by-one guard decodes it as Ok)

## Observation

Observation: the four-bit LPC coefficient-precision field is incremented before validation. Forbidden field 0b1111 becomes precision 16, but the guard compares against MAX_LPC_PRECISION + 1 and accepts it. RFC 9639 permits at most 15 and explicitly forbids that bit pattern. Expected: the malformed subframe returns Err. Concrete fix: reject raw field 0b1111 or compare the resulting precision directly with MAX_LPC_PRECISION; add a focused forbidden-pattern regression. Source: crates/ferrosintesis-flac/src/lib.rs:58-62 and 650-663.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `2c585a27`) by an agent other than the fixer.

**Original observation re-run.** Raw precision field `0b1111` now returns `Err("FLAC: invalid LPC coefficient precision")`.

**Fails-before (method B).** Restoring `> MAX_LPC_PRECISION + 1` fails `lpc_rejects_the_forbidden_maximum_coefficient_precision` (left `Ok(())`). Restored; `git diff` empty; passes on HEAD.

**Gates.** This fix causes no gate failure; trunk `8b6a6f86` is red for other recorded reasons.

## Notes
