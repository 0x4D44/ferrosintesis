# MM-BUG-CRU-00072 — Catalog overlap audit's reset-sorts-first same-tick rule has no cross-track control

- **State:** Closed
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
- **State history:** Open (2026-09-13T19:32:32Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T21:53:18Z, deltic:auto role=fix run=fix-20260913T215005Z-786a2a87 branch=task/bug-MM-BUG-CRU-00072-run-fix-20260913T215005Z-786a2a87 code=984f2013061c25590e93bb843b9c6493bfe08d83 gate=manual) -> Closed (2026-09-14T21:41:42Z, independent verify by Claude Opus 5 on trunk 1d87b00f: the new cross-track same-tick control passes and goes red (overlaps 1) when the reset-first sort key is disabled)

## Observation

Found at independent verification of MM-BUG-CRUCIBLE-00034 (2026-09-13, trunk 8b6a6f86); that bug was closed concurrently by another verifier. Fix fe1fb49c makes the audit in crates/render-catalog/tests/album_midi_overlaps.rs sort a GM System On first among same-tick events, as midi.rs:603 does. Making that sort a no-op leaves all 12 committed tests green: the control gm_system_on_and_a_replacement_note_at_one_tick_is_not_an_overlap keeps reset and replacement note in one track, where file order already sorts them. A probe holding a note in track 1 and sending the reset in track 2 at the same tick as a replacement note in track 1 goes red (overlaps: 1) under the mutation and passes on HEAD. Expected: a committed cross-track same-tick control pins the ordering rule.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` (fix `984f2013`) by an agent other than the fixer.

**Original observation.** The recorded gap was that disabling the reset-sorts-first rule left all controls green. `controls::gm_system_on_precedes_same_tick_replacement_across_tracks` now holds the note in one track and sends the GM System On from a second track at the replacement note's tick, which is the probe the observation described. It passes in `cargo test --workspace --all-targets --locked`.

**Fails-before (method B, on the rule the test guards).** Replacing `!matches!(event.kind, NoteKind::Reset)` in the `sort_by_key` tuple of `album_midi_overlaps.rs` with `true` fails the new control: left `NoteAudit { overlaps: 1, .. }`, right `overlaps: 0`. The 11 other controls stay green under that mutation, which confirms the new control is the only one pinning the rule. Restored.

**Repo gate on `1d87b00f`.** Green: fmt, all three clippy steps, `cargo test -p ferrosintesis-cli --no-default-features`, and `cargo test --workspace --all-targets`. Red, not caused by this fix: `cargo test -p ferrosintesis --no-default-features` fails `no_default_gate_is_paired_with_embedded_sample_coverage` (MM-BUG-KILN-00301 reopened), and 4 `test_prepare.py` tests error (MM-BUG-CRU-00068 reopened).

## Notes
