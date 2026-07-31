# MM-BUG-CRUCIBLE-00006 — Realtime voice buckets allocate above 64 same-channel voices

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / realtime renderer
- **Raised:** 2026-07-31
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
- **State history:** Open (2026-07-31, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh) -> Fixed (2026-07-31T07:25:23Z, deltic:auto role=fix run=fix-20260731T065132Z-p82136-n128071600-c1 branch=task/bug-MM-BUG-CRUCIBLE-00006-run-fix-20260731T065132Z-p82136-n128071600-c1 code=c439884297e9e388ae9da988ad253036bc245d2b gate=manual) -> Closed (2026-07-31, claude-opus-5; independent two-eyes verification on trunk `ddd71e6`. The fixer was `deltic:auto role=fix` with GPT-5.6 as the authoring model on `c439884`; I did not fix it. ORIGINAL OBSERVATION re-checked by measurement, not by reading: the regression the fix added, `realtime_bucket_reservation_covers_the_single_channel_voice_cap`, drives a real `RealtimeSynth` through `reserve_realtime_storage()` and then counts allocations inside `render_add` with the `rtalloc` global-allocator counter, comparing a crowded single-channel case against a matched control that spreads the same total polyphony across channels. TWO-SIDED: reverse-applying ONLY the `EngineCore::reserve_voices` hunk in `engine.rs` makes it FAIL with "same-channel voice 65 allocated 10 times versus the matched spread-channel control's 9" — one extra allocation, which is exactly the 64-capacity `voice_by_ch` bucket reallocating at the 65th same-channel voice, the number the report predicted. Restoring the hunk makes it pass, and the 128-voice case passes too, so the reservation now holds all the way to the live cap. The control-matched design matters: it isolates bucket growth from the per-key variation in voice-model allocation, so the test cannot pass by accident. COVERAGE CAVEAT recorded deliberately, and NOT a defect introduced by this fix: the regression lives in `crates/amp-lab/src/audio.rs`, and `amp-lab` left the workspace on 2026.07.26, so no step in `.deltic-integrate.toml` reaches it — `cargo test --workspace` does not run this guard. I ran it manually from `crates/amp-lab/` (1 passed). The allocation counter can only live where the `#[global_allocator]` lives, so this is a pre-existing structural property of where that harness sits, documented in CLAUDE.md, not a gap the fix created. Repo gate green on the exact tree: fmt, both clippy configurations with `-D warnings`, `cargo test -p ferrosintesis --no-default-features` (714 passed), `cargo test --workspace` (849 passed in the lib, 0 failures), and the Python sample-tool suite. No residual.)

## Observation

`EngineCore` creates each per-channel voice-index bucket with capacity 64 at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\engine.rs:2050-2059`
and
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\engine.rs:2156-2161`.
The comments claim these buckets keep the render path allocation-free.

The public setup method
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\live.rs:229-236`
reserves storage for the 128-voice live cap, but
`EngineCore::reserve_voices` at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\engine.rs:2383-2390`
reserves only `active`. It does not reserve `voice_by_ch`.

With 65 distinct held voices on one melodic channel, the live cap has not
fired. `rebuild_voice_buckets` at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\engine.rs:3365-3387`
pushes the 65th index into that channel's bucket and reallocates inside
`render_block_add`, despite setup having called `reserve_realtime_storage()`.

**Expected:** after the documented setup reservation, auxiliary voice storage
cannot grow anywhere within the deadline-bearing render callback up to the live
polyphony cap.

**Actual:** 65–128 same-channel voices grow a 64-capacity bucket during render.
This is a bounded but avoidable soft-realtime reliability defect that can cause
an audio dropout.

## Fix

Make realtime reservation cover every `voice_by_ch` bucket up to the live cap,
or size those buckets to that cap at construction. The extra worst-case
reservation is small: 16 channels × 128 `usize` indices.

Extend the allocation-counting callback oracle with 65–128 held voices on one
channel after `reserve_realtime_storage()`. Require zero bucket allocations.
The current `live_polyphony_is_capped` test queues enough voices to exercise
large buckets, but it measures only the final count.

## Notes

Static review only; the pass did not execute the application or tests.

This is distinct from `MM-BUG-KILN-00092`, which explicitly accepts the
architectural per-voice `Box` allocation pending measurement. It is a missed
`Vec` reservation in the setup-time remedy for `MM-BUG-KILN-00082`.

Reported in
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\wrk_docs\2026.07.31 - CR - 20260731-REV-CLA@CRUCIBLE-code-review-014814.md`.
