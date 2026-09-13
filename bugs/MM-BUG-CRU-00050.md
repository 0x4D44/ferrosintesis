# MM-BUG-CRU-00050 — Mandolin provenance still names a retired physical WAV package path

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** mandolin sample crate / packaged provenance
- **Raised:** 2026-08-20T12:21:24Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T194535Z-9d03e62f
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00050-run-verify-20260913T194535Z-9d03e62f
- **Owner base:** 43852a0fdc7072ac7dc7b39c18892473c525293c
- **Owner fingerprint:** sha256:e76e0b363711c0a15b667120c6beb86a07dcccc2f1fcbce8dca1d2f0e75d35d3
- **Owner since:** 2026-09-13T19:45:35Z
- **Owner until:** 2026-09-13T21:45:35Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-20T12:21:24Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:11:08Z, deltic:auto role=fix run=fix-20260913T150730Z-28f71eea branch=task/bug-MM-BUG-CRU-00050-run-fix-20260913T150730Z-28f71eea code=b8162d01134c9adc165374e1465b61cb32f34480 gate=manual)

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

## Notes
