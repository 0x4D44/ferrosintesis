# MM-BUG-KILN-00028 — Channel-10 room-reverb send ignores authored CC91; a dry kit is unreachable from MIDI

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** engine
- **Raised:** 2026-07-20
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
- **State history:** Open (2026-07-20, raised from the GM instrument sweep audit — Claude Fable 5)

## Observation

The channel-10 drum room-reverb send is a fixed constant (`ROOM_SEND`,
`crates/ferrosintesis/src/engine.rs`, grep `ROOM_SEND`) applied unconditionally at
the drum mix points. An authored CC91 on channel 10 therefore cannot dry the kit —
a dry-drums bar is impossible from MIDI.

This runs against the crate's own controller doctrine ("an unauthored controller
is inert" — with the implied converse that an authored one works), which every
melodic channel honours via its CC91 reverb send. It also contradicts the
README's Controllers table, which documents CC91 as the reverb send with no
channel-10 carve-out.

## Fix

<unfixed — raised only>

Sketch: scale the room send by the channel's CC91 only when the channel has
authored CC91 (unauthored keeps today's fixed default — exact-render-preserving
for every existing file, per the opt-in controller policy). Any diff at all on
albums that never author ch-10 CC91 would be a bug (controller-feature rule).

## Notes

- Surfaced by the 2026-07-20 GM instrument sweep (drums auditor); also flagged as
  item 8 of the scratchpad README-contradiction entry (2026.07.12).
- The docs sweep of 2026-07-20 documents the current behaviour honestly in the
  README Controllers table; this bug tracks making the behaviour match the
  doctrine instead.
