# MM-BUG-KILN-00232 — FLAC total sample count can abort the decoder with an enormous allocation

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis-flac / resource bounds
- **Raised:** 2026-08-16T20:59:04Z
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
- **State history:** Open (2026-08-16T20:59:04Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T05:56:31Z, deltic:auto role=fix run=fix-20260913T054211Z-eb7058c3 branch=task/bug-MM-BUG-KILN-00232-run-fix-20260913T054211Z-eb7058c3 code=4d6ec363e4fd3698acf02aa21afed2bb90417ad gate=manual) -> Closed (2026-09-13T19:25:30Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: 42-byte 2^36-1-sample STREAMINFO rejected before allocation; test fails with MAX_DECODED_SAMPLES removed)

## Observation

Observation: A 42-byte FLAC-shaped input can declare STREAMINFO total_samples = 2^36-1. On 64-bit targets, decode_mono16 accepts that count and calls Vec::with_capacity before reading a frame, requesting about 128 GiB and potentially aborting or panicking instead of returning the crate's promised typed Err. The frame-copy loop also pushes before checking the declared total, and MD5 verification allocates a second full PCM copy. Expected: malformed or unsupported-size input fails without infallible allocation. Concrete fix: validate a supported decoded-size/input bound, reserve fallibly, check a frame fits before pushing, and feed MD5 incrementally without a full PCM byte copy. Add a tiny huge-count negative fixture and allocation-failure-safe regression. Source: crates/ferrosintesis-flac/src/lib.rs:334-379; README.md:8-12.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `4d6ec363`) by an agent other than the fixer.

**Original observation re-run.** The regression is the exact repro: a 42-byte STREAMINFO-only input declaring 2^36-1 samples now returns `Err("FLAC: decoded sample count exceeds supported limit")` with no allocation attempt.

**Fails-before (method B).** Removing the `MAX_DECODED_SAMPLES` bound fails `an_enormous_declared_length_is_rejected_before_allocation` (it reaches "stream ended before the declared sample count" instead). Restored; `git diff` empty; all 15 `ferrosintesis-flac` tests pass.

Reservation is fallible, a fit check precedes each append, and MD5 is hashed incrementally, so no second PCM copy is built. The reordered fit-before-push check has no dedicated test.

## Notes
