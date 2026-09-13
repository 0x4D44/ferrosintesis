# MM-BUG-KILN-00239 — Gong regeneration command leaves the embedded FLAC bank stale

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** gong sample crate / deterministic regeneration
- **Raised:** 2026-08-16T21:53:11Z
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
- **State history:** Open (2026-08-16T21:53:11Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T06:34:33Z, deltic:auto role=fix run=fix-20260913T062419Z-07b08de2 branch=task/bug-MM-BUG-KILN-00239-run-fix-20260913T062419Z-07b08de2 code=c91028c3285522b6643a786671cc0a1ad471925a gate=manual) -> Closed (2026-09-13T20:22:13Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: --local-only replaces the FLAC gong bank with no WAVs; skipping the pending publish reddens the workflow test; direct writer split to MM-BUG-CRU-00070)

## Observation

Observation: README.md:15-18 and PROVENANCE.md:130-140 publish python3 tools/ferrosintesis-samples/prepare.py --local-only as the complete gong regeneration command. That path selects LOCAL_SOURCES whose output names are .wav at tools/ferrosintesis-samples/prepare.py:1091-1098 and writes them with write_wav_mono at :5444-5462. The crate instead embeds only .flac at crates/ferrosintesis-samples-gong/src/lib.rs:12-20. Following the documented command therefore creates two extra WAVs while leaving both shipped FLAC payloads unchanged; the crate inventory test then sees four bank files against FILE_COUNT=2, and Cargo.toml:10 would package both container sets. The separate tools/ferrosintesis-samples/to_flac.py conversion is not named by either regeneration document and describes itself as a one-time bake. Expected: the documented regeneration workflow atomically refreshes the exact packaged FLAC assets and leaves a testable clean two-file inventory. Concrete fix: integrate verified FLAC emission/conversion into the selected gong recipe or publish and test a complete two-step workflow; refresh provenance sizes/names; add a negative regression that starts from the committed FLAC-only bank, runs the workflow in an isolated tree, and proves both embedded payloads were replaced with no duplicate WAVs. Static review only; the command was not run under this pass contract.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (test `c91028c3`; root cause `55298fb1`, `_finish` calls `publish_pending_banks`) by an agent other than the fixer.

**Original observation re-run.** `prepare.py --local-only` through `main()` on an isolated FLAC-only gong bank replaces exactly the two FLACs and leaves no WAVs.

**Fails-before (method B).** Making `_finish` skip the pending-bank publish fails `GongRegenerationWorkflowTest.test_local_only_replaces_the_committed_flac_bank_without_wav_duplicates`, listing the leftover `gong_ageng_*.wav`. Restored; passes on HEAD.

**Residual split to MM-BUG-CRU-00070.** Gong still writes WAVs straight into the live crate and converts per file, so an interrupted run can leave a mixed bank (found by reading the code).

## Notes
