# MM-BUG-KILN-00238 — Gong sample API still documents WAV keys and bytes after FLAC conversion

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** gong sample crate / public lookup contract
- **Raised:** 2026-08-16T21:52:59Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T195755Z-f79e08c9
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00238-run-verify-20260913T195755Z-f79e08c9
- **Owner base:** 6bf579c8825cfd21f7ceee44f3dc239d59b7711d
- **Owner fingerprint:** sha256:9ed7c6c288fbdc7dc4845cf5c6223b7de69f3f961e18a1372565bf28679ea16a
- **Owner since:** 2026-09-13T19:57:55Z
- **Owner until:** 2026-09-13T21:57:55Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-16T21:52:59Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T06:22:54Z, deltic:auto role=fix run=fix-20260913T061026Z-c982e0e7 branch=task/bug-MM-BUG-KILN-00238-run-fix-20260913T061026Z-c982e0e7 code=bf8066cda96af77f7c9e0e13c0046d24733c969a gate=manual)

## Observation

Observation: crates/ferrosintesis-samples-gong/src/lib.rs:23-25 promises embedded WAV bytes and exact names with a .wav suffix, and README.md:3-5 promises raw WAV bytes. The shipped SAMPLES table at src/lib.rs:12-20 contains only gong_ageng_loud.flac and gong_ageng_soft.flac, so a caller following the public docs receives None for either documented .wav key; a caller that uses the current key but trusts the documented container passes FLAC bytes to a WAV parser. PROVENANCE.md:93-108 compounds the stale contract by inventorying .wav outputs and the retired 2,971,398-byte aggregate, while the two packaged FLAC files total 1,160,636 bytes. Expected: the published API, README, and provenance name the actual FLAC keys/container and current packaged inventory, or intentionally preserve documented WAV aliases with a clear container contract. Concrete fix: choose and document the supported compatibility contract, update all package-local prose and inventory together, and add a documentation/API guard that rejects the current stale .wav wording and proves every documented lookup key resolves. Static review only; no app, test, build, generator, decoder, render, package command, or exploratory harness ran.

## Fix

<unfixed — raised only>

## Notes
