# MM-BUG-KILN-00259 — MuseScore sample regeneration leaves the embedded FLAC bank stale

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** MuseScore sample crate / deterministic regeneration
- **Raised:** 2026-08-17T03:29:03Z
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
- **State history:** Open (2026-08-17T03:29:03Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-09-13T14:21:50Z, deltic:auto role=fix run=fix-20260913T141756Z-302585e6 branch=task/bug-MM-BUG-KILN-00259-run-fix-20260913T141756Z-302585e6 code=55298fb16c0f370149bafafb7e518685cafa4443 gate=manual)

## Observation

The package publishes `python3 tools/ferrosintesis-samples/prepare.py --only=brasssection,sitar,panflute,bottle,shakuhachi,celesta` as its regeneration command at `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-040926\crates\ferrosintesis-samples-musescore\PROVENANCE.md:7`. `_bake_sf_onset` still validates and writes `<family>_*.wav` at `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-040926\tools\ferrosintesis-samples\prepare.py:4528` and line 4561, while the package embeds only 36 FLAC keys at `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-040926\crates\ferrosintesis-samples-musescore\src\lib.rs:18` and runtime requests those FLAC names at `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-040926\crates\ferrosintesis\src\sampler.rs:2188`, line 2663, and line 2856. The stale-output guard at `prepare.py:5402` examines only WAV names. Following the documented command therefore adds 36 unconsumed WAVs beside 36 unchanged FLACs, leaves playback on the stale FLAC bank, and makes `inventory_matches_packaged_samples` see 72 assets against `FILE_COUNT=36`. Expected: the scoped recipe replaces and verifies the exact final-format bank runtime consumes. Actual: it produces a second container set and never refreshes shipped bytes. Concrete fix: stage, encode, and verify the final FLAC bank, reject mixed containers before publication, replace the active bank, and refresh the generated inventory. Add a negative fixture starting from the current FLAC-only tree. Sibling stale-regeneration bugs cover other crates, not this package. Static review only; the command was not run. Estimated effort: Medium.

## Fix

<unfixed — raised only>

## Notes
