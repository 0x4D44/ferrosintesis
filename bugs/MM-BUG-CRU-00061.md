# MM-BUG-CRU-00061 — ffmpeg-prerequisite documentation tests pass on text that denies ffmpeg is needed

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample tooling / regeneration prerequisite oracles
- **Raised:** 2026-09-13T19:22:43Z
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
- **State history:** Open (2026-09-13T19:22:43Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T20:38:22Z, deltic:auto role=fix run=fix-20260913T202711Z-3a9994fe branch=task/bug-MM-BUG-CRU-00061-run-fix-20260913T202711Z-3a9994fe code=bf681a3f105cef44e82b767c99a4fd751b40cc2d gate=manual) -> Closed (2026-09-13T21:11:51Z, independent verify by Codex run=verify-20260913T210307Z-804af6a8: negated ffmpeg prerequisites no longer satisfy documentation contracts)

## Observation

Split at independent verification of MM-BUG-CRU-00047, MM-BUG-CRU-00051 and MM-BUG-CRU-00053 (2026-09-13, trunk 8b6a6f86). GrandRegenerationRecipeTest, KawaiPackagedDocumentContractTest and YdpPackagedDocumentContractTest only require 'ffmpeg' within ~80 characters of 'PATH'. Rewording the grand, Kawai or YDP README/PROVENANCE to 'does not need ffmpeg on PATH' / 'needs no ffmpeg on PATH' still passes, so the tests cannot tell a requirement from a denial. The CRU-00053 record asked for an oracle that rejects 'no ffmpeg' claims for every recipe reaching _require_ffmpeg(); the landed tests are per-crate and negation-blind.

## Fix

`bf681a3f105cef44e82b767c99a4fd751b40cc2d` (`fix(MM-BUG-CRU-00061): reject negated ffmpeg prerequisites`) adds a shared prerequisite oracle that requires affirmative ffmpeg/PATH language and rejects nearby negation. It applies the oracle to the Grand, Kawai, and YDP documentation contracts.

## Verification

- Independent verifier: Codex, run `verify-20260913T210307Z-804af6a8`; no same-code ownership collision was reported.
- Original affected contracts: `GrandRegenerationRecipeTest`, `KawaiPackagedDocumentContractTest`, and `YdpPackagedDocumentContractTest` passed all 8 tests.
- Regression tests: `FfmpegPrerequisiteDocumentationTest` passed both positive and negated-claim tests.
- Mutation check: removing `no` from the negative matcher made the negated-claim regression fail on `The recipe needs no ffmpeg on PATH.`; the source was restored and all 10 focused tests passed again.
- `cargo fmt --all -- --check`: passed.
- Full Python sample suite: 267 tests passed.
- Full `cargo test --workspace`: 900 passed, 44 ignored, and 1 unrelated inventory-test failure (`every_public_sample_inventory_surface_is_complete_or_delegated`). No ffmpeg documentation test failed.
- Full `cargo clippy --workspace --all-targets -- -D warnings`: failed on four unrelated baseline lints in `tests/archive_boundary.rs:562`, `src/midi.rs:1068`, `src/parse_robustness.rs:175`, and `src/payload.rs:434`.

## Notes

The persistent origin gate failures were recorded separately as `MM-BUG-CRU-00074`.
