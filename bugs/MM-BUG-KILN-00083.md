# MM-BUG-KILN-00083 — amp-lab silently drops authoritative UI commands when its ring fills

- **State:** Open
- **Priority:** Could
- **Severity:** Medium
- **Area:** amp-lab / command delivery
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/amp-lab/`)

## Observation

`Producer::push()` and `push_midi()` deliberately return `false` when the
4,095-entry queue lacks space (`crates/amp-lab/src/ring.rs:61-91`). Every UI
call site ignores that result: full-rig and knob delivery
(`crates/amp-lab/src/main.rs:75-85`), play (`:222`), solo (`:226`), and panic
(`:229`).

If the audio callback stalls or stops draining while the user continues
interacting, the UI commits the new state even when its authoritative command
was discarded. An A/B recall on the same voice sends six independent packets
(`main.rs:94-100`), so a nearly full ring can apply only part of a stored rig.
On recovery, the callback drains up to 4,095 stale byte commands before
rendering (`crates/amp-lab/src/audio.rs:75-97`), which can compound the missed
deadline.

Expected: the heard synth eventually converges to the latest displayed/exported
state, and panic/transport delivery is reliable. Actual: saturation silently
drops newest state or safety commands with no diagnostic or resynchronization.
Healthy playback normally drains faster than the UI produces, so the trigger
requires a prior stall or stream disruption.

## Fix

Represent coalescible controls as latest desired state rather than an ordered
byte backlog. Reserve a reliable path for panic and transport, bound callback
drain work, and resend one complete latest-state snapshot after any overflow.
At minimum, observe every enqueue result, surface failure, and retry atomically
instead of partially applying A/B slots.

Add deterministic saturation tests covering a knob change, a six-knob recall,
play/solo, and panic. After consumer recovery, assert that audio-thread state
matches the latest UI state and that work per callback remains bounded.

## Notes

The fixed memory bound prevents unbounded RAM growth. It does not make silently
discarding authoritative state correct.
