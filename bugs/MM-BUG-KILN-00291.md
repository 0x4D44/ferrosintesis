# MM-BUG-KILN-00291 — Fret-noise public API still documents WAV keys and bytes after FLAC conversion

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** fret-noise sample crate / public lookup contract
- **Raised:** 2026-08-17T20:45:41Z
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
- **State history:** Open (2026-08-17T20:45:41Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T19:32:20Z, deltic:auto role=fix run=fix-20260913T192808Z-986c2aa3 branch=task/bug-MM-BUG-KILN-00291-run-fix-20260913T192808Z-986c2aa3 code=84b6a05dcc286fc0974bd7c416a0bdd941ac77c2 gate=manual) -> Closed (2026-09-14T22:04:11Z, independent verify by Claude Opus 5 on trunk 1d87b00f: fret-noise rustdoc, README and PROVENANCE now describe .flac keys and FLAC bytes; a positive documented-key lookup test passes)

## Observation

Static review found that the published fret-noise asset crate still documents WAV lookup names and WAV payloads after its table migrated to FLAC. `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\crates\ferrosintesis-samples-fretnoise\src\lib.rs:20-65` contains only `.flac` keys, while `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\crates\ferrosintesis-samples-fretnoise\src\lib.rs:78-80` says `get` returns WAV bytes and exact names use `.wav`. Because `get` compares names exactly, a caller following the public contract and requesting `fretnoise_rr01.wav` receives `None`. `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\crates\ferrosintesis-samples-fretnoise\README.md:13-14,41-43` and `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\crates\ferrosintesis-samples-fretnoise\PROVENANCE.md:68-69` repeat the retired format. Expected: published API and package documentation describe the actual FLAC keys/container, or intentionally provide compatible aliases without mislabeling FLAC bytes as WAV. Concrete fix: update all package-local API/prose/test comments together, add a positive documented-key lookup assertion, and add a source-derived documentation guard so a future container migration cannot leave the public contract behind. Static review only; no app, test, build, generator, decoder, render, package command, or exploratory harness ran. Estimated effort: Small.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` (fix `84b6a05d`) by an agent other than the fixer.

**Original observation, re-derived.** The crate's `samples/` holds 12 files, `fretnoise_rr01.flac` to `fretnoise_rr12.flac`. The `get` rustdoc now says it returns FLAC bytes for an exact `.flac` name; the README shows `get("fretnoise_rr01.flac")` asserting `fLaC`; PROVENANCE documents the `.flac` lookup key. `public_lookup_accepts_the_documented_flac_name` passes: the documented key resolves to `fLaC` bytes and `fretnoise_rr01.wav` returns `None`. The remaining 'wav' mentions describe the tracked source cuts (`cuts/fret_rrNN.wav` hashes, restoring source WAVs) or name `sampler::parse_wav`, which is accurate.

**Fails-before (method A).** Against `84b6a05d^`, the README lacks the `.flac` example and `fLaC` check and the rustdoc lacks the FLAC wording, so `FretnoisePackagedContractTest` fails there; it passes on the fix and in the gate's Python suite. The fix is docs-only, so the new Rust lookup test pins behaviour that was already correct; closure rests on the re-derivation above.

**Repo gate on `1d87b00f`.** Green: fmt, all three clippy steps, `cargo test -p ferrosintesis-cli --no-default-features`, and `cargo test --workspace --all-targets`. Red, not caused by this fix: `cargo test -p ferrosintesis --no-default-features` fails `no_default_gate_is_paired_with_embedded_sample_coverage` (MM-BUG-KILN-00301 reopened), and 4 `test_prepare.py` tests error (MM-BUG-CRU-00068 reopened).

## Notes
