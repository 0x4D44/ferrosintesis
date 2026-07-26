# MM-BUG-KILN-00127 — Sampled drum NoteOn allocates a filename and scans the bank

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sampler / realtime drum lookup
- **Raised:** 2026-07-26
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
- **State history:** Open (2026-07-26, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-drumkit/`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T075807Z-p50144-n860597800-c1 branch=task/bug-MM-BUG-KILN-00127-run-fix-20260726T075807Z-p50144-n860597800-c1 code=b4383169955c6be8db71fedb1416f918d2d425aa gate=manual) -> Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: deltic:auto role=fix), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree: `cargo fmt --all --check`, `clippy --workspace --exclude amp-lab --all-targets -D warnings`, `clippy -p ferrosintesis --no-default-features --all-targets -D warnings`, `test -p ferrosintesis --no-default-features --locked` (630 passed) and `test --workspace --exclude amp-lab --locked` (735 passed) - 1468 tests, 0 failures. Original observation re-run at source, and the fix proven non-vacuous by reverting it. `Bank::pcm()` is now `take_index(layer, rr)` arithmetic plus a direct `(self.source.pcm_by_index)(index)` lookup - no `format!` allocation and no linear scan on the NoteOn path - while `file_name()` and the name-keyed `pcm(name)`/`get(name)` remain for diagnostics exactly as the fix direction asked. `SampledDrum::new` needed no change; it already called `bank.pcm(layer, rr)`, which now takes the fast path. The real correctness risk in this change is a silent off-by-one swapping drum takes, and that is closed properly: `bank_take_indices_match_the_owning_inventory` walks EVERY bank x layer x round-robin in both asset crates and asserts `SAMPLES[take_index(l, rr)].0 == file_name(l, rr)` - i.e. the index resolves to the same file the old name lookup would have found - plus `ptr::eq` between the new fast path and `pcm_by_index`. The requested channel-10 regression exists as `sampled_drum_note_on_does_not_allocate_for_take_lookup`, which prewarms a real engine, sends 0x99/38/100 through the live command path and counts allocations with `rtalloc::measure`, asserting exactly the one engine-owned `Box<dyn Voice>`. To prove it sees the defect I reverted `Bank::pcm` to its pre-fix name-format-and-scan body: the oracle went red reporting FOUR allocations instead of one. Restored; `git status --porcelain` clean. NOTE ON GATE COVERAGE: this fix touches `crates/amp-lab`, which `.deltic-integrate.toml` deliberately excludes from both the clippy and test steps, so the integration gate alone would NOT have exercised the bug's own regression. I ran `cargo clippy -p amp-lab --all-targets --locked -- -D warnings` (clean) and `cargo test -p amp-lab --locked` (27 passed, 0 failed) separately, per the repo's documented convention for touching the lab.)

## Observation

Every sampled drum voice performs a name-based asset lookup on the realtime NoteOn
path, even after both PCM caches are initialized.

`Bank::pcm()` calls `Bank::file_name()` at
`crates/ferrosintesis-samples-drumkit/src/lib.rs:737-764`. `file_name()` uses
`format!` to allocate a new `String`. The core `pcm(name)` then scans up to all 140
entries to recover the index at
`crates/ferrosintesis-samples-drumkit/src/lib.rs:778-785`. Companion banks use the
same `Bank` method and then scan their own 48-entry table.

`SampledDrum::new` calls this path for every routed hit at
`crates/ferrosintesis/src/sampler.rs:4432-4457`. Live pending NoteOns are constructed
while `RealtimeSynth::fill_ring()` drains commands at
`crates/ferrosintesis/src/live.rs:292-304`, before the voice cap is enforced.

Expected: after setup and prewarming, selecting a known `(bank, layer, round-robin)`
take is direct bounded indexing with no temporary name allocation.

Actual: each sampled drum NoteOn allocates and frees a filename, then performs a
linear string search. A 128-hit burst therefore adds 128 temporary allocations and
up to 17,920 core-table comparisons before rendering. The operations are
source-confirmed; their wall time and audible effect are unmeasured.

## Fix

Give each `Bank` a direct mapping from `(layer, round-robin)` to its owning cache
index, and extend `BankSource` with an index-based PCM accessor. Keep `file_name()` for
diagnostics and tests, but remove it from voice construction.

Add a focused allocation/lookup regression for a prewarmed sampled-drum NoteOn.
The oracle must exercise a channel-10 sampled key; the existing amp-lab allocation
ratchet uses a melodic NoteOn and cannot see this path.

Estimated effort: Medium.

## Notes

Blocked bug `MM-BUG-KILN-00092` covers the engine-wide architectural cost of boxed
voice construction. This issue is deliberately separate: the filename allocation and
linear scan are local to sampled drums and can be removed without a voice-pool design.
