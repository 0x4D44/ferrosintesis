# MM-BUG-KILN-00008 — Electric snare (key 40) collapses onto the acoustic snare (key 38) in the default sampled kit

- **State:** Closed
- **Priority:** Should
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit); Fixed (2026-07-18, `d03e33d` — sampled electric snare (key 40) repitched 1.15× on the `SNARE` bank to match the modeled path's `center_mul 1.15`; +2.4 st, brighter/tighter. Regression `sampled_electric_snare_distinct_from_acoustic`: fail-first on bit-identity (both were `kit::SNARE`@1.0) + spectral centroid 2333 vs 2023 Hz. Level parity within 3 dB (`sampled_drum_level_parity`). render-diff over 109 album MIDIs: 4 changed (V3-kit key-40 albums), 0 contamination; 3 brush-kit albums (ch10 prog 40 → brush swirl) correctly unmoved.); Closed (2026-07-19, independent verification by a separate fresh-context agent — two-eyes, the fixer did not self-close. Passes-after: centroid 2333 vs 2023 Hz (electric brighter). Fails-before: reverting `ELECTRIC_SNARE_REPITCH`→1.0 makes key 40 render bit-identical to key 38, so the regression genuinely gates the fix. Fix is in the sampled path (the root cause); key 38 unchanged; key 40 level −0.64 dB (within ±3 dB); clippy `-D warnings` clean. Non-blocking note: the fix comment slightly overstates the `DRUM_LEVEL[40]` role — parity holds naturally from the repitch, no compensation entry was added.)

## Observation

In the default sampled drum path both key 38 (acoustic snare) and key 40
(electric snare) map to `kit::SNARE` at repitch 1.0
(`crates/ferrosintesis/src/sampler.rs:~1935`) with identical level 0.98
(`DRUM_LEVEL`, `sampler.rs:~1716`). The modeled path *does* differentiate them
(`drums.rs:~1551`, `center_mul 1.15` + `am_depth`), but that arm is unreachable
when samples are on — i.e. in the shipped default.

Expected: an album that uses key 40 as a contrasting backbeat hears a distinct
electric snare. Actual: it hears the same drum as key 38, differing only by
round-robin seed.

## Fix

Differentiate the sampled electric snare — a small upward repitch and/or a
brighter velocity-layer bias, or route it to a distinct articulation — restoring
in the default path the 38/40 distinction the modeled path already builds.

## Notes

- Cheap, high effort-to-payoff ratio (drums audit).
- Changes the sampled-drum render → render-diff inventory; expected diffs only on
  albums using key 40.
