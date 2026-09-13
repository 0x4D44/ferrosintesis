# MM-BUG-KILN-00287 — Orchestral regeneration leaves the embedded FLAC bank stale

- **State:** Closed
- **Priority:** Must
- **Severity:** Medium
- **Area:** orchestral sample generation / final-format regeneration
- **Raised:** 2026-08-17T13:40:55Z
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
- **State history:** Open (2026-08-17T13:40:55Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T04:24:49Z, deltic:auto role=fix run=fix-20260913T042224Z-c069c901 branch=task/bug-MM-BUG-KILN-00287-run-fix-20260913T042224Z-c069c901 code=55298fb16c0f370149bafafb7e518685cafa4443 gate=manual) -> Closed (2026-09-13T20:44:18Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: steel and chanter regenerations leave FLAC-only banks; each publish reversal reproduces the mixed inventory; bagpipe direct writer split to MM-BUG-CRU-00070)

## Observation

The published regeneration instruction at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-141930\crates\ferrosintesis-samples-orchestral\PROVENANCE.md:7`
tells maintainers to run `prepare.py --only=<family>`. The selected-family maps
at `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-141930\tools\ferrosintesis-samples\prepare.py:5303`
still derive `.wav` output names, the preflight at line 5402 inspects only WAVs,
and the generic bake loop at line 5733 writes those WAV names directly. The
bagpipe-specific path does the same at line 4266. The active package instead
contains 158 FLAC files and exact `.flac` keys at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-141930\crates\ferrosintesis-samples-orchestral\src\lib.rs:12`;
the synth consumer also requests FLAC keys.

Following the documented command therefore creates fresh, unconsumed WAVs beside
unchanged FLACs. Runtime keeps using the stale FLAC bank,
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-141930\crates\ferrosintesis-samples-orchestral\Cargo.toml:10`
packages both containers, and the crate inventory sees the mixed set. The required
preflight at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-141930\tools\ferrosintesis-samples\test_prepare.py:2823`
also compares WAV expectations with only on-disk WAVs, so the current FLAC-only
families cannot satisfy it.

Expected: every scoped recipe stages, validates, and replaces the exact
final-format bank consumed at runtime. Concrete fix: separate source member names
from canonical output names, encode and independently verify the complete FLAC
set in empty staging, reject mixed same-stem containers, publish the validated
set atomically, refresh the generated Rust inventory, and add a negative fixture starting from
the committed FLAC-only tree. Static source review only; no generator, test,
decoder, app, package command, or exploratory harness ran.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `55298fb1` + `dc135609`) by an agent other than the fixer.

**Original observation re-run.** A scratch harness drove `main` on an isolated FLAC-only orchestral bank: `--only=steel` (generic path) replaced 8 FLACs and `--only=chanter` (bagpipe path) replaced 17, neither leaving WAVs. The required `SelectedFamilyPreflightTest` compares packaged names and passes.

**Fails-before (method B).** A WAV-copying staged publisher doubles the steel inventory (16 != 8); skipping the pending-bank publish doubles the chanter inventory (34 != 17). Restored; the preflight and shared generic tests pass on HEAD.

**Residual split to MM-BUG-CRU-00070.** `_bake_bagpipe` writes WAVs straight into the live crate and converts at the end, which is not transactional.

## Notes

Open `MM-BUG-KILN-00241` covers the separate generated-library syntax failure.
Open `MM-BUG-KILN-00262` records the analogous orchestral2
impact but does not name or verify this original package.
