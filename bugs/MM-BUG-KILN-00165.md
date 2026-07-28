# MM-BUG-KILN-00165 — Steinway logical aliases duplicate half of packaged and decoded PCM

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** Steinway sample package / memory and package size
- **Raised:** 2026-07-28
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
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

Read-only SHA-256 grouping of crates/ferrosintesis-samples-vcsl-steinway/samples found only 27 unique payloads among 54 files. For each of the nine zones, pp_rr2, mf, and f_rr2 are byte-identical, while mf_rr2 and f are byte-identical. This follows from tools/ferrosintesis-samples/prepare.py:701-709, where six logical dynamic/round-robin cells map to three upstream velocity layers.

Expected: the documented logical aliases preserve their names and musical behavior without storing and decoding duplicate PCM.

Actual: crates/ferrosintesis-samples-vcsl-steinway/src/lib.rs:12-229 embeds all 54 physical WAVs. The 27 redundant files add exactly 3,592,296 packaged bytes. crates/ferrosintesis/src/sampler.rs:1249-1349 constructs six independent decoded banks; prewarm reaches all six at crates/ferrosintesis/src/sampler.rs:3168-3181, retaining approximately 7,182,216 redundant decoded PCM bytes and repeating conversion work. Final release-executable linker deduplication was not measured in this read-only pass and is unverified.

Concrete fix: retain exact logical names through explicit aliases to 27 canonical payloads, share decoded Zone storage between aliased banks, and add a source-derived oracle that permits only declared duplicate aliases. Coordinate the class fix with open MM-BUG-KILN-00162, the Kawai sibling.

Estimated effort: Medium.

## Fix

<unfixed — raised only>

## Notes
