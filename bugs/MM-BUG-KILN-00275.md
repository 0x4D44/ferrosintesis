# MM-BUG-KILN-00275 — Zero Set-Tempo collapses the MIDI timeline and exposes infinite BPM

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis / SMF tempo validation
- **Raised:** 2026-08-17T09:41:26Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260913T174542Z-d74af8a3
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00275-run-fix-20260913T174542Z-d74af8a3
- **Owner base:** dfdbd903054f27af8fee34277c25017e1c6db941
- **Owner fingerprint:** -
- **Owner since:** 2026-09-13T17:45:42Z
- **Owner until:** 2026-09-13T19:45:42Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T09:41:26Z, raised via `deltic bugs new`)

## Observation

Observation: crates/ferrosintesis/src/midi.rs:358-362 accepts Set-Tempo payload 00 00 00 and stores us=0. The tempo-map arithmetic at :470-480 then uses zero seconds per tick, so every later event collapses onto one timestamp. The finite-duration guard at :502-507 passes, while Song::initial_bpm at :513 becomes positive infinity and is exposed by offline.rs:91-95.

Expected: reject a zero-microsecond tempo as malformed before it reaches the timeline and public BPM. Actual: parsing succeeds with collapsed timing and a non-finite public value.

Concrete fix: reject us == 0 while decoding Set-Tempo, return a specific malformed-tempo/header error, and add a regression with tick-separated note events plus an assertion that every successfully parsed Song exposes finite initial_bpm.

Static review only; no current ledger record covers zero Set-Tempo. Estimated effort: Small.

## Fix

<unfixed — raised only>

## Notes
