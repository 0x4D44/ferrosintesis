# MM-BUG-CRUCIBLE-00025 — RealtimeSynth buffers an unbounded MIDI command burst before one audio block

- **State:** Fixed
- **Priority:** Should
- **Severity:** High
- **Area:** ferrosintesis / realtime MIDI queue
- **Raised:** 2026-08-14T11:47:06Z
- **Discovery source:** Agent
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
- **State history:** Open (2026-08-14T11:47:06Z, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh) -> Fixed (2026-08-15T04:07:51Z, deltic:auto role=fix run=fix-20260815T035517Z-p44240-n504663000-c1 branch=task/bug-MM-BUG-CRUCIBLE-00025-run-fix-20260815T035517Z-p44240-n504663000-c1 code=9d10dcd gate=manual)

## Observation

`RealtimeSynth::write_byte` promises to accept a raw MIDI stream whose commands take
effect in the next `render_add` block. The queue between those calls must therefore have
bounded storage and bounded audio-callback work.

At
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\live.rs:164`,
`pending` is a `Vec<LiveCommand>`. Construction reserves 128 entries at lines 188-193,
but every completed message still calls `Vec::push` at lines 472-485. No limit or
overflow policy exists. `fill_ring` drains the entire backlog at lines 295-305 before it
renders one 64-frame block. A caller can feed millions of valid controller messages such
as `B0 00 00` before calling `render_add`; memory grows with the burst and the next audio
callback processes every command. A NoteOn burst also creates every voice before the cap,
then `EngineCore::enforce_voice_cap` repeatedly scans and removes from a `Vec` at
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\engine.rs:2396`.

Expected: the public realtime surface has a fixed command budget and deterministic
overflow semantics. Actual: valid input can cause unbounded memory growth and an
unbounded callback stall. This is a public-library realtime reliability defect.

This is not a duplicate of MM-BUG-KILN-00082, which reserved initial capacity, or
MM-BUG-CRUCIBLE-00013, which bounded the amp-lab producer. Neither caps the library queue.

## Fix

Replace the growable pending backlog with fixed-capacity storage. Define whether excess
commands are coalesced, rejected, or dropped, and make overflow observable to the caller.
Bound commands applied per render block. Add a regression that feeds more than the budget
using non-voice commands and proves both storage and per-block work remain bounded; add a
NoteOn-burst case that cannot trigger quadratic cap enforcement. Estimated effort: Medium.

## Notes
