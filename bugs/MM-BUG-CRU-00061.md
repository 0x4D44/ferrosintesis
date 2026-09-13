# MM-BUG-CRU-00061 — ffmpeg-prerequisite documentation tests pass on text that denies ffmpeg is needed

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample tooling / regeneration prerequisite oracles
- **Raised:** 2026-09-13T19:22:43Z
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
- **State history:** Open (2026-09-13T19:22:43Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T20:38:22Z, deltic:auto role=fix run=fix-20260913T202711Z-3a9994fe branch=task/bug-MM-BUG-CRU-00061-run-fix-20260913T202711Z-3a9994fe code=bf681a3f105cef44e82b767c99a4fd751b40cc2d gate=manual)

## Observation

Split at independent verification of MM-BUG-CRU-00047, MM-BUG-CRU-00051 and MM-BUG-CRU-00053 (2026-09-13, trunk 8b6a6f86). GrandRegenerationRecipeTest, KawaiPackagedDocumentContractTest and YdpPackagedDocumentContractTest only require 'ffmpeg' within ~80 characters of 'PATH'. Rewording the grand, Kawai or YDP README/PROVENANCE to 'does not need ffmpeg on PATH' / 'needs no ffmpeg on PATH' still passes, so the tests cannot tell a requirement from a denial. The CRU-00053 record asked for an oracle that rejects 'no ffmpeg' claims for every recipe reaching _require_ffmpeg(); the landed tests are per-crate and negation-blind.

## Fix

<unfixed — raised only>

## Notes
