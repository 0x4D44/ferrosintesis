# MM-BUG-CRU-00060 — Sample container-documentation oracle misses WAV claims after source-context phrases and headings

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** sample asset crates / container documentation oracle
- **Raised:** 2026-09-13T19:22:42Z
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
- **State history:** Open (2026-09-13T19:22:42Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T20:24:45Z, deltic:auto role=fix run=fix-20260913T201450Z-4b649983 branch=task/bug-MM-BUG-CRU-00060-run-fix-20260913T201450Z-4b649983 code=02b8eec294c48d666cf7717f4ab565660483db00 gate=manual) -> Closed (2026-09-13T20:59:45Z, independent verify by Codex run=verify-20260913T204905Z-553a16f8: packaged WAV claims remain visible despite source context and headings)

## Observation

Split at independent verification of MM-BUG-CRUCIBLE-00044 (2026-09-13, trunk 8b6a6f86). payload::tests::sample_crate_documents_match_their_packaged_containers (fix db16a45b) exempts lines that contain source-context phrases or sit under source-ish headings. With the pre-fix text restored it does NOT flag the bug's own cited sentence, clavinet PROVENANCE.md:9 'The 11 WAVs in samples/ are ... extracted from ...', because 'extracted from' marks it as source context. It also accepted an adversarial 'This crate ships 11 WAV files.' planted under '## Extraction and bake'. Expected: a claim about the packaged samples/ container is judged by its subject, not exempted by a nearby phrase or heading.

## Fix

`02b8eec294c48d666cf7717f4ab565660483db00` (`fix(MM-BUG-CRU-00060): classify packaged container claims by subject`) adds explicit package subject markers (`crate ships`, `package ships`, and `samples/` claims) and a `bake` source marker. It adds adversarial fixtures for source-context and extraction-heading false negatives.

## Verification

- Independent verifier: Codex, run `verify-20260913T204905Z-553a16f8`; no same-code ownership collision was reported.
- `cargo test -p ferrosintesis payload::tests::`: 10 passed, including the original packaged-container oracle and the regression test.
- Mutation check: removing the `in \`samples/` and `samples/ are` package markers made `sample_container_oracle_rejects_a_mutated_public_document` fail as expected; the source was restored and the 10 focused tests passed again.
- `cargo fmt --all -- --check`: passed.
- Full `cargo test --workspace`: 897 passed, 44 ignored, and 2 unrelated inventory-test failures (`every_public_sample_inventory_surface_is_complete_or_delegated` and `every_generated_bake_output_family_is_inventory_validated`). No payload test failed.
- Full `cargo clippy --workspace --all-targets -- -D warnings`: failed on four unrelated pre-existing lints in `tests/archive_boundary.rs:562`, `src/midi.rs:1068`, `src/parse_robustness.rs:175`, and `src/payload.rs:434`; focused verification remains green.

## Notes

The persistent origin gate failures were recorded separately as `MM-BUG-CRU-00074`.
