# MM-BUG-KILN-00148 — Standalone MuseScore-grand crate omits the upstream MIT permission and full copyright notices

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample packaging / licensing
- **Raised:** 2026-07-26
- **Owner:** deltic:gpt-5.5
- **Owner role:** fix
- **Owner run:** fix-20260726T235403Z-p9812-n116206100-c25
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00148-run-fix-20260726T235403Z-p9812-n116206100-c25
- **Owner base:** 0e2a93420356d46b2d5d11a3dfa3f6d0fa2db0b7
- **Owner fingerprint:** -
- **Owner since:** 2026-07-26T23:54:03Z
- **Owner until:** 2026-07-27T00:39:03Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

Static reproduction:

1. Inspect the standalone package allowlist at `crates/ferrosintesis-samples-musescore-grand/Cargo.toml:10`: it ships `src/**`, `samples/**`, `README.md`, `NOTICE`, and `PROVENANCE.md`, but no upstream `COPYING` or licence file.
2. Read every packaged text file. `NOTICE:8-14` says MIT and gives abbreviated acknowledgements, but none of the packaged files contains the MIT permission grant (`Permission is hereby granted...`) or the complete upstream FluidR3/FluidR3Mono copyright notices.
3. Compare the cited MuseScore_General licence and the sibling MuseScore-derived packages. The upstream terms require the copyright and permission notices to accompany copies; `ferrosintesis-samples-clavinet/NOTICE` and `ferrosintesis-samples-musescore/NOTICE` reproduce both, while this independently publishable crate does not.

Expected: a consumer of the published standalone sample crate receives the complete upstream MIT permission and copyright notices required for redistribution.

Actual: the package contains the copyrighted WAV payloads and only an abbreviated notice. A parent `ferrosintesis` binary may concatenate a full MIT grant from another bank, but that does not repair distribution of this standalone crate.

No application, package command, generator, build, test, render, or exploratory harness ran. This was confirmed by static package-boundary inspection and an upstream licence lookup.

## Fix

Reproduce the complete upstream MIT permission grant and all required
FluidR3/FluidR3Mono/MuseScore_General copyright notices in this crate's
`NOTICE`, or add a dedicated upstream `COPYING` file and include it in the
manifest.

Extend `crates/ferrosintesis/src/licensing.rs` so an MIT sample bank cannot pass
merely by naming the licence and one licensor-owned signal. The regression must
inspect the packaged bank's own documents and fail when the permission grant or
required copyright block is removed.

Estimated effort: Small.

## Notes

This is not `MM-REQ-KILN-00144`. That Draft requirement tracks packaging the
exact source SHA-256; it does not cover the licence text that must accompany the
derived WAVs.
