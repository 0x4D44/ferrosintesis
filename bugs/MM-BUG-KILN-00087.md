# MM-BUG-KILN-00087 — Fast same-key bank switches retrigger the previous voice

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth / tremolo retrigger routing
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

**Symptom.** A bank change followed by the same key within the 100 ms tremolo
window can play the voice selected by the previous bank instead of the newly
selected voice.

The source-level reproduction is deterministic:

1. On a melodic channel, select GM program 25 with CC32 bank LSB 0 and send a
   NoteOn.
2. Select CC32 bank LSB 96, optionally repeat program 25 as a normal bank-select
   sequence, and send the same key 75 ms later.
3. `EngineCore::note_on` finds the existing steel-guitar `Active` voice and calls
   `retrigger()`. It returns before `make_variation(25, 96, ...)`, so the
   requested mandolin never spawns.

The reverse transition can replay a mandolin while base steel is selected.
The same identity gap applies to two nonzero CC0 alt banks: `Active` retains
`alt_bank_value`, but the retrigger predicate compares only the boolean `alt`.
A rapid melodic-to-XG-drum CC0 transition can also reach retrigger before
current drum routing is computed.

**Expected.** Program and bank changes affect future NoteOns. A fast repeat may
reuse a ringing voice only when its complete spawn-time routing identity matches
the currently selected routing.

**Actual.** `crates/ferrosintesis/src/engine.rs:2482-2501` matches only channel,
key, program, and the CC0-alt boolean. `Active` at
`crates/ferrosintesis/src/engine.rs:1833-1847` has no spawn-time `bank_lsb`, and
the predicate ignores its existing `alt_bank_value` and `is_drum` fields.

This review was source-only by contract; the application and tests were not
run.

## Fix

Represent the effective spawn-time voice/routing identity on `Active`, including
CC32 LSB, raw CC0 alternate-bank identity, and melodic/drum routing. Require
that identity to match the current strip before permitting a tremolo retrigger;
otherwise spawn the newly selected voice.

Add focused regressions for both steel↔mandolin directions, two distinct
nonzero CC0 banks, and melodic↔XG-drum routing inside the tremolo window. Also
pin that an unchanged bank still takes the existing retrigger path.

Estimated effort: Small–Medium.

## Notes

The tremolo-retrigger lookup predates the CC32 variation-voice implementation.
No existing bug entry covers bank identity at this early-return boundary.

