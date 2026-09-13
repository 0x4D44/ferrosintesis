# MM-BUG-KILN-00236 — FLAC decoder rejects valid explicit 44.1 kHz frame rates

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis-flac / frame sample-rate parsing
- **Raised:** 2026-08-16T20:59:27Z
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
- **State history:** Open (2026-08-16T20:59:27Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T16:24:43Z, deltic:auto role=fix run=fix-20260913T162023Z-c2fcdbf2 branch=task/bug-MM-BUG-KILN-00236-run-fix-20260913T162023Z-c2fcdbf2 code=e2f93c6526b76f5f2e39e4152453710449c234b0 gate=manual)

## Observation

Observation: frame sample-rate codes 13 and 14 are read and then rejected unconditionally. RFC 9639 allows code 13 to carry 44100 Hz directly and code 14 to carry 4410 tens-of-Hz, so both can represent the crate's advertised 44.1 kHz input shape. Expected: accept those encodings only when their decoded rate equals STREAMINFO and 44100 Hz; reject other values. Concrete fix: decode each explicit representation, normalize to Hz with checked arithmetic, compare it, and add positive 13/14 fixtures plus wrong-value negatives. Source: crates/ferrosintesis-flac/src/lib.rs:499-512; README.md:8-12.

## Fix

<unfixed — raised only>

## Notes
