# MM-BUG-KILN-00275 — Zero Set-Tempo collapses the MIDI timeline and exposes infinite BPM

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis / SMF tempo validation
- **Raised:** 2026-08-17T09:41:26Z
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
- **State history:** Open (2026-08-17T09:41:26Z, raised via `deltic bugs new`)

## Observation

Observation: crates/ferrosintesis/src/midi.rs:358-362 accepts Set-Tempo payload 00 00 00 and stores us=0. The tempo-map arithmetic at :470-480 then uses zero seconds per tick, so every later event collapses onto one timestamp. The finite-duration guard at :502-507 passes, while Song::initial_bpm at :513 becomes positive infinity and is exposed by offline.rs:91-95.

Expected: reject a zero-microsecond tempo as malformed before it reaches the timeline and public BPM. Actual: parsing succeeds with collapsed timing and a non-finite public value.

Concrete fix: reject us == 0 while decoding Set-Tempo, return a specific malformed-tempo/header error, and add a regression with tick-separated note events plus an assertion that every successfully parsed Song exposes finite initial_bpm.

Static review only; no current ledger record covers zero Set-Tempo. Estimated effort: Small.

## Fix

<unfixed — raised only>

## Notes
