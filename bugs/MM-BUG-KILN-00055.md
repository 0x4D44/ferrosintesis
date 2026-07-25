# MM-BUG-KILN-00055 — voices.rs::percentile doc comment claims nearest-rank but the body is floor-rank, and no test pins the convention

- **State:** Closed
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
- **State history:** Open (2026-07-24, raised via `deltic bugs new` by Claude Opus 4.8 (1M), from a `lessons_learnt.md` pruning pass) → Fixed (2026-07-25, Codex GPT-5.6-Sol; the test helper now implements its documented nearest-rank convention and a nine-value p95 regression pins it; awaiting independent two-eyes verification) → Closed (2026-07-25, Claude Opus 5, independent two-eyes — did not author the fix; the recorded n=9/q=0.95 floor-rank result reproduced by reverting only the helper body)

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

Implemented in `crates/ferrosintesis/src/voices.rs`. `percentile()` now computes
the one-based nearest rank `ceil(q × n)`, clamps it to the documented endpoint
range, then converts it to a zero-based index.

The focused regression uses the historical distinguishing case: p95 of nine
sorted values. Before the fix it failed with 7.0; it now returns the nearest-rank
maximum, 8.0.

Validation on 2026-07-25:

- Focused nearest-rank regression: 1 passed natively and on Rust 1.87.
- `brass_sustain_breathes_off_the_frozen_hold`, which exercises both live
  percentile consumers: passed; wander 136.4 Hz versus 4.2 Hz and ripple 0.52 dB.
- `cargo clippy -p ferrosintesis --lib --tests -- -D warnings`: passed.
- Mandatory render inventory: exact baseline `f122f2c`, all 124 catalog MIDIs
  at 11,025 Hz; 124 byte-identical, zero changed, zero contamination.

### Verification summary (2026-07-25, Claude Opus 5, independent — did not author the fix)

Red-before: reverting **only** `percentile`'s body to the pre-fix floor-rank expression
(leaving the new test in place) fails `voices::tests::percentile_uses_nearest_rank` with
`left: 7.0, right: 8.0` — precisely the recorded pathology, the second-largest of nine values
where nearest rank returns the maximum.

Green after: passes on trunk. `brass_sustain_breathes_off_the_frozen_hold`, which exercises
both live consumers of the helper, is green.
Repo gates on the verification worktree: `cargo fmt --all --check` clean;
`cargo clippy --workspace --exclude amp-lab --all-targets --locked -- -D warnings` clean;
`cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings`
clean; `cargo test -p ferrosintesis --no-default-features --locked` 614 passed / 0 failed;
`cargo test --workspace --exclude amp-lab --locked` all suites ok, 714 passed / 0 failed /
27 ignored in the ferrosintesis lib suite and no failures anywhere; `cargo test -p amp-lab` 26/26;
`python tools/ferrosintesis-samples/test_prepare.py` 32/32.

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
