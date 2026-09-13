# MM-BUG-CRU-00050 — Mandolin provenance still names a retired physical WAV package path

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** mandolin sample crate / packaged provenance
- **Raised:** 2026-08-20T12:21:24Z
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
- **State history:** Open (2026-08-20T12:21:24Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:11:08Z, deltic:auto role=fix run=fix-20260913T150730Z-28f71eea branch=task/bug-MM-BUG-CRU-00050-run-fix-20260913T150730Z-28f71eea code=b8162d01134c9adc165374e1465b61cb32f34480 gate=manual) -> Closed (2026-09-13T19:59:17Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: mandolin provenance separates 40 logical WAV inputs from 40 packaged FLACs; reversing the hunk fails the wording test)

## Observation

The published provenance describes a physical package path that no longer exists.
`D:\worktrees\ferrosintesis\20260820-REV-MM-CDX@CRUCIBLE-code-review-124001\crates\ferrosintesis-samples-mandolin\PROVENANCE.md:18-20`
says the committed source cuts are inputs and “`samples/*.wav` here is the baked
output.” The package instead contains 40 `.flac` files, and the generated table at
`crates/ferrosintesis-samples-mandolin/src/lib.rs:12-173` exposes only `.flac` keys.

The distinction is important. `tools/ferrosintesis-samples/prepare.py:1228-1245`
deliberately preserves `family_NOTE_dyn.wav` as the logical recording name while mapping
the on-disk package name to `.flac`; the source-cut paths and checksum rows later in
`PROVENANCE.md` correctly remain WAV. The incorrect claim is specifically the physical
`samples/*.wav` package path. `tools/ferrosintesis-samples/gen_crate_lib.py:2` has the
same physical-input drift: its docstring says it generates from `samples/*.wav`, while
the implementation accepts both containers at `:106-111` and this crate contains only
FLAC.

Open `MM-BUG-CRUCIBLE-00044` covers stale `.wav` public lookup contracts and an explicit
list of other crate prose, but it calls mandolin's container-neutral `get()` documentation
correct and does not enumerate either path above. A blanket `.wav` replacement would be
wrong because the logical/source WAV names are intentional. Expected: published
provenance distinguishes logical/source WAV names from the physical FLAC bank. Actual:
it points readers at a retired physical path. Static review only; no generator, test,
build, decoder, package, app, render, or exploratory harness ran. Estimated effort:
Small.

## Fix

<unfixed — raised only>

Reword the baked-output sentence to say that logical WAV outputs are packaged under
`samples/*.flac`, and make the generator docstring container-neutral. Preserve the
raw-take, committed-source, and checksum-table `.wav` names. Any cross-crate documentation
oracle must distinguish logical/source names from physical package paths.

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `b8162d01`) by an agent other than the fixer.

**Original observation re-derived.** Mandolin `PROVENANCE.md:18-20` says the committed inputs are logical WAVs and the baked outputs are `samples/*.flac`; disk holds 40 `.flac` in `samples/` and 40 `.wav` in `mandolin-src/`. The `gen_crate_lib.py` docstring names both containers; the checksum-table `.wav` names are the unchanged inputs.

**Fails-before (method B).** Reversing the hunk fails `MandolinProvenanceContainerTest` ("'committed logical WAV inputs' not found"). Restored; passes on HEAD.

## Notes
