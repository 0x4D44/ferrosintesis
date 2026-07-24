# MM-BUG-KILN-00087 — Fast same-key bank switches retrigger the previous voice

- **State:** Closed
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
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). The tremolo-restrike predicate now
  matches the voice’s COMPLETE spawn-time routing identity — program, CC0 alt bank and its
  raw value, CC32 bank LSB, and melodic/drum routing, with drum routing resolved before
  the predicate rather than after it. Four-transition regression added. Evidence under
  "Fix landed" below. Awaits independent two-eyes closure.)
  → Closed (2026-07-24, independently verified by Codex GPT-5.6-Sol; fails-before,
  passes-after, root-cause review, and green gate evidence are recorded in
  `wrk_journals/2026.07.24 - JRN - Fixed queue two-eyes closure pass.md`.)

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

## Fix landed (2026-07-24)

**Code** (`crates/ferrosintesis/src/engine.rs`). Two changes, both in `note_on`:

- `Active` gained a spawn-time `bank_lsb`, and the tremolo-restrike predicate now requires
  the ringing voice's COMPLETE routing identity to match the strip: program, `alt`, the raw
  `alt_bank_value` (1 legacy alt and 2 cathedral organ are different voices), `bank_lsb`,
  and melodic-vs-drum on both sides.
- `is_drum` is resolved BEFORE the restrike path instead of at spawn. That was the bug's
  second half: the predicate cannot compare against a value computed 60 lines later. The
  hoist is behaviour-neutral — nothing between the two positions mutates `xg_drum` /
  `gs_drum`.

**Regression** — `a_routing_change_inside_the_tremolo_window_spawns_the_new_voice`. It
drives `EngineCore` directly and observes whether a SECOND voice appears: a retrigger
re-excites the one ringing voice (`active.len() == 1`), a correct spawn leaves the old one
ringing and adds the new (`== 2`). Cases are COLLECTED rather than short-circuited, so a
partial fix cannot hide behind the first assertion. Four transitions, all four failing
before the fix and passing after:

```
4 routing change(s) re-picked the PREVIOUS bank's voice instead of spawning the newly
selected one - the requested voice never sounds:
  steel guitar -> mandolin (CC32 0 -> 96)
  mandolin -> steel guitar (CC32 96 -> 0)
  alt bank 1 -> alt bank 2 (both CC0 nonzero, on a plucked program)
  melodic -> XG drum part (CC0 -> 127)
```

Plus two clauses the fix could otherwise have broken silently: an UNCHANGED bank must
still take the retrigger path (or TREM1 is disabled and a fast figure is a click train
again), and the spawned voice must carry the newly selected `bank_lsb`, not the old one.

*Note on the alt-bank case:* the bug suggested GM 19 for it, which does NOT reproduce —
only `Pluck` implements `retrigger()`, so an organ falls through to a spawn anyway. The
case is real on a PLUCKED program, which is what the test uses.

**Blast radius — census, then render-diff.** The change can only alter output where a
same-key NoteOn follows within 100 ms AND the channel's bank changed in between. A parse
of all 141 committed `albums/**` + `demos/**` MIDIs (tempo-mapped to real seconds, tracking
CC0/CC32 per channel against each voice's spawn-time bank) finds **zero** such restrikes,
so no committed render can move. Confirmed empirically: both Hollow Hill parts, The Signal
Fire, and the two GM-96/FX demos render **byte-identical** against a baseline binary built
at `83082d2` — 5 of 5.

Seed accounting is unchanged either way: the retrigger path already consumed a seed slot,
and `seed` is derived after the restrike block, so a note switching from retrigger to spawn
cannot shift any later voice's seed.

**Gates.** `cargo test --release -p ferrosintesis` 658 passed / 0 failed / 26 ignored (+4
doc-tests); clippy `-D warnings` clean; `cargo fmt --check` clean.

## Notes

The tremolo-retrigger lookup predates the CC32 variation-voice implementation.
No existing bug entry covers bank identity at this early-return boundary.

