# MM-BUG-KILN-00148 — Standalone MuseScore-grand crate omits the upstream MIT permission and full copyright notices

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample packaging / licensing
- **Raised:** 2026-07-26
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
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=gpt-5.6-sol@high) → Fixed (2026-07-27, deltic:auto role=fix run=fix-20260726T235403Z-p9812-n116206100-c25 branch=task/bug-MM-BUG-KILN-00148-run-fix-20260726T235403Z-p9812-n116206100-c25 code=4c7e9b49a225a67dfed2a9a7f1827ddfae2cf922 gate=focused-licensing model=codex@xhigh; held branch recovered by Codex)

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

### Fix summary (2026-07-27, deltic:auto run=fix-20260726T235403Z-p9812-n116206100-c25 code=4c7e9b49a225a67dfed2a9a7f1827ddfae2cf922 gate=focused-licensing)

Agent-reported summary: Fixed MM-BUG-KILN-00148 by making the standalone MuseScore grand sample crate carry the complete upstream MIT permission text and MuseScore/FluidR3 copyright notices in its packaged NOTICE. Reproduced the original static observation by confirming the package include list shipped README.md, NOTICE, and PROVENANCE.md but none contained the MIT permission grant. Added a licensing regression that reads each MIT sample bank's own packaged documents rather than relying on the parent ferrosintesis notice. The new regression failed before the NOTICE fix on ferrosintesis-samples-musescore-grand and passed after the notice was completed. Recovery also compared the notice with the pinned MuseScore_General licence and restored the two mandatory acknowledgement lines omitted by the held fix.

Root cause: The MuseScore grand crate's NOTICE was a hand-written abbreviated attribution that named MIT and some lineage credits, but the existing oracle only required a packaged NOTICE with a licence name and one licensor-owned signal. That allowed an independently publishable MIT sample crate to omit the permission grant and full upstream copyright block required to accompany redistributed WAV payloads.

Changed:
- Completed crates/ferrosintesis-samples-musescore-grand/NOTICE with the MuseScore/FluidR3 copyright block, source licence URL, and full MIT terms.
- Extended crates/ferrosintesis/src/licensing.rs with a regression that checks packaged MIT bank documents for the MIT grant and the complete MuseScore-lineage copyright block.

Tests:
- $null | deltic timeout 180 cargo test -p ferrosintesis licensing (failed before the NOTICE fix, naming ferrosintesis-samples-musescore-grand)
- `$null | deltic timeout 240 cargo test -p ferrosintesis licensing::tests -- --nocapture` passed: 9 passed.
- `$null | deltic timeout 240 cargo test -p ferrosintesis --no-default-features licensing::tests -- --nocapture` passed: 9 passed.
- `$null | deltic timeout 180 cargo test -p ferrosintesis-samples-musescore-grand` passed: 2 unit tests and doc-tests.
- `deltic timeout 120 cargo package -p ferrosintesis-samples-musescore-grand --list --allow-dirty` confirmed that `NOTICE` is packaged.
- `deltic timeout 120 cargo fmt --package ferrosintesis -- --check` passed.
- `git diff --check` passed.

No Cargo manifest, lockfile, journal, scratchpad, or lesson file changed.

## Notes

This is not `MM-REQ-KILN-00144`. That Draft requirement tracks packaging the
exact source SHA-256; it does not cover the licence text that must accompany the
derived WAVs.
