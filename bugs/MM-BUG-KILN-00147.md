# MM-BUG-KILN-00147 — GM44 tremolo strings is the last bowed program on the saw voice, and has no sampled onset

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** voices / bowed strings
- **Raised:** 2026-07-26
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
- **Held branch:** host-local:KILN:task/bug-MM-BUG-KILN-00147-run-fix-20260727T034803Z-p9812-n357621900-c48-code-1785124935354
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=claude-opus-4.6@high) -> Fixed (2026-07-27, deltic:auto role=fix run=fix-20260727T034803Z-p9812-n357621900-c48 branch=task/bug-MM-BUG-KILN-00147-run-fix-20260727T034803Z-p9812-n357621900-c48 code=1c801edef6dd gate=cargo model=codex@xhigh)

## Observation

GM 40/41/110 moved to the `BowedString` waveguide on 2026-07-26, joining 42/43. GM 44 (tremolo strings) is now the ONLY bowed program still rendering as the saw-based `Bowed` voice, and the only bowed program with no LA sampled onset at all — see the bare `44 => Box::new(Bowed::new(44, ...))` arm in crates/ferrosintesis/src/voices.rs.

It was left behind deliberately, not overlooked. Migrating it is NOT a voicing-table entry like the other three were:

- Tremolo is rapid bow-DIRECTION change, so each stroke needs its own re-articulation in the waveguide — the stick-slip interaction re-established per stroke, not a gain LFO over a sustained tone. `Bowed` fakes it with amplitude modulation plus per-stroke jitter (the BOW_TREM_* constants).
- There is a design question to settle first: GM 44 is a SECTION sound ('Tremolo Strings'), so the solo-string waveguide may be the wrong target and an ensemble treatment may fit better. Decide that before implementing.

Impact is low. A census of every committed .mid on 2026-07-26 found no album or demo in the repo authoring GM 44, so nothing currently renders differently — this is about ferrosintesis being a faithful general GM player, which CLAUDE.md is explicit is the standard to judge it by ('never cull a feature just because no in-repo album uses it').

## Fix

<unfixed — raised only>

### Fix summary (2026-07-27, deltic:auto run=fix-20260727T034803Z-p9812-n357621900-c48 code=1c801edef6dd gate=cargo)

Agent-reported summary: Fixed MM-BUG-KILN-00147 by moving GM44 Tremolo Strings off the legacy saw-based Bowed default path and onto the BowedString waveguide. The default GM44 path now uses the existing string-section LA onset bank, so samples-on differs from samples-off where embedded samples are available. The waveguide has a GM44-only tremolo path that flips bow direction, jitters stroke timing and gain, and re-establishes the scratch catch at each reversal instead of using a plain gain LFO. The GM44 velocity response changed with the waveguide migration, so the existing per-program velocity compensation table now includes GM44. The focused regression was made red before the fix by requiring GM44 to route as bow

Root cause: GM44 was left as a bare Bowed::new arm because the previous migration handled solo arco programs but did not add a tremolo-capable bowed-string default treatment or choose a section-appropriate sampled onset. That left Tremolo Strings as the only bowed default program still using the legacy saw-based voice and the only one without an LA sampled onset.

Changed:
- crates/ferrosintesis/src/voices.rs: GM44 default routing, BowedString tremolo stroke handling, LA routing table, velocity compensation, and bowed routing regres

Tests:
- cargo test -p ferrosintesis --lib voices::tests::default_bowed_articulations_and_sample_routing
- cargo test -p ferrosintesis --lib voices::tests::default_bowed_pitch_range_and_legato
- cargo test -p ferrosintesis --lib velocity_law::tests::every_gm_program_follows_the_square_law
- git diff --check

Left alone:
- bugs/ ledger files
- Cargo.toml and Cargo.lock
- broad integration gate and render-diff inventory for Deltic

## Notes
