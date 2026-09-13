# MM-BUG-KILN-00275 — Zero Set-Tempo collapses the MIDI timeline and exposes infinite BPM

- **State:** Closed
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
- **State history:** Open (2026-08-17T09:41:26Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T18:11:51Z, deltic:auto role=fix run=fix-20260913T174542Z-d74af8a3 branch=task/bug-MM-BUG-KILN-00275-run-fix-20260913T174542Z-d74af8a3 code=43c67469bf9ae856a527ee29f8d2ecdd69828503 gate=manual) -> Closed (2026-09-13T19:21:20Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: zero Set-Tempo file rejected as InvalidTempo; regression fails on the non-finite BPM assertion with the check disabled)

## Observation

Observation: crates/ferrosintesis/src/midi.rs:358-362 accepts Set-Tempo payload 00 00 00 and stores us=0. The tempo-map arithmetic at :470-480 then uses zero seconds per tick, so every later event collapses onto one timestamp. The finite-duration guard at :502-507 passes, while Song::initial_bpm at :513 becomes positive infinity and is exposed by offline.rs:91-95.

Expected: reject a zero-microsecond tempo as malformed before it reaches the timeline and public BPM. Actual: parsing succeeds with collapsed timing and a non-finite public value.

Concrete fix: reject us == 0 while decoding Set-Tempo, return a specific malformed-tempo/header error, and add a regression with tick-separated note events plus an assertion that every successfully parsed Song exposes finite initial_bpm.

Static review only; no current ledger record covers zero Set-Tempo. Estimated effort: Small.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `43c67469`) by an agent other than the fixer.

**Original observation re-run.** A file with Set-Tempo `00 00 00` and notes 480 ticks apart is rejected by the CLI: "invalid Set-Tempo value 0: microseconds per quarter note must be non-zero".

**Fails-before (method B).** Disabling the `us == 0` check fails `zero_set_tempo_is_rejected_before_tempo_map_arithmetic` with "accepted zero Set-Tempo exposed non-finite initial BPM: inf", the recorded symptom. Restored; `git diff` empty; it and the `InvalidTempo` robustness case pass on HEAD.

**Gates.** This fix causes no gate failure; trunk `8b6a6f86` is red for unrelated recorded reasons.


## Notes
