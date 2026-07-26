# MM-BUG-KILN-00028 — Channel-10 room-reverb send ignores authored CC91; a dry kit is unreachable from MIDI

- **State:** Closed
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
- **State history:** Open (2026-07-20, raised from the GM instrument sweep audit — Claude Fable 5) → Fixed (2026-07-26, GPT-5.6 Codex on KILN-Windows — authored CC91 now controls each rhythm part's private drum-room send while an unauthored channel retains the exact historical default) → Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: GPT-5.6 Codex on KILN-Windows), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree at b0b93d9: `cargo fmt --all --check`, `clippy --workspace --exclude amp-lab --all-targets -D warnings`, `clippy -p ferrosintesis --no-default-features --all-targets -D warnings`, `test -p ferrosintesis --no-default-features --locked` (628 passed) and `test --workspace --exclude amp-lab --locked` (731 passed) - 1461 tests, 0 failures. Original observation re-run at source: `Strip::drum_room_send()` (`engine.rs:1607-1613`) returns the exact historical `ROOM_SEND` when CC91 is unauthored and `ROOM_SEND * reverb_send` once authored, so CC91=0 is fully dry - the unconditional constant the bug reported is gone. Four oracles green and mutually non-vacuous: `authored_cc91_zero_dries_the_channel_10_room` demands BIT-IDENTITY between drum-room-on and drum-room-off renders at CC91=0 (the strongest form of "exactly dry"); `drum_room_early_reflections` proves the room bus really does emit energy, so that bit-identity is a live constraint and not trivially satisfied, and that non-ch9 audio never leaks in; `authored_cc91_scales_the_drum_room_linearly` pins the unauthored default to exactly `ROOM_SEND` and linear scaling at 0/32/64/96/127; `authored_cc91_zero_dries_gs_and_xg_drum_rooms` covers the secondary rhythm parts. I also rendered a ch10 snare bar through the release CLI with and without an authored CC91=0; that end-to-end probe could NOT resolve the effect (hit-to-hit kit variation, up to 3.3 dB, swamps a 0.35-scaled early-reflection send), so I rely on the engine's exact A/B - which holds seed, round-robin and humanisation constant and is the sounder design - rather than on my own weaker measurement.)

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
