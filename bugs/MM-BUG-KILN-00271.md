# MM-BUG-KILN-00271 — Strings regeneration command leaves the embedded FLAC bank stale

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** strings sample crate / deterministic regeneration
- **Raised:** 2026-08-17T07:29:12Z
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
- **State history:** Open (2026-08-17T07:29:12Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T17:29:02Z, deltic:auto role=fix run=fix-20260913T171722Z-c6965ed4 branch=task/bug-MM-BUG-KILN-00271-run-fix-20260913T171722Z-c6965ed4 code=711e6a5a22170ff23bd3a5df09ea37464ff91539 gate=manual) -> Closed (2026-09-13T20:44:18Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: strings selector replaces all 40 FLACs with no WAVs; WAV-copying publisher reddens the scoped test)

## Observation

The package documents python3 tools/ferrosintesis-samples/prepare.py --only=cellosolo,dbass,pizzbass as its regeneration command at crates/ferrosintesis-samples-strings/README.md:26-27 and PROVENANCE.md:7. Those source tables still own .wav output names at tools/ferrosintesis-samples/prepare.py:354-358, :372-379, and :479-485; the generic path selects them at :5576-5584 and writes WAV files at :5733-5779. The active package instead embeds only 40 .flac files at crates/ferrosintesis-samples-strings/src/lib.rs:23-180, and runtime consumes .flac keys at crates/ferrosintesis/src/sampler.rs:898-961 and :1087-1127. The stale-output validator at prepare.py:5402-5429 scans only .wav names. Following the documented command on the current FLAC-only tree therefore leaves all runtime payloads unchanged, adds 40 unconsumed WAVs, and makes the inventory test at src/lib.rs:204-231 see 80 sample files against 40 embedded entries. Expected: the documented scoped workflow replaces and verifies the exact final-format bank runtime consumes, with no duplicate container set. Concrete fix: generate into empty staging, encode and independently verify the canonical FLAC outputs, reject mixed same-stem containers, atomically replace the active bank, and refresh the embedded inventory. Add a negative regression starting from the committed FLAC-only package. Static review only; the command was not run. Estimated effort: Medium.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (test `711e6a5a`; root cause `55298fb1` + `dc135609`) by an agent other than the fixer.

`StringsGenericScopedPublicationTest.test_strings_selector_replaces_all_three_families_without_wav_duplicates` drives `main` with `--only=cellosolo,dbass,pizzbass` over all 40 real entries; only the 40 FLACs remain.

**Fails-before (method B).** Making the shared publisher copy WAVs fails the published-name set assertion. Restored; it and `StringsPackagedDocumentContractTest` pass on HEAD.

## Notes
