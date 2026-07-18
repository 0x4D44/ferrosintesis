# MM-BUG-KILN-00009 — Two sampled toms stretched across six GM keys thin the top of tom fills

- **State:** Fixed
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit); Fixed (2026-07-18, `d3dd46b` — the bug's "add a third mid tom" premise proved unbuildable: no CC0 tom recording reaches GM's 293/352 Hz high toms (measured Virtuosity htom 176 Hz, Big Rusty ≤116, VCSL ≤111). So restore the thinned body rather than source a higher tom — `HybridTom` layers a modeled tom body under the sampled htom on keys 47/48/50, scaled by `HYBRID_TOM_MIX`. Keys 48/50: spectral centroid −10/−12% (less chipmunk), low-mid body +17/+21%, within the ±3 dB `sampled_drum_level_parity` guard (key 50 +2.46 dB). Regression `hybrid_tom_restores_body_on_stretched_high_toms`. render-diff 39 changed (albums using 47/48/50) / 0 contamination / 0 not-reached. Blend levels are a named constant for Arthur's audition.)

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
- 2026-07-18 hunt result (durable): NO CC0 tom recording reaches GM's high toms.
  Measured Virtuosity htom 176 Hz, Big Rusty tom_14/15/18/22 56–116 Hz, VCSL
  Tom1/Tom2/tenor 88–111 Hz — real toms cluster 90–180 Hz, GM keys 48/50 want
  293/352 Hz. The instruments that tune that high (rototoms/octobans) aren't in
  the curated CC0 libraries; Freesound has them but only via OAuth/lossy previews.
  Hence the model-under-sample body-restoration fix rather than a new asset.
