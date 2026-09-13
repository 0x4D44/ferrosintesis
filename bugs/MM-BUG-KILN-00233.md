# MM-BUG-KILN-00233 — Malformed FLAC predictors can overflow decoder arithmetic

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis-flac / malformed predictor handling
- **Raised:** 2026-08-16T20:59:25Z
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
- **State history:** Open (2026-08-16T20:59:25Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T06:04:35Z, deltic:auto role=fix run=fix-20260913T054417Z-112a7e87 branch=task/bug-MM-BUG-KILN-00233-run-fix-20260913T054417Z-112a7e87 code=52d6bcb685d795d3fd8e3e3c31102ebbcf47458b gate=manual) -> Closed (2026-09-13T19:25:30Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: FIXED and LPC overflow fixtures panic and zigzag accepts 2^31 with unchecked arithmetic restored)

## Observation

Observation: decode_fixed and decode_lpc reconstruct samples with unchecked i64 multiplication, addition, and subtraction. The residual decoder also accepts values outside RFC 9639's signed-32-bit residual limit. A small malformed LPC frame can make recurrence values exceed i64: debug builds panic and release builds wrap before the final i16 range check. Expected: every malformed frame returns Err and never panics or produces wrapped PCM. Concrete fix: enforce the residual-value limit and use checked reconstruction arithmetic, rejecting overflow or an out-of-depth reconstructed sample before it can feed the next prediction. Add adversarial FIXED and LPC fixtures that used to panic/wrap. Source: crates/ferrosintesis-flac/src/lib.rs:622-734; README.md:8-12.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `52d6bcb6`) by an agent other than the fixer.

**Original observation re-run.** The FIXED order-4 and LPC fixtures reproduce the overflow; on HEAD both return `Err("FLAC: reconstructed sample exceeds subframe bit depth")` without panicking.

**Fails-before (method B).** Restoring unchecked predictor arithmetic and removing the residual bound fails all three regressions: FIXED and LPC panic on i64 overflow, and zigzag returns `Ok(2147483648)`. Restored; `git diff` empty; all pass on HEAD.

**Gates.** This fix causes no gate failure; trunk `8b6a6f86` is red for other recorded reasons.

## Notes
