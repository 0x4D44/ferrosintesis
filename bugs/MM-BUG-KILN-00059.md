# MM-BUG-KILN-00059 — Realtime prewarm omits the Rhodes and dulcimer sample banks

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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol during the coverage-ledger review of `crates/ferrosintesis-samples-ccby/`)

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

