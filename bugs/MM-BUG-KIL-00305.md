# MM-BUG-KIL-00305 — decode_riff_wav silently truncates an over-declared data chunk instead of panicking

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / drum-kit RIFF fallback decoder
- **Raised:** 2026-08-19T09:33:15Z
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
- **State history:** Open (2026-08-19T09:33:15Z, raised via `deltic bugs new`) -> Fixed (2026-09-14T00:44:11Z, deltic:auto role=fix run=fix-20260914T003625Z-ced54b4c branch=task/bug-MM-BUG-KIL-00305-run-fix-20260914T003625Z-ced54b4c code=530be42c gate=manual) -> Closed (2026-09-14T22:59:10Z, independent verify by Claude Opus 5 on trunk 81252a3e: both drum-kit RIFF walkers now panic on an over-declared chunk; restoring the clamped slice makes each crate's regression test stop panicking)

## Observation

The drum-kit crates' RIFF walker accepts a `data` chunk that declares more bytes
than the file contains, decoding a silently short buffer — breaking the crate's own
decode contract, which the FLAC branch of the same dispatcher enforces.

`crates/ferrosintesis-samples-drumkit2/src/lib.rs:289`:
`let body = &bytes[pos + 8..(pos + 8 + len).min(bytes.len())];` — the
`.min(bytes.len())` clamp is the only bound; nothing compares the declared `len`
with what is present. Repro (static): an embedded RIFF asset with a valid `fmt `
chunk followed by `data` declaring 200,000 bytes while 1,000 remain. The loop guard
at line 286 admits the chunk, line 289 clamps the body, line 299-302 collects 500
samples, line 304 advances `pos` past EOF so the loop exits, and line 306's
`assert!(!data.is_empty())` passes. `decode_wav` returns an ~11 ms buffer where a
~2 s cymbal was expected, cached for the process lifetime (`PCM_CACHE`, line 256).

That contradicts the stated contract at lines 272-276: "an embedded asset that
fails to decode is an asset-pipeline bug" → panic. The FLAC branch rejects exactly
this failure shape (`ferrosintesis_flac::decode_mono16` errors when the decoded
count disagrees with STREAMINFO, which line 276 turns into a panic), so the two
branches of one dispatcher disagree on the same failure mode. The twin walker in
`crates/ferrosintesis-samples-drumkit/src/lib.rs:815` has the identical clamp.

Latent, not live: all 36 (and 128) current assets are FLAC, the RIFF path is the
fallback for future assets, and the duration oracle would catch the truncation for
crash/china (though not splash — MM-BUG-KILN-00203). Classification: robustness
defect in a shipped fallback path; found via lesson "Embedded data still needs
fallible, chunk-bounded parsing".

## Fix

Bound the chunk before slicing: assert `pos + 8 + len <= bytes.len()` with a
message naming the chunk id and shortfall, then slice exactly `len` bytes. Apply to
both crates' walkers in one change. Regression: a fixture with an over-declared
`data` length must panic; make it fail first against the current clamp.

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `81252a3e` (fix `530be42c`) by an independent verifier worker in this pass, other than the fixer. A later commit, `091b98f8`, touched only drumkit2's tests; the walker hunk is unchanged.

**Original observation, root cause.** The `.min(bytes.len())` clamp was the only bound, so a `data` chunk declaring more bytes than the file held decoded silently short. Both walkers (drumkit2 `src/lib.rs` about line 300, drumkit about line 832) now `assert!(len <= available, "RIFF chunk {} body is {} bytes short", ...)` and slice exactly `len` bytes. That matches the FLAC branch's panic-on-mismatch contract and also bounds the `fmt ` chunk.

**Fails-before (method B).** `tests::riff_walker_rejects_overdeclared_data_chunk` (`#[should_panic]`) passes in both crates. Its fixture declares a 4-byte data chunk with 2 bytes present, the recorded failure shape. Reverting only the assert-and-slice hunk to `let body = &bytes[pos + 8..(pos + 8 + len).min(bytes.len())];` fails it in each crate: 'test did not panic as expected' (drumkit2 `lib.rs:333`, drumkit `lib.rs:865`). Restored.

**Repo gate.** Both crates' lib suites pass under `cargo test --workspace --all-targets` (run on `1d87b00f` and `011738f6` earlier in this pass). The Python gate step is green on `56ba5184`.

## Notes

Raised by the 2026-08-19 static review of `crates/ferrosintesis-samples-drumkit2/`
(worktree 20260819-REV-MM-CLA@KILN-code-review-101941). Prior drumkit2 decode bugs
MM-BUG-KILN-00174/00175 covered different defects (miss-path decode cost; inventory
oracle) and are Closed. Estimated effort: Small.
