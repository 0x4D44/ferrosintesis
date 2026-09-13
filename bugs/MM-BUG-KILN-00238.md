# MM-BUG-KILN-00238 — Gong sample API still documents WAV keys and bytes after FLAC conversion

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** gong sample crate / public lookup contract
- **Raised:** 2026-08-16T21:52:59Z
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
- **State history:** Open (2026-08-16T21:52:59Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T06:22:54Z, deltic:auto role=fix run=fix-20260913T061026Z-c982e0e7 branch=task/bug-MM-BUG-KILN-00238-run-fix-20260913T061026Z-c982e0e7 code=bf8066cda96af77f7c9e0e13c0046d24733c969a gate=manual) -> Closed (2026-09-13T19:59:17Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: gong docs describe two FLAC keys totalling 1,160,636 bytes; pre-fix docs fail the lookup contract test)

## Observation

Observation: crates/ferrosintesis-samples-gong/src/lib.rs:23-25 promises embedded WAV bytes and exact names with a .wav suffix, and README.md:3-5 promises raw WAV bytes. The shipped SAMPLES table at src/lib.rs:12-20 contains only gong_ageng_loud.flac and gong_ageng_soft.flac, so a caller following the public docs receives None for either documented .wav key; a caller that uses the current key but trusts the documented container passes FLAC bytes to a WAV parser. PROVENANCE.md:93-108 compounds the stale contract by inventorying .wav outputs and the retired 2,971,398-byte aggregate, while the two packaged FLAC files total 1,160,636 bytes. Expected: the published API, README, and provenance name the actual FLAC keys/container and current packaged inventory, or intentionally preserve documented WAV aliases with a clear container contract. Concrete fix: choose and document the supported compatibility contract, update all package-local prose and inventory together, and add a documentation/API guard that rejects the current stale .wav wording and proves every documented lookup key resolves. Static review only; no app, test, build, generator, decoder, render, package command, or exploratory harness ran.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `bf8066cd`) by an agent other than the fixer.

**Original observation re-derived.** Gong rustdoc, README and PROVENANCE describe FLAC and name `gong_ageng_loud.flac` and `gong_ageng_soft.flac`; 518,201 + 642,435 = 1,160,636 bytes = `EXPECTED_BYTES`. Documented keys resolve through `get()` and `.wav` keys return None; remaining WAV wording covers only committed `gong-src/` inputs.

**Fails-before (method A).** With README and PROVENANCE from `bf8066cd^`, `documented_flac_lookup_contract_matches_packaged_inventory` fails. All three gong tests pass on HEAD.

## Notes
