# MM-BUG-KILN-00064 — GM76 searches 67 million sample points for every NoteOn inside the realtime callback

- **State:** Closed
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
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). Scope on investigation: **GM 64-67 sax has the
  same defect**, not just GM 76 — see "Scope on investigation". Memoized per zone, ratio
  checked first, both warmed by `prewarm()`; three oracles, two behavioural and one
  source-derived. Awaits independent two-eyes closure.)
  → Closed (2026-07-24, independently verified by Codex GPT-5.6-Sol; fails-before,
  passes-after, root-cause review, and green gate evidence are recorded in
  `wrk_journals/2026.07.24 - JRN - Fixed queue two-eyes closure pass.md`.)

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

## Scope on investigation

The report names GM 76. The defect is **two voices, one root cause**: `find_bottle_loop`
is documented as a copy of `find_sax_loop`, and `SaxLoopVoice::new` (GM 64-67) had the
identical shape — search first, cache never, pitch-ratio rejection second. Fixing only the
bottle would have left the sax paying the same per-NoteOn cost on four programs x two
velocity layers x every zone.

Measured by the new counter, per burst, before the fix:

| Voice | NoteOns | Loop searches |
|---|---|---|
| GM 76 bottle | 10 keys | 10 |
| GM 64-67 sax | 4 programs x 2 vels x 7 keys | 56 |

One search per NoteOn in both cases — the memo was simply absent. Each is an
O(starts x lengths x window) scan of static PCM (67.4 M multiply-accumulates for the
bottle's 72,765-frame recording).

## Resolution

`crates/ferrosintesis/src/sampler.rs`:

- `Zone` gains `sustain_loop: OnceLock<Option<(usize, usize)>>` and a memoizing
  `Zone::sustain_loop(LoopFinder)` accessor. The zone and its PCM are `'static` and
  immutable, so the loop bounds are a constant — computed once per zone, for the process.
  The "no usable loop" verdict is cached too, so a failing search does not repeat either.
- `SaxLoopVoice::new` and `BottleLoopVoice::new` now check the pitch ratio **first** and
  read the memo second. An out-of-window key falls back to the modeled voice without
  paying anything, which is what the original ordering got backwards.
- `prewarm()` resolves every sax and bottle zone's loop, so the work happens on the setup
  thread. It also now warms `bottle_loop_bank()` — the ACTIVE GM 76 route, which was
  missing while the retired `bottle_bank()` onset bank was warmed.

Three oracles, each proven to fail on the pre-fix tree before the fix was restored:

- `sampler::prewarm_leaves_no_sustain_loop_unsearched` — counts real searches during voice
  construction after `prewarm()`. Red at 10 (bottle) and 56 (sax); green at 0. Includes
  out-of-window keys, so the model fallback cannot hide the construction cost.
- `live::realtime_note_on_after_prewarm_does_no_decode_or_loop_search` — replaces the old
  `sample_prewarm_is_available`'s does-not-panic check with the actual contract, driven
  through `render_add` so the work is measured where the deadline is.
- `sampler::every_sustain_loop_search_is_memoized_and_prewarmed` — source-derived, per the
  CLAUDE.md convention. It enumerates every `find_*_loop` the file declares, then requires
  no call site bypasses the memo and `prewarm()` forces each. Named the exact bypass line
  in both fail-first runs. Without it, the behavioural oracle's hand-written voice list
  would silently shrink the moment a third looped voice landed.

The counter is incremented in each `find_*_loop` **body**, not at the memo, so a rewiring
that bypasses `Zone::sustain_loop` is still caught.

## Notes

- Open bug `MM-BUG-KILN-00059` covers the same drifting prewarm-list root cause for
  Rhodes and dulcimer. This bug is not a duplicate: prewarming alone cannot remove
  GM 76's repeated 67-million-operation construction search.
- Correctness, performance, test-coverage, reliability, devil's-advocate, and
  team-lead source passes independently confirmed the call graph.
- **For `MM-BUG-KILN-00073`, which lands second:** its `bottle_loop_bank` item is done —
  `prewarm()` now warms that bank and its zone loops. Its other three caches
  (`chanter_rr2`, `rain_loop`, `GONG_LAYERS`) and the oracle-predicate widening are
  untouched here and remain that bug's work.
- Timing was never measured, here or in the report. The claim proven is the deterministic
  one: **zero** searches and **zero** decodes during post-prewarm voice construction, down
  from one search per NoteOn. Wall-clock callback time remains unmeasured.

