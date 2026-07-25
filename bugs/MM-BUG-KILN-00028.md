# MM-BUG-KILN-00028 — Channel-10 room-reverb send ignores authored CC91; a dry kit is unreachable from MIDI

- **State:** Fixed
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-20, raised from the GM instrument sweep audit — Claude Fable 5) → Fixed (2026-07-26, GPT-5.6 Codex on KILN-Windows — authored CC91 now controls each rhythm part's private drum-room send while an unauthored channel retains the exact historical default)

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

`Strip` now records whether CC91 was authored and exposes one
`drum_room_send()` policy: unauthored rhythm parts receive the exact historical
`ROOM_SEND`, while authored CC91 scales that default over the complete dry-to-room
range. Both channel 10 and GS/XG secondary rhythm parts use their own strip's
policy. CC121 preserves the authored value and marker with the other persistent
effect-send state.

## Verification

- Two fail-first dry-room tests proved channel 10 and the shared GS/XG secondary
  path still emitted private-room energy at CC91=0 before the fix.
- Focused tests prove CC91=0 is exactly dry, values 0/32/64/96/127 scale the room
  linearly, unauthored channel 10 retains the exact default, GS and XG parts use
  their own CC91, and CC121 preserves the authored state.
- The complete default suite passed (725 tests, 27 ignored), the complete
  model-only suite passed (624 tests, 22 ignored), and both doc-test sets passed
  (4 tests each).
- Strict workspace clippy passed with default and no-default features;
  formatting and `git diff --check` passed.
- The exact-base 124-MIDI render inventory at 11.025 kHz matched the controller
  census exactly: all 86 pieces that sound channel 10 and author its CC91
  changed, all other 38 stayed byte-identical, with zero contamination and zero
  missed paths. No catalog MIDI contains SysEx, so no GS/XG rhythm-part catalog
  case is hidden from that classification.

## Notes

- Surfaced by the 2026-07-20 GM instrument sweep (drums auditor); also flagged as
  item 8 of the scratchpad README-contradiction entry (2026.07.12).
- The docs sweep of 2026-07-20 documents the current behaviour honestly in the
  README Controllers table; this bug tracks making the behaviour match the
  doctrine instead.
