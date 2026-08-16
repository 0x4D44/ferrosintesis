# MM-BUG-KILN-00234 — FLAC decoder ignores mandatory frame CRCs

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis-flac / frame integrity
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
- **State history:** Open (2026-08-16T20:59:26Z, raised via `deltic bugs new`)

## Observation

Observation: decode_frame reads the header CRC-8 and frame CRC-16 into underscore variables and never validates either. RFC 9639 classifies a frame whose CRC does not validate as invalid. Flipping a checksum byte leaves PCM and STREAMINFO MD5 unchanged, so the decoder returns Ok; when STREAMINFO MD5 is all zero, corrupted audio can also be accepted without any integrity check. Expected: invalid frame checksums return Err. Concrete fix: calculate CRC-8 over the header and CRC-16 over the complete frame, compare before accepting the frame, and add header/footer corruption negatives including a zero-MD5 stream. Source: crates/ferrosintesis-flac/src/lib.rs:453-523 and 374-382.

## Fix

<unfixed — raised only>

## Notes
