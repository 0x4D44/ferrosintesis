# MM-BUG-KILN-00234 — FLAC decoder ignores mandatory frame CRCs

- **State:** Closed
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
- **State history:** Open (2026-08-16T20:59:26Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T06:23:07Z, deltic:auto role=fix run=fix-20260913T060531Z-212caf5b branch=task/bug-MM-BUG-KILN-00234-run-fix-20260913T060531Z-212caf5b code=971ec0cf64c7769508fd7a446778bebb69887a7f gate=manual) -> Closed (2026-09-13T19:25:30Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: corrupted frames with no STREAMINFO MD5 now rejected; test accepts the damaged stream with CRC comparisons disabled)

## Observation

Observation: decode_frame reads the header CRC-8 and frame CRC-16 into underscore variables and never validates either. RFC 9639 classifies a frame whose CRC does not validate as invalid. Flipping a checksum byte leaves PCM and STREAMINFO MD5 unchanged, so the decoder returns Ok; when STREAMINFO MD5 is all zero, corrupted audio can also be accepted without any integrity check. Expected: invalid frame checksums return Err. Concrete fix: calculate CRC-8 over the header and CRC-16 over the complete frame, compare before accepting the frame, and add header/footer corruption negatives including a zero-MD5 stream. Source: crates/ferrosintesis-flac/src/lib.rs:453-523 and 374-382.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `971ec0cf`) by an agent other than the fixer.

**Original observation re-run.** A one-sample zero-MD5 stream decodes to `Ok([0])`; flipping a header byte, the CRC-8, a frame byte or the CRC-16 now returns the matching CRC mismatch error. The real embedded FLAC banks still decode under the check.

**Fails-before (method B).** Disabling both CRC comparisons fails `frame_crc_corruption_is_rejected_without_a_streaminfo_md5` (left `Ok([0])`, right the CRC-8 mismatch error). Restored; `git diff` empty; passes on HEAD.

**Gates.** This fix causes no gate failure; trunk `8b6a6f86` is red for other recorded reasons.

## Notes
