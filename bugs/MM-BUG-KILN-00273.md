# MM-BUG-KILN-00273 — Steinway regeneration command leaves the embedded FLAC bank stale

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** Steinway sample crate / deterministic regeneration
- **Raised:** 2026-08-17T08:39:27Z
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
- **State history:** Open (2026-08-17T08:39:27Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T17:44:12Z, deltic:auto role=fix run=fix-20260913T173029Z-61dd10a6 branch=task/bug-MM-BUG-KILN-00273-run-fix-20260913T173029Z-61dd10a6 code=cd258ca69b488cccb9a077452d399e7bca07939f gate=manual) -> Closed (2026-09-13T20:44:18Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: --only=steinwayb replaces 27 FLACs with no WAVs; WAV-copying publisher reddens the scoped test)

## Observation

The crate documents
`python3 tools/ferrosintesis-samples/prepare.py --only=steinwayb` as its scoped
regeneration command at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-091226\crates\ferrosintesis-samples-vcsl-steinway\README.md:15`
and `PROVENANCE.md:60-67`. The active package embeds 27 FLAC files at
`src/lib.rs:15-124`, and the runtime sampler requests those FLAC names at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-091226\crates\ferrosintesis\src\sampler.rs:1277-1349`.

The documented recipe still owns `.wav` output names at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-091226\tools\ferrosintesis-samples\prepare.py:720-729`
and writes them through `write_wav_mono` at `prepare.py:5733-5779`. Its preflight
at `prepare.py:5402-5429` scans only WAV names, so it does not reject or replace
the existing FLAC half.

Following the documented command therefore adds 27 WAVs beside the unchanged 27
FLACs. Runtime continues to consume the stale FLAC payloads, while
`inventory_matches_packaged_samples` at
`crates\ferrosintesis-samples-vcsl-steinway\src\lib.rs:179-193` sees 54 files
against `FILE_COUNT = 27` and fails. The source-derived alias oracle at
`tools\ferrosintesis-samples\test_prepare.py:3394-3411` also still compares WAV
source names with the now-FLAC alias targets. Expected: the scoped command
replaces and verifies the exact final-format bank used by runtime. Actual: it
produces unconsumed assets and leaves the shipped bank stale. Static review only;
the command and tests were not run.

## Fix

<unfixed — raised only. Generate all 27 canonical FLACs in empty staging,
verify the exact inventory and decoded PCM there, reject mixed same-stem
containers, then publish the complete bank atomically and refresh the alias and
Rust tables. Add a negative control starting from the current FLAC-only tree.>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (test `cd258ca6`; root cause `55298fb1` + `dc135609`) by an agent other than the fixer.

`SteinwayGenericScopedPublicationTest` drives `main` with `--only=steinwayb` over the 27 physical sources; only the 27 FLACs remain, each replaced.

**Fails-before (method B).** Making the shared publisher copy WAVs fails the published-set assertion. Restored; it, `SteinwayOutputInventoryTest` and `SteinwayPackagedContractTest` pass on HEAD.

The red `SteinwayAliasDeduplicationTest` is not caused by this fix: it comes from `8244afb1`'s legacy alias rows (KILN-00272), proven by restoring the older `ALIASES`; tracked as MM-BUG-CRU-00058.

## Notes

Open `MM-BUG-KILN-00241` covers the shared Rust generator's syntax failure; it
does not correct this Steinway-specific WAV/FLAC workflow. A separate
failure-atomicity record was not raised because complete-bank staging is already
part of this defect's concrete fix surface.
