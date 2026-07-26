# MM-BUG-KILN-00146 — GM42 cello keys 74/76 lock an octave up at high bow force, and the wolf gate's seeds could not see it

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** voices / BowedString
- **Raised:** 2026-07-26
- **Owner:** deltic:gpt-5.5
- **Owner role:** fix
- **Owner run:** fix-20260726T232502Z-p9812-n299435500-c21
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00146-run-fix-20260726T232502Z-p9812-n299435500-c21
- **Owner base:** ebc1dda32db951d19e3b7cc4ee53e767f411dcea
- **Owner fingerprint:** -
- **Owner since:** 2026-07-26T23:25:02Z
- **Owner until:** 2026-07-27T00:10:02Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=claude-opus-4.6@high)

## Observation

Two coupled defects, both pre-existing, both fixed on the branch below but NOT independently verified — raised so the two-eyes rule applies rather than self-closing them.

**1. The defect.** `BowedString` GM 42 (cello) loses its fundamental at keys 74 (D5) and 76 (E5) whenever the per-note bow force draws near the top of its range, locking an octave up at +1203 cents with the level down ~60%. Bow force is drawn per note from 2.2-2.9, so this hits roughly one note in eight at those pitches — the top two tones of the cello's range.

Root cause: bowing hard in a SHORT loop drives the waveguide off its fundamental. Same failure family as the known 46-50 wolf band (MM-BUG-KILN-00012), at the other end of the register.

**2. Why nobody saw it.** `bowed_string_wolf_band_holds_fundamental` asserts that 'every per-note seed must settle onto the requested fundamental', using seeds 7/17/23. All three are small, and `Rng::new` (crates/ferrosintesis/src/dsp.rs) seeds xorshift32 raw — its first output from a small seed is ~= -1.0, so `u = white()*0.5+0.5` ~= 0.0 and bow force collapses onto 2.2003..2.2010 out of 2.2-2.9. The gate tested ONE bow force three times, on the single axis this waveguide fails on.

The engine is unaffected: it hands out `0xBA60 ^ (index * 2654435761)` (crates/ferrosintesis/src/engine.rs:2207), a Knuth hash whose outputs are well spread, so real playback genuinely varies bow force. The gates were weaker than production, not stricter.

**Fix on branch** `task/20260726-TSK-HUM-spike-bowedstring-in-fiddle-register-key`: a bow-force ceiling over the cello's top few semitones (its `beta` cannot move — 0.140 is what holds its own 46-50 band), plus five per-program register gates (`bowed_string_{violin,viola,cello,contrabass,fiddle}_holds_register`) that use the engine's seed formula and let `slope` draw naturally, and `calibrate_register_gate_catches_the_known_wolf` which asserts each lever fails when removed.

**To verify independently:** check out the branch and run `cargo test -p ferrosintesis --release bowed_string_cello_holds_register`; then revert the `slope_hi`/`slope_hi_key`/`top_key` fields on the CELLO voicing in `string_voicing` (crates/ferrosintesis/src/voices.rs) to no-ceiling and confirm it fails at keys 74 and 76.

## Fix

<unfixed — raised only>

## Notes
