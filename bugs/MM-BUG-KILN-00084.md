# MM-BUG-KILN-00084 — amp-lab's peak meter misses peaks between UI polls

- **State:** Fixed
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/amp-lab/`) → Fixed (2026-07-25, Codex GPT-5.6-Sol; callbacks now retain the interval maximum and the UI consumes it exactly once; awaiting independent two-eyes verification)

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

Implemented in `crates/amp-lab/src/audio.rs` and `crates/amp-lab/src/main.rs`.
The audio callback now publishes through relaxed `AtomicU32::fetch_max`; the UI
consumes and resets the interval with `swap(0, Ordering::Relaxed)`. The atomic's
field is private so callers cannot accidentally restore last-block load/store
semantics.

The regression publishes 0.42, 1.25, then 0.73 before one read. It proves the
read returns 1.25 and the following read returns zero.

Validation on 2026-07-25:

- Focused interval peak regression: 1 passed.
- Full `amp-lab` suite: 26 passed.
- `cargo clippy -p amp-lab --all-targets -- -D warnings`: passed.
- Rust 1.87 probe: not runnable because the existing `image 0.25.10` dev-tool
  dependency requires Rust 1.88. The repository already excludes `amp-lab`
  from its Rust 1.87 integration component.

## Notes

If last-block telemetry was intended, rename and document it. The current code
does not implement its explicit since-read contract.
