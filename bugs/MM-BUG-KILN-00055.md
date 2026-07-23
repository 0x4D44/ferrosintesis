# MM-BUG-KILN-00055 — voices.rs::percentile doc comment claims nearest-rank but the body is floor-rank, and no test pins the convention

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** synth
- **Raised:** 2026-07-24
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
- **State history:** Open (2026-07-24, raised via `deltic bugs new` by Claude Opus 4.8 (1M), from a `lessons_learnt.md` pruning pass — filing the still-armed trap the earlier incident documented but never disarmed)

## Observation

**Symptom.** The test-only helper `percentile` documents nearest-rank semantics but its body
computes floor-rank, and no test anywhere pins the convention. The misleading comment is the
trap: it already cost a downstream consumer real error, yet it survived that incident intact
and is still there for the next reuser.

`crates/ferrosintesis/src/voices.rs:20329-20332`:

```rust
/// Nearest-rank percentile of an ALREADY-SORTED slice (q in [0,1]).
fn percentile(sorted: &[f32], q: f32) -> f32 {
    sorted[((sorted.len() - 1) as f32 * q) as usize]
}
```

Two independent departures from nearest-rank: `(n-1)` vs `n`, and truncation vs rounding. At
n=9, q=0.95 it returns `sorted[floor(8·0.95)] = sorted[7]` (the second-largest); nearest-rank
returns `sorted[ceil(0.95·9)-1] = sorted[8]` (the max).

**Scope.** The helper is inside `#[cfg(test)] mod tests` (`voices.rs:12841`) — it never runs
in the shipped synth. Two live callers, both in that test module, both far from the n=9
pathology:
- `voices.rs:20345` (`centroid_wander_hz`), n=59 — benign; both sides of a differential use
  the same statistic.
- `voices.rs:20392` (`brass_sustain_breathes_off_the_frozen_hold`, `ripple_db`), n=47 — a
  mild real bias: the understated p95 makes the `ripple_db < 4.0` "not a tremolo" ceiling
  *easier* to pass than intended. Low risk at n=47, but directional, not cosmetic.

**No test pins the convention** — a workspace-wide grep finds nothing asserting `percentile`'s
output.

**Expected.** The comment matches the body (or the body matches the comment), and a one-line
unit test locks whichever convention is chosen.

## Fix

<unfixed — raised only>

## Notes

- **Word it as "misleading doc comment on a test helper", not "percentile is broken".**
  Shipped audio is unaffected; this is Could/Low.
- **This is a known, twice-documented trap, filed because the comment outlived the incident
  that exposed it.** `lessons_learnt.md` and `crates/ferrosintesis-cli/examples/calmeter.rs:21-24`
  both warn against reusing it in almost these words. The historical damage: a downstream
  instrument-balance calibration derivation absorbed median 0.41 dB / max 18.77 dB of
  trim-table error before the convention was caught (that consumer — `calmeter` — has since
  moved to max-momentary and no longer uses it).
- **Fix shape:** correct the comment to "lower-interpolated rank" (or fix the body to true
  nearest-rank: `sorted[((q * n).ceil() as usize).clamp(1, n) - 1]`) at `voices.rs:20329-20332`,
  and add a one-line unit test pinning the chosen convention so the trap cannot re-arm.
- If anyone is already editing `voices.rs`, this is cheap enough to fold into that change
  rather than run as a standalone task.
