# MM-BUG-KILN-00275 — Zero Set-Tempo collapses the MIDI timeline and exposes infinite BPM

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis / SMF tempo validation
- **Raised:** 2026-08-17T09:41:26Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T191322Z-0a011843
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00275-run-verify-20260913T191322Z-0a011843
- **Owner base:** e9df87ba07a46a59c6c5926381672e880debbd63
- **Owner fingerprint:** sha256:b49544a219f962b86cabb7c239edd19c28bd59e48ebbe40dc581c691dfe52be3
- **Owner since:** 2026-09-13T19:13:22Z
- **Owner until:** 2026-09-13T21:13:22Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T09:41:26Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T18:11:51Z, deltic:auto role=fix run=fix-20260913T174542Z-d74af8a3 branch=task/bug-MM-BUG-KILN-00275-run-fix-20260913T174542Z-d74af8a3 code=43c67469bf9ae856a527ee29f8d2ecdd69828503 gate=manual)

## Observation

Observation: crates/ferrosintesis/src/midi.rs:358-362 accepts Set-Tempo payload 00 00 00 and stores us=0. The tempo-map arithmetic at :470-480 then uses zero seconds per tick, so every later event collapses onto one timestamp. The finite-duration guard at :502-507 passes, while Song::initial_bpm at :513 becomes positive infinity and is exposed by offline.rs:91-95.

Expected: reject a zero-microsecond tempo as malformed before it reaches the timeline and public BPM. Actual: parsing succeeds with collapsed timing and a non-finite public value.

Concrete fix: reject us == 0 while decoding Set-Tempo, return a specific malformed-tempo/header error, and add a regression with tick-separated note events plus an assertion that every successfully parsed Song exposes finite initial_bpm.

Static review only; no current ledger record covers zero Set-Tempo. Estimated effort: Small.

## Fix

<unfixed — raised only>

## Notes
