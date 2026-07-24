# MM-BUG-KILN-00083 — amp-lab silently drops authoritative UI commands when its ring fills

- **State:** Fixed
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
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). A new testable `Outbox` observes every
  enqueue, resends the complete latest state as one atomic snapshot after any drop, and
  retries a dropped panic — so the audio thread converges to the displayed state. One
  drain-bounding suggestion is deliberately not taken; see "Fix landed". Awaits
  independent two-eyes closure.)

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

## Fix landed (2026-07-24)

**The fix fits the UI amp-lab already is: an eframe app that repaints continuously.** So
the answer to "a single push was dropped" is convergence, not making one push reliable.

New `crates/amp-lab/src/outbox.rs` — an `Outbox` factored out of the egui `App` exactly as
`Core` was factored out of the cpal closure, so it is testable with a real `Ring` pair
(the `App` itself cannot be constructed in a test):

- **Every enqueue result is observed.** A dropped push sets a `dirty` flag and latches a
  `saturated` flag the UI now surfaces ("audio busy — re-syncing controls…"), so a lost
  command is never silent.
- **`pump`, called once per frame, resends the COMPLETE latest state** — rig bytes + Play
  + Solo — whenever `dirty`, and clears the flag only when the whole snapshot lands. After
  any transient stall the audio thread converges to exactly what the UI shows.
- **The snapshot is atomic.** A new `Producer::free()` lets `pump` preflight the whole
  snapshot and push it only when it all fits, so the audio thread never sees a half-applied
  rig — the "partial A/B recall" the bug calls out. The incremental knob path stays cheap
  in the common case; a miss just falls back to the full resend.
- **Panic has its own retry.** A dropped all-notes-off is a stuck note, worse than a stale
  knob, so `panic_pending` is retried ahead of the snapshot every frame until it lands.

Every UI call site now goes through the `Outbox` instead of ignoring `push()`'s bool.

**Regression** — four `outbox` tests on a real ring: a dropped knob edit is recovered on the
next pump; an A/B recall into a nearly-full ring is delivered whole or not at all (never
partial); a panic into a full ring is held and retried, not lost; and the uncontended path
sends immediately and pumps to a no-op.

**Fails before / passes after.** Reverting `observe` to ignore the enqueue result (the
pre-fix behaviour) fails the recovery and the atomic-recall tests; the panic and happy-path
tests still pass, because they do not depend on `dirty`.

**One suggestion deliberately NOT taken: bounding per-callback drain work.** The bug lists
it among the fixes, and the callback still drains the whole ring per call
(`audio.rs`, the `while let Some(c) = rx.pop()` loop). I left it, with reasons: (a) the
convergence design makes a deep backlog far rarer — the UI no longer floods the ring with
incremental deltas that fail, it sends ONE snapshot on recovery, so the steady-state
backlog is ~23 commands, not thousands; (b) the drain loop lives in the device-bound cpal
closure, which by this crate's own Core-split philosophy is exactly where untestable logic
should NOT go; and (c) a cap adds a new behaviour (commands lingering across callbacks) that
could itself delay a panic. It is a performance hardening for a now-unlikely path, not the
correctness defect — which was the silent loss of authoritative state, and is fixed. Worth
a separate look if a real deep-backlog stall is ever observed.

**Gates.** `cargo test -p amp-lab` 25 passed / 0 failed; clippy `-D warnings` clean; `cargo
fmt --check` clean. amp-lab is outside the workspace gate, so these were run explicitly.

## Notes

The fixed memory bound prevents unbounded RAM growth. It does not make silently
discarding authoritative state correct.
