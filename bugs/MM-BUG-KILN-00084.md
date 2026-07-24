# MM-BUG-KILN-00084 — amp-lab's peak meter misses peaks between UI polls

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** amp-lab / telemetry
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/amp-lab/`)

## Observation

`Meters::peak_x1e4` is documented as the peak “since the last read”
(`crates/amp-lab/src/audio.rs:18-24`). Each audio callback instead overwrites it
with only that callback's peak (`audio.rs:129-144`), while the UI loads it about
every 100 ms (`crates/amp-lab/src/main.rs:105-106` and `:262-275`).

Expected: any peak between UI reads remains visible at the next poll. Actual: a
later quieter callback erases it, so the red clipping indicator can miss short
transients. This is diagnostic-only but matters while choosing amp defaults,
because Drive changes level.

## Fix

Accumulate with an atomic maximum in the callback and have the UI consume/reset
the interval using `swap(0, ...)`. Add a deterministic test that publishes a
high peak followed by quieter callbacks before one UI read, then proves the high
peak is returned exactly once.

## Notes

If last-block telemetry was intended, rename and document it. The current code
does not implement its explicit since-read contract.
