# MM-BUG-KILN-00227 — Mandatory gate can accept fret-noise WAVs that violate BAKE-SHA256

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** fret-noise sample integrity gate
- **Raised:** 2026-08-16T16:53:04Z
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
- **State history:** Open (2026-08-16T16:53:04Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-09-13T16:15:47Z, deltic:auto role=fix run=fix-20260913T155945Z-fcf1412b branch=task/bug-MM-BUG-KILN-00227-run-fix-20260913T155945Z-fcf1412b code=a2f0f9dc38151ac172bc006a712a500f0ac27599 gate=manual) -> Closed (2026-09-13T20:44:18Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: a same-length one-byte mutation of a committed fret-noise FLAC fails the mandatory stdlib BAKE-SHA256 test)

## Observation

The crate publishes an exact per-file output manifest at
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-173412\crates\ferrosintesis-samples-fretnoise\BAKE-SHA256:1`, but the mandatory checks do not authenticate the committed WAVs against it.

`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-173412\crates\ferrosintesis-samples-fretnoise\src\lib.rs:192` compares each embedded file with the on-disk file by length only. The other crate test at
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-173412\crates\ferrosintesis-samples-fretnoise\src\lib.rs:208` checks aggregate length and RIFF/WAVE magic. A same-length PCM change that preserves the first twelve bytes satisfies every one of those assertions.

The Python test module does exercise exact hashing, but
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-173412\tools\ferrosintesis-samples\test_fretnoise_bake.py:18` skips the whole module when NumPy is absent. Its real-bank verification at line 93 also skips outside the one canonical Python/NumPy platform. The required integration gate at
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-173412\.deltic-integrate.toml:50` explicitly accepts those skips.

**Static reproduction.** Change one PCM byte without changing the file length or RIFF/WAVE signature, on a gate box without the canonical bake environment. The Rust predicates remain true and the exact verifier skips, so the required gate can pass while the committed file disagrees with its packaged pin. Depending on the changed bytes, the released bank can play altered audio or panic the trusted embedded-WAV parser.

**Expected.** Every required gate authenticates the exact filename set and each committed output against `BAKE-SHA256`, independently of the optional canonical re-bake environment.

**Actual.** Exact output authentication is optional. The current files are not corrupt: this review independently hashed all twelve, and every digest matches its pin. This is a Low-severity false-negative in release protection.

## Fix

Unfixed. Add an always-on, standard-library-only check that strictly parses
`BAKE-SHA256`, requires exact manifest/directory filename equality, and hashes
every committed WAV. Keep the canonical NumPy re-bake as stronger optional
coverage. Add a same-length PCM mutation negative control and require that it
fails.

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `a2f0f9dc`) by an agent other than the fixer.

**Original observation re-derived.** `test_fretnoise_manifest.py` is standard-library only (no numpy skip) and is collected by the mandatory `unittest discover -s tools/ferrosintesis-samples` gate step. It strictly parses `BAKE-SHA256`, requires the manifest's file set to equal the 12 committed FLACs, and hashes each.

**Fails-before (static reproduction from the record).** Flipping one mid-file byte of `fretnoise_rr01.flac` without changing its length fails `test_committed_bank_matches_exact_file_manifest` (sha256 52c57212... != pinned aed3e134...). Flipped back; status clean; all four `FretNoiseManifestTests` pass on HEAD.

This fix does not touch `sampler.rs`; the clavinet gate failures trace to `6ee2af43` (MM-BUG-CRU-00064).

## Notes

Closed `MM-BUG-KILN-00095` added the canonical environment, pins, and optional
non-mutating re-bake. It did not make committed-output authentication mandatory,
so this is a residual rather than a duplicate. Implemented
`MM-REQ-KILN-00031` cites the length-only Rust test as byte-identity evidence.
