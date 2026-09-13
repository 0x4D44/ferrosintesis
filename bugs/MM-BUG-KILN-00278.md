# MM-BUG-KILN-00278 — Crate rustdoc overstates the embedded payload and evades its size oracle

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis / public payload documentation
- **Raised:** 2026-08-17T09:42:03Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260913T220707Z-29f8619f
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00278-run-fix-20260913T220707Z-29f8619f
- **Owner base:** 7fb684187aae579c5e149ba722039a0c75646134
- **Owner fingerprint:** -
- **Owner since:** 2026-09-13T22:07:07Z
- **Owner until:** 2026-09-14T00:07:07Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T09:42:03Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T18:35:03Z, deltic:auto role=fix run=fix-20260913T181332Z-673057bf branch=task/bug-MM-BUG-KILN-00278-run-fix-20260913T181332Z-673057bf code=4a4df67d171fe46ed93a004de7fde5c2b9433bb1 gate=manual) -> Open (2026-09-13T19:35:03Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: the rewritten rustdoc still overstates the payload (1080 recordings against 1026 embedded, 54 MiB for 51.5 MiB) and the fix breaks the clippy gate)

## Observation

Observation: public crate rustdoc at crates/ferrosintesis/src/lib.rs:51-53 still claims the default feature embeds roughly 111 MiB across 1156 WAVs. The current default sample-crate directories contain 1080 WAV/FLAC recordings totaling 56,450,470 bytes (53.835 MiB), matching README.md:84-96 after the FLAC migration. The source-derived size oracle does not catch the stale rustdoc because payload.rs:size_claims at :123-149 scans one line at a time: line 51 contains compiles but no MiB, while line 52 contains MiB but neither embed nor compil. The stale wrapped paragraph therefore contributes no claim and the test passes on the README claim alone.

Expected: docs.rs describes the current embedded payload and the guard rejects a stale claim even when Markdown/rustdoc wraps it. Actual: the public size/count contract is about two times too large and names the retired all-WAV container set; its guard silently skips it.

Concrete fix: update the crate rustdoc to approximately 54 MiB, 1080 recordings, WAV/FLAC wording; make size_claims inspect paragraphs or joined continuation lines; add an adversarial wrapped stale-claim fixture that must fail.

Static review only. File count and bytes were independently read from the current sample directories. Estimated effort: Small.

## Fix

<unfixed — raised only>

## Notes

### Verification (reopen) (2026-09-13, Claude Opus 5, independent)

Checked on trunk `8b6a6f86` (fix `4a4df67d`) by an agent other than the fixer.

**What works.** The size oracle now joins wrapped lines: restoring the pre-fix wrapped "111 MiB" rustdoc fails `documented_payload_size_is_within_ten_percent` ("claims 111 MiB ... embeds 51.5 MiB (116% off)"), and making `size_claims_in` scan line by line again fails `size_oracle_rejects_a_wrapped_stale_claim`. Both pass on HEAD.

**Why reopened.**
1. The rewritten rustdoc still overstates the payload. `crates/ferrosintesis/src/lib.rs:51-52` says "roughly 54 MiB ... across 1080 WAV/FLAC recordings". Counting `samples/` WAV/FLAC files in the 24 crates of the `embedded-samples` feature on origin/main gives 1026, as `crates/ferrosintesis/README.md:85` already says. The payload is 53,996,157 bytes: 54.0 MB but 51.5 MiB. That is inside the oracle's 10% tolerance, so it is mislabelled rather than rejected.
2. The fix breaks the required clippy gate: `filter_next` at `crates/ferrosintesis/src/payload.rs:429` (`.filter(|tok| !tok.is_empty()).next_back()`, blamed to `4a4df67d`) fails `cargo clippy --workspace --all-targets -D warnings` on clippy 1.95.0.
3. No oracle checks the recording count, and `//!` blocks are never split into paragraphs, so the whole module doc is scanned as one.

**Needed to close.** Use `.rfind(..)`, state 1026 recordings and 51.5 MiB (or derive both), and consider a recording-count claim oracle.
