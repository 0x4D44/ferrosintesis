# MM-BUG-KILN-00284 — Core drum-kit audio oracle omits 33 routed takes

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** core drum-kit sample crate / audio validation
- **Raised:** 2026-08-17T11:40:04Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260914T213534Z-79417402
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00284-run-verify-20260914T213534Z-79417402
- **Owner base:** 07b10bf8647927fa84fc40f754e36615f9c761d6
- **Owner fingerprint:** sha256:44a15d3310c1430c6ca5c1c3c30a8d16ed7223f9485f3b41061466089d9139e3
- **Owner since:** 2026-09-14T21:35:34Z
- **Owner until:** 2026-09-14T23:35:34Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T11:40:04Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T19:09:35Z, deltic:auto role=fix run=fix-20260913T185158Z-892715cf branch=task/bug-MM-BUG-KILN-00284-run-fix-20260913T185158Z-892715cf code=4687d7dc15d4b9c674243e3f9135e2bff8c7261b gate=manual)

## Observation

`crates/ferrosintesis-samples-drumkit/src/lib.rs:683-686` registers ten routed
banks, but `decoded_banks_are_valid_audio` at `:966-1000` applies duration, peak,
and RMS assertions to only seven. It omits `RIDE_BELL` (9 takes at `:603-610`),
`HH_OPEN` (12 takes at `:619-626`), and `HH_PEDAL` (12 takes at `:627-634`) — 33
routed files in total.

The mapping test at `:904-923` decodes those takes but proves only name/index and
pointer agreement. The inventory test at `:947-960` proves only aggregate bytes,
container magic, and self-lookup. A structurally valid FLAC containing silence,
bad normalization, or an implausible duration in any omitted bank can therefore
pass this crate's local quality oracles and reach ride-bell, open-hat, or
pedal-hat playback.

Expected: every public bank receives the same meaningful-signal and duration
validation. Actual: 33 takes have structural coverage only. No current bad take
was claimed, and no test or decoder ran; the false-green mutation follows directly
from the enumerated test table.

## Fix

<unfixed — raised only. Derive the quality sweep from `BANKS`, keep per-bank
duration bounds as data, and assert that the bounds table covers every registered
bank exactly once. Add a negative silent or badly normalized omitted-bank fixture.
Estimated effort: Small.>

## Notes
