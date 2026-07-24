# MM-BUG-KILN-00064 — GM76 searches 67 million sample points for every NoteOn inside the realtime callback

- **State:** Open
- **Priority:** Should
- **Severity:** High
- **Area:** sampler / realtime
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol during the coverage-ledger review of `crates/ferrosintesis-samples-bottle/`)

## Observation

**Symptom.** Every samples-enabled GM 76 NoteOn calls `find_bottle_loop()` while
constructing `BottleLoopVoice`. The selected loop is deterministic for the one static
sample, but its bounds are not cached. Notes outside the accepted pitch range also run
the full search before the ratio check rejects the sample and falls back to the model.

**Expected.** A NoteOn should do bounded voice setup. After
`RealtimeSynth::prewarm_samples()`, it should not decode a sample or search static PCM
inside the deadline-bearing render callback.

**Actual.** `D:\worktrees\midi-music\20260724-REV-CLA@KILN-code-review-065916\crates\ferrosintesis\src\sampler.rs:3308-3367`
tests 764 start positions and 20 candidate lengths per start. For the committed
72,765-frame WAV, `imbalance()` performs exactly 67,384,800 `x*x` sample
accumulations and 30,560 square roots per NoteOn. The call occurs at
`D:\worktrees\midi-music\20260724-REV-CLA@KILN-code-review-065916\crates\ferrosintesis\src\sampler.rs:3407`,
before the pitch-range rejection at lines 3408-3410.

The realtime path constructs every pending voice inside `fill_ring()` at
`D:\worktrees\midi-music\20260724-REV-CLA@KILN-code-review-065916\crates\ferrosintesis\src\live.rs:272-284`
and enforces its voice cap only afterwards. A burst of GM 76 NoteOns therefore
multiplies the search cost even when voice stealing will immediately discard voices.

Prewarming is also pointed at the retired onset bank:
`D:\worktrees\midi-music\20260724-REV-CLA@KILN-code-review-065916\crates\ferrosintesis\src\sampler.rs:2464`
calls `bottle_bank()`, while the active whole-voice route uses `bottle_loop_bank()`.
The first sampled NoteOn additionally parses the 145,574-byte WAV and allocates
291,060 bytes of decoded `f32` PCM despite the promise at
`D:\worktrees\midi-music\20260724-REV-CLA@KILN-code-review-065916\crates\ferrosintesis\src\live.rs:207-213`.

This pass did not run a timing probe or the application. Exact callback time and
dropout duration are unverified; the deterministic callback work and contract breach
are source-confirmed.

## Fix

Check the pitch ratio before loop discovery. Cache the decoded zone and validated
`(loop_start, loop_end)` together in one `OnceLock`, and make
`BottleLoopVoice::new()` consume those cached bounds. Initialize that same cache from
`sampler::prewarm()`.

Replace `live.rs::sample_prewarm_is_available`, which currently only proves the call
does not panic, with an oracle that proves a post-prewarm GM 76 NoteOn performs no
decode, allocation, or loop search. Include an out-of-window key so fallback cannot
hide the construction cost.

## Notes

- Open bug `MM-BUG-KILN-00059` covers the same drifting prewarm-list root cause for
  Rhodes and dulcimer. This bug is not a duplicate: prewarming alone cannot remove
  GM 76's repeated 67-million-operation construction search.
- Correctness, performance, test-coverage, reliability, devil's-advocate, and
  team-lead source passes independently confirmed the call graph.

