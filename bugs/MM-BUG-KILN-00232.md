# MM-BUG-KILN-00232 — FLAC total sample count can abort the decoder with an enormous allocation

- **State:** Open
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
- **State history:** Open (2026-08-16T20:59:04Z, raised via `deltic bugs new`)

## Observation

Observation: A 42-byte FLAC-shaped input can declare STREAMINFO total_samples = 2^36-1. On 64-bit targets, decode_mono16 accepts that count and calls Vec::with_capacity before reading a frame, requesting about 128 GiB and potentially aborting or panicking instead of returning the crate's promised typed Err. The frame-copy loop also pushes before checking the declared total, and MD5 verification allocates a second full PCM copy. Expected: malformed or unsupported-size input fails without infallible allocation. Concrete fix: validate a supported decoded-size/input bound, reserve fallibly, check a frame fits before pushing, and feed MD5 incrementally without a full PCM byte copy. Add a tiny huge-count negative fixture and allocation-failure-safe regression. Source: crates/ferrosintesis-flac/src/lib.rs:334-379; README.md:8-12.

## Fix

<unfixed — raised only>

## Notes
