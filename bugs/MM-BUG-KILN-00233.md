# MM-BUG-KILN-00233 — Malformed FLAC predictors can overflow decoder arithmetic

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis-flac / malformed predictor handling
- **Raised:** 2026-08-16T20:59:25Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T191948Z-e985ce1e
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00233-run-verify-20260913T191948Z-e985ce1e
- **Owner base:** 3768fdedb8f81d03581ef6d2722a99ef3a6a714e
- **Owner fingerprint:** sha256:ed0ba1bbfab48207f487f6c49d08768a8693ce23ade2793fb18bbe83ccba2698
- **Owner since:** 2026-09-13T19:19:48Z
- **Owner until:** 2026-09-13T21:19:48Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-16T20:59:25Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T06:04:35Z, deltic:auto role=fix run=fix-20260913T054417Z-112a7e87 branch=task/bug-MM-BUG-KILN-00233-run-fix-20260913T054417Z-112a7e87 code=52d6bcb685d795d3fd8e3e3c31102ebbcf47458b gate=manual)

## Observation

Observation: decode_fixed and decode_lpc reconstruct samples with unchecked i64 multiplication, addition, and subtraction. The residual decoder also accepts values outside RFC 9639's signed-32-bit residual limit. A small malformed LPC frame can make recurrence values exceed i64: debug builds panic and release builds wrap before the final i16 range check. Expected: every malformed frame returns Err and never panics or produces wrapped PCM. Concrete fix: enforce the residual-value limit and use checked reconstruction arithmetic, rejecting overflow or an out-of-depth reconstructed sample before it can feed the next prediction. Add adversarial FIXED and LPC fixtures that used to panic/wrap. Source: crates/ferrosintesis-flac/src/lib.rs:622-734; README.md:8-12.

## Fix

<unfixed — raised only>

## Notes
