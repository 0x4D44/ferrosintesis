# MM-BUG-KILN-00059 — Realtime prewarm omits the Rhodes and dulcimer sample banks

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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol during the coverage-ledger review of `crates/ferrosintesis-samples-ccby/`)
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). The omission was **56 banks**, not 2 — see
  "Scope on investigation". Fixed with two derived oracles so the list cannot drift
  again. Awaits independent two-eyes closure.)
  → Closed (2026-07-24 — independent two-eyes verification by **Codex gpt-5.6-sol**,
  cross-family, read-only on post-fix trunk. Verdict: **CLOSE+SPLIT**. Verdict recorded by
  Claude Opus 4.8 (1M), which authored the fix and did NOT perform the verification.
  Confirmed: Rhodes, dulcimer and all 22 omitted public accessors are prewarmed, the
  measured 56 cold caches are gone, and an independent audio A/B found no render change.
  **Residual split to MM-BUG-KILN-00073:** the oracle enumerates only `pub fn *_bank`, so
  four realtime lazy caches are outside it — `bottle_loop_bank` and `chanter_rr2` (private
  fns), `rain_loop` (public but not `*_bank`), and `GONG_LAYERS` (an `OnceLock<(Vec<f32>,
  Vec<f32>)>`, which the `bank!` counter never sees). Each independently confirmed present
  and absent from `prewarm()`.)

## Observation

**Symptom.** Calling `RealtimeSynth::prewarm_samples()` does not initialize either
CC-BY attack bank. The first sampled GM 4 (Rhodes) or GM 15 (dulcimer) NoteOn therefore
decodes the bank and allocates its `Vec<Zone>` storage while the realtime renderer is
handling pending events inside `fill_ring()`.

**Expected.** `crates/ferrosintesis/src/live.rs:207-213` promises that
`prewarm_samples()` decodes lazy attack banks on the setup thread so first use cannot
blow the audio-callback deadline.

**Actual.** `crates/ferrosintesis/src/sampler.rs:2421-2469` calls neither
`rhodes_bank()` nor `dulcimer_bank()`. Those functions initialize `OnceLock<Vec<Zone>>`
at `sampler.rs:660-707`; the GM 4 and GM 15 voice constructors call them at
`voices.rs:12170-12182` and `:12415-12427`. `fill_ring()` handles the pending NoteOn
before rendering its deadline-bearing block at `live.rs:272-289`.

The deterministic first-use work is substantial:

- Rhodes: 11 WAVs, 440,462 decoded `f32` samples, 1,761,848 heap bytes.
- Dulcimer: 9 WAVs, 358,442 decoded `f32` samples, 1,433,768 heap bytes.

This review did not run the application or measure an xrun. The exact dropout duration
is unverified, but the callback work and violated prewarm contract are confirmed from
the call graph and asset headers.

## Fix

Add both banks to `sampler::prewarm()`. Replace or strengthen
`live.rs:885-888::sample_prewarm_is_available`, which currently proves only that the
call does not panic, with an oracle that proves every realtime-reachable lazy bank has
been initialized. Prefer a central registry shared by bank declaration and prewarming;
the hand-maintained prewarm list has other later-bank omissions and can recur.

## Notes

- No existing bug or open requirement matched this realtime-prewarm omission.
- The defect was independently confirmed by the performance lens, devil's advocate,
  and team lead. No source or tests were changed during review.

## Scope on investigation: 56 banks, not 2 (2026-07-24)

The report named the Rhodes and dulcimer banks. Comparing every `pub fn *_bank` in
`sampler.rs` against the calls in `prewarm()` showed **22 of the 46 public accessors**
were never touched — and because several fan out internally, the true count of
uninitialized banks is higher still. Measured, not estimated: with the original
`prewarm()`, the new oracle reports **56 sample banks** still decoding on first use.

The 22 missing accessors: every alternative piano bank (`grand`, `steinwayb`, `kawai`,
`headroom`, `musescoregrand`, `darkgrand`, `ydpgrand`, `honkytonk`), the saxophones,
the clavinet, the harpsichord, the celesta, the vibraphone, the tubular bells, the
music box, the dulcimer, the Rhodes, and the whole bass family (`pizzbass`,
`finger_bass`, `pick_bass`, `contrabass`, `cello`).

Each was individually confirmed to have real callers crate-wide, so all are genuinely
realtime-reachable. The reporter found the newest two entries in a list that had been
drifting for a long time — the same systemic shape as MM-BUG-KILN-00060, where the
attribution guide named 5 of 10 banks.

## Fix as landed

- `sampler::prewarm()` — now covers every accessor. Fan-out is handled by iterating the
  grid rather than picking one value: the piano-shaped banks select among six statics on
  `(velocity, round-robin)` and `sax_bank` among eight on `(program, velocity)`, so a
  single representative call leaves most of the bank set cold.
- `live.rs::prewarm_samples` — its doc now states the trade explicitly: it decodes
  *every* bank because a live stream can select any program or alternate bank at any
  moment, and that costs setup time and holds roughly twice the embedded sample payload
  resident. A caller who prefers occasional first-use stalls simply does not call it.
- Two oracles in `sampler.rs`, which together cannot be satisfied by a partial list:
  - `prewarm_leaves_no_bank_uninitialized` — calls `prewarm()`, snapshots a test-only
    `BANK_INITS` counter incremented inside the `bank!` macro, then sweeps every public
    accessor across its **full** argument space and asserts the count did not move.
  - `every_public_bank_accessor_is_exercised` — source-scans `sampler.rs` and asserts
    every `pub fn *_bank` appears in that sweep. Without it, adding a bank and
    forgetting the sweep would silently shrink what the first oracle covers, and it
    would keep passing while checking less.

**Why the counter is race-free** despite tests running in parallel: once `prewarm()`
returns, every bank it covers is initialized, so no later call from any thread can
increment it. `OnceLock::get_or_init` runs its closure exactly once, so a test that
raced ahead of `prewarm()` incremented *before* the snapshot.

**Fails-before / passes-after, observed:** with `prewarm()` reverted to its original
list, `prewarm_leaves_no_bank_uninitialized` fails with "**56 sample bank(s) were still
uninitialized after prewarm()**". After the fix both oracles pass.

**No audio change.** `prewarm` only pre-initializes `OnceLock`s and the counter is
`#[cfg(test)]`, so renders are bit-identical by construction. Confirmed by the full
`-p ferrosintesis` suite (641 passed, 0 failed), which includes the pinned render
hashes. `clippy -D warnings` and `fmt --check` clean.

**Not addressed here:** MM-BUG-KILN-00064 (GM 76's per-NoteOn loop search) shares this
bug's drifting-prewarm root cause but is not fixed by prewarming alone — it needs the
loop bounds cached. It also notes `prewarm()` points at the retired `bottle_bank()`
rather than `bottle_loop_bank()`; that is left to 00064, which owns the bottle path.

