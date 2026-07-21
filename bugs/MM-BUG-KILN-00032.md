# MM-BUG-KILN-00032 — SMF tempo map: a first Set-Tempo after tick 0 mis-times every event before it (the default-120bpm prefix is never applied)

- **State:** Open
- **Priority:** Should
- **Severity:** High
- **Area:** parser
- **Raised:** 2026-07-21
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
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the cross-agent MIDI/GM support audit — found by gpt-5.6-sol-xhigh, corroborated by source read)

## Observation

`parse()` in `crates/ferrosintesis/src/midi.rs` builds the tick→seconds map from the
sorted tempo list but never prepends the SMF default tempo (120 bpm = 500 000 µs/quarter)
for the region before the first Set-Tempo event. The seconds accumulator seeds its rate
from `tempos[0]` **regardless of that entry's tick**:

- `let mut spt = tempos[0].1 as f64 / 1_000_000.0 / tpq;` (midi.rs:347) then the loop
  `sec += (tick - prev_tick) as f64 * spt` (midi.rs:349) times the span `[0, T)` with the
  first *authored* tempo instead of 120 bpm, whenever the first Set-Tempo is at tick `T > 0`.
- Worse, `to_sec(tick)` for any event before `T` binary-searches to `Err(0)`, uses
  `cum[0] = (T, …)`, and `tick.saturating_sub(T)` underflows to 0 (midi.rs:355-363) — so
  **every pre-tempo event collapses onto the single timestamp of the first tempo change**,
  not merely mis-rated.

Per SMF, 120 bpm applies until the first Set-Tempo. Files that place their initial tempo at
a nonzero delta (some DAW exports; conductor tracks with a pickup) are mis-timed before
synthesis begins. The common case — tempo at tick 0 — is unaffected. No in-repo album
triggers it (their Python builders emit the initial tempo at tick 0); the defect is audible
only on foreign GM files, consistent with ferrosintesis being a faithful generic GM player.

Repro (unit): a hand-assembled format-0 file with a Note-On at tick 0 and the first
Set-Tempo (e.g. 60 bpm) at tick 480, no tick-0 tempo. Expected: the note at t=0 s and the
480-tick point at 0.5 s (120 bpm default over the prefix). Actual: the prefix is timed at
60 bpm and the pre-tempo note collapses to the first-tempo timestamp.

## Fix

<to be filled by the fixer>

## Notes

- Surfaced by the gpt-5.6-sol-xhigh second opinion in the cross-agent audit; neither the
  original 14-agent workflow nor the Fable 5 review caught it — it lives in the parser's
  timing seam, which a per-subsystem feature census does not exercise.
- Parser-timing correctness, not a voicing issue.
