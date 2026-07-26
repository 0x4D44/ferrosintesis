# MM-BUG-KILN-00127 — Sampled drum NoteOn allocates a filename and scans the bank

- **State:** Open
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
- **State history:** Open (2026-07-26, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-drumkit/`)

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
