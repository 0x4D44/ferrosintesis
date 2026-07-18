# MM-BUG-KILN-00014 — Acoustic string section (48/49) collapses to a bare detuned-saw ensemble under --no-samples / default-features off

- **State:** Open
- **Priority:** Could
- **Severity:** Medium
- **Area:** voices
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

The string section (`fn strings`, `crates/ferrosintesis/src/voices.rs:~5684`)
returns a `SawStack`; the 48..=49 arm wraps `LA_STRINGS` (`voices.rs:~10967`) for
its onset. With samples off (`--no-samples`, or `default-features = false`) it
falls to the bare detuned-saw stack — one of the most-used orchestral programs
dropping to the weakest tier. The voices audit called this "the single biggest
realism gap in the core orchestral middle," because the section's credibility
currently depends on the LA onset.

## Fix

Raise the modeled-only floor: a bow-noise onset, more decorrelated layers, or a
richer partial treatment on the `strings` `SawStack`, so a samples-off build does
not collapse the section. (Not the sustained-sampler architecture — that is
onset-only-ceiling territory; this is about the modeled fallback.)

## Notes

- The shipped default renders with samples, so this bites only the samples-off
  build — lower priority than the default-path items, but a real floor gap for
  library consumers who build modeled-only.
- Choir/pad/organ "sameness" is a different, structural onset-only ceiling (a
  sample cannot fix a sustain) — not this bug.
