# MM-BUG-KILN-00293 — Successful fret-noise rebake retains obsolete packaged outputs

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** fret-noise sample generation / output inventory
- **Raised:** 2026-08-17T20:46:02Z
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
- **State history:** Open (2026-08-17T20:46:02Z, raised via `deltic bugs new`)

## Observation

A successful normal fret-noise bake does not reconcile the packaged output set. `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\tools\ferrosintesis-samples\fretnoise_bake.py:305-322` inspects committed names only when `out_dir` is supplied, but `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\tools\ferrosintesis-samples\fretnoise_bake.py:343` passes `out_dir` only for `--verify`. The normal write loop at `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\tools\ferrosintesis-samples\fretnoise_bake.py:366-369` encodes generated names and never detects or removes obsolete `fretnoise_rr*.flac` files. If maintainers intentionally retire a source cut and update its pin and Rust table before rebaking, the command reports success while the old FLAC remains under `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-212530\crates\ferrosintesis-samples-fretnoise\Cargo.toml:10`'s `samples/**` package allowlist; the later crate inventory test fails, and a package command run without that test can carry the stale payload. Expected: a successful normal bake produces exactly the authoritative output set. Concrete fix: stage the complete bank in an empty directory, validate exact name equality, then publish atomically while removing only obsolete files owned by this generator; add a removed-take negative control. This is distinct from `MM-BUG-KILN-00229`, which covers partial publication after a write failure. Static review only; no app, test, build, generator, decoder, render, package command, or exploratory harness ran. Estimated effort: Small-Medium.

## Fix

<unfixed — raised only>

## Notes
