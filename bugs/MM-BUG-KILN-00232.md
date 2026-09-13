# MM-BUG-KILN-00232 — FLAC total sample count can abort the decoder with an enormous allocation

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis-flac / resource bounds
- **Raised:** 2026-08-16T20:59:04Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T191914Z-a6909962
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00232-run-verify-20260913T191914Z-a6909962
- **Owner base:** 15b480ab543f48432736c1a349c0de467b9c45ec
- **Owner fingerprint:** sha256:db167b11e76c2d375906f4f61d4c5a06c22584e2fa57a9688636656f1c08c95f
- **Owner since:** 2026-09-13T19:19:14Z
- **Owner until:** 2026-09-13T21:19:14Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-16T20:59:04Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T05:56:31Z, deltic:auto role=fix run=fix-20260913T054211Z-eb7058c3 branch=task/bug-MM-BUG-KILN-00232-run-fix-20260913T054211Z-eb7058c3 code=4d6ec363e4fd3698acf02aa21afed2bb90417ad gate=manual)

## Observation

Observation: A 42-byte FLAC-shaped input can declare STREAMINFO total_samples = 2^36-1. On 64-bit targets, decode_mono16 accepts that count and calls Vec::with_capacity before reading a frame, requesting about 128 GiB and potentially aborting or panicking instead of returning the crate's promised typed Err. The frame-copy loop also pushes before checking the declared total, and MD5 verification allocates a second full PCM copy. Expected: malformed or unsupported-size input fails without infallible allocation. Concrete fix: validate a supported decoded-size/input bound, reserve fallibly, check a frame fits before pushing, and feed MD5 incrementally without a full PCM byte copy. Add a tiny huge-count negative fixture and allocation-failure-safe regression. Source: crates/ferrosintesis-flac/src/lib.rs:334-379; README.md:8-12.

## Fix

<unfixed — raised only>

## Notes
