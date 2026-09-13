# MM-BUG-KILN-00253 — MuseScore-grand package still documents WAV payloads after FLAC conversion

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** MuseScore grand sample crate / published package contract
- **Raised:** 2026-08-17T02:29:49Z
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
- **State history:** Open (2026-08-17T02:29:49Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-09-13T08:07:48Z, deltic:auto role=fix run=fix-20260913T080115Z-16968b61 branch=task/bug-MM-BUG-KILN-00253-run-fix-20260913T080115Z-16968b61 code=12b5f29b5e1e2ae473ab3c97048ae5520b7af99e gate=manual) -> Closed (2026-09-13T20:22:13Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: MuseScore-grand docs list 25 FLAC keys and 1,223,383 bytes; pre-fix docs fail the contract test)

## Observation

Static review found the published package still describes WAV payloads after the FLAC migration. crates/ferrosintesis-samples-musescore-grand/README.md:7-9 says the dense bank is made of mono 16-bit 44.1 kHz WAVs, and PROVENANCE.md:9-14 plus :41-47 says the committed source/output is WAV. The package actually embeds 25 `.flac` keys at crates/ferrosintesis-samples-musescore-grand/src/lib.rs:14-111. A standalone consumer following the published physical-format description can derive `.wav` lookup names that `get()` does not contain, and the package audit trail states the wrong shipped container. Expected: README and provenance describe the final FLAC payloads and lookup names. Actual: both describe the retired WAV bank. Concrete fix: update the format, processing, and output wording; name the complete final-format regeneration workflow; and add a source-derived document guard proving the packaged format claims and at least one documented key match the embedded inventory. Open MM-BUG-KILN-00243 covers the separate `ferrosintesis-samples-grand` crate and does not fix this independently published package. Static review only; no app, build, test, decoder, generator, render, or exploratory harness ran. Estimated effort: Small.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `12b5f29b`) by an agent other than the fixer.

**Original observation re-derived.** MuseScore-grand README and PROVENANCE say FLAC, list all 25 keys, give 1,223,383 bytes (25 files), and describe the full scoped `--only=musescoregrand` workflow including FLAC publication.

**Fails-before (method A).** With docs from `12b5f29b^`, `MuseScoreGrandSampleApiContractTest` fails. It passes on HEAD; its documented key set equals disk and the embedded table. Both crate tests pass.

## Notes
