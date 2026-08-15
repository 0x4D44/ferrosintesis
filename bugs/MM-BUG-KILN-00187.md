# MM-BUG-KILN-00187 — MuseScore-grand standalone NOTICE assigns the bank to GM0

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** MuseScore grand sample package / routing documentation
- **Raised:** 2026-08-13T21:20:10Z
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
- **State history:** Open (2026-08-13T21:20:10Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-08-15T15:27:33Z, deltic:auto role=fix run=fix-20260815T152256Z-p32100-n802301500-c1 branch=task/bug-MM-BUG-KILN-00187-run-fix-20260815T152256Z-p32100-n802301500-c1 code=94ffc27 gate=manual)

## Observation

Static review found that crates/ferrosintesis-samples-musescore-grand/NOTICE lines 16-18 call the bank GM 0 / Bright Acoustic Piano alternate use. The shipping router and every other package surface place it at GM program 1 Bright Acoustic Piano, CC0=2: crates/ferrosintesis/src/altbank.rs lines 1041-1064 and crates/ferrosintesis/src/sampler.rs lines 1533-1537. A standalone package consumer therefore receives the wrong program identity in its legal notice. Closed MM-BUG-KILN-00149 corrected the parent README and NOTICE, but its derived guard checks package module docs, manifest, README, and provenance, not the standalone package NOTICE, so this residual stayed green. Expected: the NOTICE says GM 1 Bright Acoustic Piano alternate, CC0=2, consistently with runtime routing. Actual: it says GM 0. Fix the wording and extend the source-derived GM1 package-document guard to cover NOTICE, with a negative control restoring the exact stale phrase. Static review only; no build, test, app, render, generator, or exploratory harness ran.

## Fix

<unfixed — raised only>

## Notes
