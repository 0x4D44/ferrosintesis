# MM-BUG-KILN-00008 — Electric snare (key 40) collapses onto the acoustic snare (key 38) in the default sampled kit

- **State:** Open
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit)

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
