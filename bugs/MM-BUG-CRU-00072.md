# MM-BUG-CRU-00072 — Catalog overlap audit's reset-sorts-first same-tick rule has no cross-track control

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** crates/render-catalog / MIDI overlap oracle tests
- **Raised:** 2026-09-13T19:32:32Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260914T213042Z-9cfc0b25
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00072-run-verify-20260914T213042Z-9cfc0b25
- **Owner base:** 23097e8da9523c8fc7d5062f044a9156d03844b6
- **Owner fingerprint:** sha256:02a12a5a97f6a40913e531466daf8acc75ff4dd94456eb68437528746cd89d17
- **Owner since:** 2026-09-14T21:30:42Z
- **Owner until:** 2026-09-14T23:30:42Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:32:32Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T21:53:18Z, deltic:auto role=fix run=fix-20260913T215005Z-786a2a87 branch=task/bug-MM-BUG-CRU-00072-run-fix-20260913T215005Z-786a2a87 code=984f2013061c25590e93bb843b9c6493bfe08d83 gate=manual)

## Observation

Found at independent verification of MM-BUG-CRUCIBLE-00034 (2026-09-13, trunk 8b6a6f86); that bug was closed concurrently by another verifier. Fix fe1fb49c makes the audit in crates/render-catalog/tests/album_midi_overlaps.rs sort a GM System On first among same-tick events, as midi.rs:603 does. Making that sort a no-op leaves all 12 committed tests green: the control gm_system_on_and_a_replacement_note_at_one_tick_is_not_an_overlap keeps reset and replacement note in one track, where file order already sorts them. A probe holding a note in track 1 and sending the reset in track 2 at the same tick as a replacement note in track 1 goes red (overlaps: 1) under the mutation and passes on HEAD. Expected: a committed cross-track same-tick control pins the ordering rule.

## Fix

<unfixed — raised only>

## Notes
