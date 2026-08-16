# MM-REQ-KILN-00204 — Share drum-kit PCM runtime across split asset crates

- **State:** Draft
- **Priority:** Could
- **Area:** sample assets / split drum-kit runtime
- **Raised:** 2026-08-16T07:17:08Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-16T07:17:08Z, raised via `deltic reqs new`)

## Statement

The split drum-kit crates must share the generic lookup, cache, prewarm, diagnostics, and RIFF-decoder implementation while retaining crate-local inventories and independent caches.

## Notes

`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-075555\crates\ferrosintesis-samples-drumkit2\src\lib.rs:218`
through line 286 duplicates exact-name lookup, indexed lookup, prewarming, cache
diagnostics, cache initialization, and RIFF decoding from
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-075555\crates\ferrosintesis-samples-drumkit\src\lib.rs:743`
through line 819.

The drift risk has already materialized: commit `233d591` fixed the cold-cache
miss ordering in the companion crate, while the core crate retained the old
ordering until `44fcdf3`. The shared implementation should preserve independent
per-crate `OnceLock` caches, inventories, and public bank descriptors; this
requirement is about sharing the generic runtime logic, not merging the package
payloads or changing rendered audio.

A suitable Gate-1 oracle should prevent a lookup/cache/decoder fix from landing
in only one half and should pin unchanged public behavior for valid lookups,
misses, prewarming, and cache initialization. The implementation may use a shared
internal helper or a generated common section; avoid a public API expansion unless
the chosen design requires one.

This does not duplicate Draft `MM-REQ-KILN-00176` (bank descriptors),
`MM-REQ-KILN-00144` (published source pins), `MM-REQ-KILN-00155` (package
ownership), or `MM-REQ-CRUCIBLE-00007` (application-level drum routing metadata).
Proposed priority: Could. Proposed flow: heavy. Estimated effort: Medium.
