# MM-BUG-KILN-00291 — Fret-noise public API still documents WAV keys and bytes after FLAC conversion

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** fret-noise sample crate / public lookup contract
- **Raised:** 2026-08-17T20:45:41Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T211205Z-371e391b
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00291-run-verify-20260913T211205Z-371e391b
- **Owner base:** a24880284fb24448f3863d333aded683325e40ea
- **Owner fingerprint:** sha256:4f83b6c9856bc08bc490aadc6119110d7e594d2c9f3f4928a85c6d505aa7d5cf
- **Owner since:** 2026-09-13T21:12:05Z
- **Owner until:** 2026-09-13T23:12:05Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T20:45:41Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T19:32:20Z, deltic:auto role=fix run=fix-20260913T192808Z-986c2aa3 branch=task/bug-MM-BUG-KILN-00291-run-fix-20260913T192808Z-986c2aa3 code=84b6a05dcc286fc0974bd7c416a0bdd941ac77c2 gate=manual)

## Observation

Static review found that the published fret-noise asset crate still documents WAV lookup names and WAV payloads after its table migrated to FLAC. `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\crates\ferrosintesis-samples-fretnoise\src\lib.rs:20-65` contains only `.flac` keys, while `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\crates\ferrosintesis-samples-fretnoise\src\lib.rs:78-80` says `get` returns WAV bytes and exact names use `.wav`. Because `get` compares names exactly, a caller following the public contract and requesting `fretnoise_rr01.wav` receives `None`. `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\crates\ferrosintesis-samples-fretnoise\README.md:13-14,41-43` and `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\crates\ferrosintesis-samples-fretnoise\PROVENANCE.md:68-69` repeat the retired format. Expected: published API and package documentation describe the actual FLAC keys/container, or intentionally provide compatible aliases without mislabeling FLAC bytes as WAV. Concrete fix: update all package-local API/prose/test comments together, add a positive documented-key lookup assertion, and add a source-derived documentation guard so a future container migration cannot leave the public contract behind. Static review only; no app, test, build, generator, decoder, render, package command, or exploratory harness ran. Estimated effort: Small.

## Fix

<unfixed — raised only>

## Notes
