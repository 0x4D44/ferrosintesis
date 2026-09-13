# MM-BUG-CRU-00072 — Catalog overlap audit's reset-sorts-first same-tick rule has no cross-track control

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** crates/render-catalog / MIDI overlap oracle tests
- **Raised:** 2026-09-13T19:32:32Z
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
- **State history:** Open (2026-09-13T19:32:32Z, raised via `deltic bugs new` model=claude-opus-5)

## Observation

Found at independent verification of MM-BUG-CRUCIBLE-00034 (2026-09-13, trunk 8b6a6f86); that bug was closed concurrently by another verifier. Fix fe1fb49c makes the audit in crates/render-catalog/tests/album_midi_overlaps.rs sort a GM System On first among same-tick events, as midi.rs:603 does. Making that sort a no-op leaves all 12 committed tests green: the control gm_system_on_and_a_replacement_note_at_one_tick_is_not_an_overlap keeps reset and replacement note in one track, where file order already sorts them. A probe holding a note in track 1 and sending the reset in track 2 at the same tick as a replacement note in track 1 goes red (overlaps: 1) under the mutation and passes on HEAD. Expected: a committed cross-track same-tick control pins the ordering rule.

## Fix

<unfixed — raised only>

## Notes
