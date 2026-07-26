# MM-BUG-KILN-00119 — calmeter's do-not-reuse note describes percentile's OLD floor-rank body; KILN-00055 inverted it

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** docs / ferrosintesis-cli examples
- **Raised:** 2026-07-25
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, raised via `deltic bugs new` model=claude-opus-5@high) → Fixed (2026-07-26, GPT-5.6 Codex on KILN-Windows — rewrote the do-not-reuse rationale for the current nearest-rank helper)

## Observation

**Symptom.** `crates/ferrosintesis-cli/examples/calmeter.rs:21-24` states, in the present
tense and as fact, that `voices.rs::percentile`'s "body is `sorted[floor(q * (len - 1))]`,
which at n = 9 returns the SECOND-largest block". Since MM-BUG-KILN-00055's fix (`b8f8247`)
that is **false, and inverted** — the body is now true nearest-rank:

```rust
// crates/ferrosintesis/src/voices.rs
fn percentile(sorted: &[f32], q: f32) -> f32 {
    let rank = (q * sorted.len() as f32).ceil() as usize;
    sorted[rank.clamp(1, sorted.len()) - 1]
}
```

and `voices::tests::percentile_uses_nearest_rank` pins p95 of nine values at the **maximum**
(8.0), which is precisely the statistic calmeter's own point 1 says it wants ("Nearest-rank
p95 happens to equal the max at n <= 19").

**Why it matters more than a stale comment.** `lessons_learnt.md` signposts
`calmeter.rs:21-24` as the authority on this convention, so the falsehood sits directly on the
path the next reader is sent down — and it is inverted rather than merely out of date, so a
reader who trusts it will reach the opposite conclusion about what the helper does.

**Expected.** The note describes the helper's current nearest-rank body, or stops describing
the body at all.

**Actual.** It describes the pre-`b8f8247` floor-rank body as current.

**Reproduce.** Read `crates/ferrosintesis-cli/examples/calmeter.rs:21-24` against
`crates/ferrosintesis/src/voices.rs`'s `percentile` on any commit at or after `b8f8247`.
Confirmed by reading both at `6c4c21e`; no build needed.

## Fix

The example keeps its explicit-maximum rule but now describes the helper's
current nearest-rank behavior. It explains that p95 equals the maximum for nine
blocks only by coincidence, stops doing so at twenty blocks, and would couple
the intended calibration statistic to window-derived block count. The measured
error from the former floor-rank implementation remains clearly historical.

## Verification — 2026-07-26

- `ferrosintesis-cli`'s `calmeter` example compiles.
- The focused nearest-rank regression still passes and returns 8.0 for p95 of
  nine sorted values.
- Formatting and `git diff --check` passed.

## Notes

- **Keep the "do not reuse" advice — only its justification is falsified.** The surviving
  reason is point 1's design argument: calmeter wants a *maximum* over ~9 blocks, and a
  percentile is the wrong statistic regardless of which rank convention it uses. Deleting the
  advice along with the false sentence would be an over-correction.
- **Scope is one sentence.** No shipped audio is affected; `calmeter` is a dev-only
  calibration example and `percentile` is inside `#[cfg(test)]`.
- **Leave the journal alone.** `wrk_journals/2026.07.21 - JRN - M-CAL foundation proven.md:49-50`
  repeats the same claim, but it is correctly dated, immutable history of what was true then.
- **Provenance.** Surfaced by the independent two-eyes verification of MM-BUG-KILN-00055 on
  2026-07-25, as a residual the fix created in a file the fixer had a direct pointer to. 00055
  itself is correctly Closed: its root cause was the helper's own doc comment at
  `voices.rs:20329-20332`, which the fix addressed at the right layer.
- **Same defect class as 00055 itself** — a misleading comment about this exact helper —
  which is why it is filed at the same Could/Low weight rather than absorbed as a note.
