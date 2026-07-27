# MM-BUG-KILN-00147 — GM44 tremolo strings is the last bowed program on the saw voice, and has no sampled onset

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** voices / bowed strings
- **Raised:** 2026-07-26
- **Owner:** deltic:gpt-5.5
- **Owner role:** fix
- **Owner run:** fix-20260727T034803Z-p9812-n357621900-c48
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00147-run-fix-20260727T034803Z-p9812-n357621900-c48
- **Owner base:** d515a7c7531fdba19e8da84c3104ec69cb7bbeae
- **Owner fingerprint:** -
- **Owner since:** 2026-07-27T03:48:03Z
- **Owner until:** 2026-07-27T04:43:47Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=claude-opus-4.6@high)

## Observation

GM 40/41/110 moved to the `BowedString` waveguide on 2026-07-26, joining 42/43. GM 44 (tremolo strings) is now the ONLY bowed program still rendering as the saw-based `Bowed` voice, and the only bowed program with no LA sampled onset at all — see the bare `44 => Box::new(Bowed::new(44, ...))` arm in crates/ferrosintesis/src/voices.rs.

It was left behind deliberately, not overlooked. Migrating it is NOT a voicing-table entry like the other three were:

- Tremolo is rapid bow-DIRECTION change, so each stroke needs its own re-articulation in the waveguide — the stick-slip interaction re-established per stroke, not a gain LFO over a sustained tone. `Bowed` fakes it with amplitude modulation plus per-stroke jitter (the BOW_TREM_* constants).
- There is a design question to settle first: GM 44 is a SECTION sound ('Tremolo Strings'), so the solo-string waveguide may be the wrong target and an ensemble treatment may fit better. Decide that before implementing.

Impact is low. A census of every committed .mid on 2026-07-26 found no album or demo in the repo authoring GM 44, so nothing currently renders differently — this is about ferrosintesis being a faithful general GM player, which CLAUDE.md is explicit is the standard to judge it by ('never cull a feature just because no in-repo album uses it').

## Fix

<unfixed — raised only>

## Notes
