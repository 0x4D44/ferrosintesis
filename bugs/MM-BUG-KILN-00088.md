# MM-BUG-KILN-00088 — Mandolin round-robin phase splits across engine spawns and voice retriggers

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth / mandolin round robin
- **Raised:** 2026-07-24
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-mandolin/`)

## Observation

**Symptom.** A mandolin phrase boundary can immediately replay a round-robin
take and break the recorded down/up pick order.

The source-level sequence is:

1. A fresh mandolin NoteOn consumes engine `pitched_rr == 0`, plays `rr1`, and
   advances the engine counter to 1.
2. A same-key NoteOn within 100 ms retriggers the existing `LaVoice`, which
   rotates its private index and plays `rr2`. The early return does not advance
   the engine counter.
3. After a gap longer than 100 ms, the next fresh voice consumes the still-1
   engine counter and plays `rr2` again.

The heard sequence is therefore take 0, take 1, take 1 rather than take 0,
take 1, take 2. Because the recorded takes encode alternating pick direction,
this gives down/up/up and repeats identical onset PCM at the phrase boundary.

There is a second manifestation of the same ownership defect.
`crates/ferrosintesis/src/engine.rs:2565-2587` advances `pitched_rr` for every
non-alt melodic spawn, not only mandolin. A base steel or unrelated LSB voice
on the same channel/key can therefore perturb the next mandolin take.

**Expected.** One bank-scoped source of truth advances exactly once for every
accepted mandolin stroke, including a fast retrigger, and unrelated voices do
not consume its phase.

**Actual.** Fresh spawns advance `pitched_rr` at
`crates/ferrosintesis/src/engine.rs:2567-2586`. Fast strokes return at
`crates/ferrosintesis/src/engine.rs:2491-2501` after advancing only
`LaVoice::rr` at `crates/ferrosintesis/src/sampler.rs:3377-3413`.

This review was source-only by contract; the application, tests, and audio were
not run.

## Fix

Make one bank-scoped strike phase authoritative. Advance it exactly once for
every mandolin stroke, whether the stroke spawns or successfully retriggers a
voice, and do not advance it for base/undefined/other variation voices.

Add an engine-level state oracle covering:

- fresh take 0 → fast retrigger take 1 → gap → fresh take 2;
- multiple fast strokes followed by a fresh phrase;
- base steel and unrelated LSB notes on the same channel/key before mandolin;
- counter wrap after take 3.

Estimated effort: Small–Medium.

## Notes

The existing sampler oracle proves strict rotation inside one continuously
retriggered `LaVoice`. It cannot see the hand-off back to the engine-owned
counter at a fresh-spawn boundary.

