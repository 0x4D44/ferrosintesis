# MM-BUG-CRUCIBLE-00006 — Realtime voice buckets allocate above 64 same-channel voices

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / realtime renderer
- **Raised:** 2026-07-31
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260731T065132Z-p82136-n128071600-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00006-run-fix-20260731T065132Z-p82136-n128071600-c1
- **Owner base:** 4866778d4d0744daca4ad50d7fe0b941ffed72dc
- **Owner fingerprint:** -
- **Owner since:** 2026-07-31T06:51:32Z
- **Owner until:** 2026-07-31T08:51:32Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-31, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh)

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
