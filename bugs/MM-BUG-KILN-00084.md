# MM-BUG-KILN-00084 — amp-lab's peak meter misses peaks between UI polls

- **State:** Closed
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/amp-lab/`) → Fixed (2026-07-25, Codex GPT-5.6-Sol; callbacks now retain the interval maximum and the UI consumes it exactly once; awaiting independent two-eyes verification) → Closed (2026-07-25, Claude Opus 5, independent two-eyes — did not author the fix; the erased-transient symptom reproduced by restoring the pre-fix store)

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

### Verification summary (2026-07-25, Claude Opus 5, independent — did not author the fix)

Red-before: replacing `fetch_max` with the pre-fix `store` in `publish_peak` fails
`interval_peak_survives_quieter_callbacks_and_is_consumed_once` with `left: 7300,
right: 12500`. The 1.25 transient is erased by the later, quieter 0.73 callback — exactly the
documented symptom, that a peak between UI polls disappears and the clipping indicator misses
it.

Green after: the full `amp-lab` suite passes, 26/26.
Repo gates on the verification worktree: `cargo fmt --all --check` clean;
`cargo clippy --workspace --exclude amp-lab --all-targets --locked -- -D warnings` clean;
`cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings`
clean; `cargo test -p ferrosintesis --no-default-features --locked` 614 passed / 0 failed;
`cargo test --workspace --exclude amp-lab --locked` all suites ok, 714 passed / 0 failed /
27 ignored in the ferrosintesis lib suite and no failures anywhere; `cargo test -p amp-lab` 26/26;
`python tools/ferrosintesis-samples/test_prepare.py` 32/32.

## Notes

If last-block telemetry was intended, rename and document it. The current code
does not implement its explicit since-read contract.
