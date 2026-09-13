# MM-BUG-KILN-00251 — Honky-tonk regeneration command leaves the embedded FLAC bank stale

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** honky-tonk sample crate / deterministic regeneration
- **Raised:** 2026-08-17T01:05:18Z
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
- **State history:** Open (2026-08-17T01:05:18Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T07:58:25Z, deltic:auto role=fix run=fix-20260913T075214Z-f2492ebf branch=task/bug-MM-BUG-KILN-00251-run-fix-20260913T075214Z-f2492ebf code=55298fb16c0f370149bafafb7e518685cafa4443 gate=manual) -> Closed (2026-09-13T20:44:18Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: --only=honkytonk leaves 9 FLACs; skipping the pending publish reproduces the 18-vs-9 symptom; direct writer split to MM-BUG-CRU-00070)

## Observation

The crate publishes `python3 tools/ferrosintesis-samples/prepare.py
--only=honkytonk` as its regeneration command at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\crates\ferrosintesis-samples-honkytonk\README.md:14-15`
and
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\crates\ferrosintesis-samples-honkytonk\PROVENANCE.md:48-54`.
The active crate embeds nine `.flac` files at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\crates\ferrosintesis-samples-honkytonk\src\lib.rs:12-49`,
and the runtime requests those FLAC names at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\crates\ferrosintesis\src\sampler.rs:1760-1773`.
The documented recipe instead validates and writes `honkytonk_*.wav` at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\tools\ferrosintesis-samples\prepare.py:4787-4818`,
while its stale-output validator inspects only WAV names at `prepare.py:5402-5429`.

Following the documented command therefore adds nine WAVs beside the nine old
FLACs without changing the payloads runtime consumes. The crate inventory test at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\crates\ferrosintesis-samples-honkytonk\src\lib.rs:70-84`
then sees 18 sample files against `FILE_COUNT = 9`. Expected: the scoped command
atomically replaces and verifies the exact final-format bank runtime embeds.
Actual: it creates unconsumed outputs, leaves playback stale, and makes inventory
fail. Concrete fix: make the recipe stage, encode, verify, and publish the nine
final FLACs as one unit; reject mixed containers before the first write; refresh
the generated table; and add a negative regression starting from the current
FLAC-only tree. Static review only; the command was not run.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `55298fb1`) by an agent other than the fixer.

**Original observation re-run.** A scratch harness ran `main` with `--only=honkytonk` over the real 9 notes on an isolated FLAC-only bank: all 9 FLACs replaced, no WAVs.

**Fails-before (method B).** Making `_finish` skip the pending-bank publish reproduces exactly the recorded 18 files against `FILE_COUNT=9` and fails the shared `GongRegenerationWorkflowTest`. Restored; the shared tests, `HonkytonkOutputInventoryTest` and `HonkytonkSampleApiContractTest` pass on HEAD. No honky-tonk-specific end-to-end test exists.

**Residual split to MM-BUG-CRU-00070.** `_bake_honkytonk` writes WAVs straight into the live crate and conversion is not all-or-nothing.

## Notes

Open `MM-BUG-KILN-00239`, `MM-BUG-KILN-00244`, and
`MM-BUG-KILN-00248` cover analogous but independently owned sample workflows.
Open `MM-BUG-KILN-00241` covers the separate syntax failure in
`gen_crate_lib.py`. Closed WAV-era stale-output bugs do not cover this later FLAC
migration mismatch.
