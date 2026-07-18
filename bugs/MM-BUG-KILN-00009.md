# MM-BUG-KILN-00009 — Two sampled toms stretched across six GM keys thin the top of tom fills

- **State:** Open
- **Priority:** Could
- **Severity:** Medium
- **Area:** drums
- **Raised:** 2026-07-18
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit)

## Observation

The default sampled kit maps the six GM tom keys 45/47/48/50 onto two physical
tom recordings (`crates/ferrosintesis/src/sampler.rs:~1938`). `TOM_HI` has root
181 Hz (`sampler.rs:~1745`), so key 50 plays at 352/181 = 1.94× playback rate
(~+11.5 semitones) and key 48 at 1.62× (~+8.4 st). Large upward repitch shortens
decay and thins the shell body, so the top of a descending fill sounds
tight/chipmunk-ish rather than like a smaller drum with its own resonance. The
code comment at `sampler.rs:~1739` admits the mapping only "minimizes stretch."

## Fix

Add a third sampled source drum (a mid tom) to roughly halve worst-case stretch,
or cap the upward repitch so keys 48/50 are not driven ~1.6–1.9× off the 181 Hz
rack tom.

## Notes

- The modeled fallback already renders six distinct toms
  (`tom_ladder_is_six_distinct_drums`, `drums.rs:~2900`); this is a
  sampled-path-only deficiency.
- Adding a source drum is the larger option (new sample sourcing + level pin);
  the repitch cap is the cheap mitigation.
