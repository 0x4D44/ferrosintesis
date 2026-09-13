# MM-BUG-KILN-00272 — Steinway FLAC migration dropped half of the legacy WAV lookup keys

- **State:** Closed
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
- **State history:** Open (2026-08-17T08:39:21Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T17:31:07Z, deltic:auto role=fix run=fix-20260913T172137Z-e299aa2e branch=task/bug-MM-BUG-KILN-00272-run-fix-20260913T172137Z-e299aa2e code=8244afb1a90b9eea54500efcce72a67eae2f70a7 gate=manual) -> Closed (2026-09-13T20:22:13Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: all 54 legacy Steinway .wav keys resolve and removing an alias fails the Rust test; its ALIASES rows break the dedup oracle, split to MM-BUG-CRU-00058)

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

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fixes `8244afb1`, `96a8c624`; wording later adjusted by `4951e6ed`) by an agent other than the fixer.

**Original observation re-derived.** All 27 former physical `.wav` keys map to their `.flac` payloads (`ALIASES` 54 rows, `LOGICAL_FILE_COUNT = 81`), and README, PROVENANCE and NOTICE no longer call the payloads WAV. `gen_crate_lib.read_aliases` accepts the new rows.

**Fails-before (method B).** Removing the `steinwayb_C2_pp.wav` alias row fails `tests::former_physical_wav_keys_remain_accepted`. Restored; it and `SteinwayPackagedContractTest` pass on HEAD.

**Residual split to MM-BUG-CRU-00058 (Must).** The 27 appended `ALIASES` rows break the KILN-00165 oracle `SteinwayAliasDeduplicationTest.test_declared_aliases_exactly_cover_repeated_logical_sources`, turning the required Python gate red. Reverting only `ALIASES` to `8244afb1^` turns that class green. The two contracts need reconciling.

## Notes

The current committed bank itself is internally consistent: all 27 FLAC disk
names match the embedded table, all 27 existing alias targets resolve, and the
sampler requests the current FLAC names. This bug is lookup compatibility and
published contract drift, not evidence of payload corruption.
