# MM-BUG-KILN-00272 — Steinway FLAC migration dropped half of the legacy WAV lookup keys

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** Steinway sample crate / public lookup compatibility
- **Raised:** 2026-08-17T08:39:21Z
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
- **State history:** Open (2026-08-17T08:39:21Z, raised via `deltic bugs new`)

## Observation

Before the FLAC migration, the crate accepted all 54 Steinway musical sample
names as `.wav` keys. The migration changed the 27 physical entries to `.flac`
at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-091226\crates\ferrosintesis-samples-vcsl-steinway\src\lib.rs:15-124`,
but retained aliases only for the other 27 `mf`, `f`, and `f_rr2` WAV names at
`src/lib.rs:126-154`. `get()` performs exact alias substitution followed by an
exact physical-name lookup at `src/lib.rs:156-166`.

Consequently, a previously valid call such as
`get("steinwayb_C2_pp.wav")` now returns `None`; the replacement
`get("steinwayb_C2_pp.flac")` succeeds. A static comparison with the parent of
migration commit `9046cd1` found 27 removed `.wav` keys and 27 added `.flac`
keys. The in-repo sampler was retargeted to FLAC and still works, but standalone
callers lost half of the package's former 54-name lookup surface.

The published contract remains stale: `README.md:8-15`,
`PROVENANCE.md:9-15,51-67`, and `NOTICE:4-11` still describe the embedded
payloads as WAVs and imply a 54-name WAV bank. Expected: the FLAC migration
preserves the complete legacy WAV lookup surface and accurately documents the
physical container. Actual: only 27 legacy WAV aliases survive and package
auditors receive the retired container description. Static review only; no app,
test, package, decoder, generator, render, or exploratory harness ran.

## Fix

<unfixed — raised only. Add compatibility aliases for the 27 former physical
WAV keys, keep the canonical FLAC entries, update the accepted-name count and
published format contract, and add a source-derived regression that enumerates
all pre-migration logical WAV names.>

## Notes

The current committed bank itself is internally consistent: all 27 FLAC disk
names match the embedded table, all 27 existing alias targets resolve, and the
sampler requests the current FLAC names. This bug is lookup compatibility and
published contract drift, not evidence of payload corruption.
