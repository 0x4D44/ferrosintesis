# MM-BUG-KILN-00233 — Malformed FLAC predictors can overflow decoder arithmetic

- **State:** Open
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
- **State history:** Open (2026-08-16T20:59:25Z, raised via `deltic bugs new`)

## Observation

Observation: decode_fixed and decode_lpc reconstruct samples with unchecked i64 multiplication, addition, and subtraction. The residual decoder also accepts values outside RFC 9639's signed-32-bit residual limit. A small malformed LPC frame can make recurrence values exceed i64: debug builds panic and release builds wrap before the final i16 range check. Expected: every malformed frame returns Err and never panics or produces wrapped PCM. Concrete fix: enforce the residual-value limit and use checked reconstruction arithmetic, rejecting overflow or an out-of-depth reconstructed sample before it can feed the next prediction. Add adversarial FIXED and LPC fixtures that used to panic/wrap. Source: crates/ferrosintesis-flac/src/lib.rs:622-734; README.md:8-12.

## Fix

<unfixed — raised only>

## Notes
