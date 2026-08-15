# MM-BUG-KILN-00190 — MuseScore sample regeneration rewrites the separate bottle bank

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** MuseScore sample package / regeneration scope
- **Raised:** 2026-08-13T22:31:45Z
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
- **State history:** Open (2026-08-13T22:31:45Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-08-15T15:34:36Z, deltic:auto role=fix run=fix-20260815T152809Z-p11220-n214089500-c1 branch=task/bug-MM-BUG-KILN-00190-run-fix-20260815T152809Z-p11220-n214089500-c1 code=1ceb2bc gate=manual)

## Observation

Static review of crates/ferrosintesis-samples-musescore/PROVENANCE.md line 7 found that the documented crate regeneration command includes --only=bottle. In tools/ferrosintesis-samples/prepare.py, bottle is one global family selector: _bake_selected_local_banks calls bake_bottle_loop for that selector at lines 5377-5385 and main always invokes it at lines 5685-5687, while the MuseScore onset loop separately calls _bake_sf_onset for bottle_C6.wav at lines 5581-5587. Expected: following this independently published crate provenance recipe regenerates this crate or explicitly states every other tracked package it changes. Actual: the command also rewrites crates/ferrosintesis-samples-bottle/samples/bottleloop_G3.wav, a separately sourced active whole-voice bank. Fix by adding a package-scoped selector or splitting the retired onset selector from the active bottle family; update the packaged recipe and add a static routing test proving the command touches only its declared output crate. Static source review only; no generator, app, test, build, render, network, or exploratory harness ran.

## Fix

<unfixed — raised only>

## Notes
