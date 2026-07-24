# MM-BUG-KILN-00080 — amp-lab's safe ring API can violate its unsafe SPSC invariant

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** amp-lab / concurrency
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
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). Both endpoints carry
  `PhantomData<Cell<()>>`, so they are `Send` but no longer `Sync`, and a compile-time
  assertion (with a positive control) proves it. Evidence under "Fix landed" below.
  Awaits independent two-eyes closure.)
  → Closed (2026-07-24, independently verified by Codex GPT-5.6-Sol; fails-before,
  passes-after, root-cause review, and green gate evidence are recorded in
  `wrk_journals/2026.07.24 - JRN - Fixed queue two-eyes closure pass.md`.)

## Observation

`Ring` is manually marked `Send + Sync`
(`crates/amp-lab/src/ring.rs:35-40`). The endpoint wrappers contain
`Arc<Ring>` (`:58-59`), so `Producer` and `Consumer` automatically become
`Sync`. Their operations take `&self` (`:64` and `:97`).

Non-Clone endpoints do not enforce one caller. Safe Rust can share
`&Producer` between scoped threads or wrap it in `Arc<Producer>`. Two concurrent
`push()` calls can both load the same head, pass the capacity check, and write
the same `UnsafeCell<Cmd>` at `ring.rs:73`; those non-atomic writes are a data
race and undefined behavior. Shared concurrent `pop()` calls analogously claim
the same tail and can let the producer reuse a slot while another reader still
accesses it.

The current application uses exactly one UI producer and one audio consumer, so
the shipped execution path does not trigger the race. The unsafe implementation
is nevertheless unsound because its safe API permits the violating use.

## Fix

Make both endpoints `Send` but not `Sync`, for example with
`PhantomData<Cell<()>>`, while retaining the internal sharing required between
opposite endpoints. Alternatively require `&mut self` for `push`,
`push_midi`, and `pop`, and propagate exclusive endpoint ownership through the
callers.

Add compile-time assertions that each endpoint is `Send + !Sync`. Runtime SPSC
tests cannot prove this auto-trait contract.

## Fix landed (2026-07-24)

**Code** (`crates/amp-lab/src/ring.rs`). `Producer` and `Consumer` each gained a
`PhantomData<Cell<()>>` field. `Cell` is precisely "`Send`, never `Sync`", so the
endpoints stay movable between threads — which the app needs, the consumer is moved into
the audio callback — while safe code can no longer SHARE one: `&Producer` cannot cross a
thread boundary, and `Arc<Producer>` is no longer `Send`. That closes the hole exactly:
the unsound part was never the atomics, it was that the types did not enforce the
single-producer / single-consumer discipline the `unsafe impl Sync` on `Ring` assumes.

I took the marker rather than `&mut self` on `push`/`push_midi`/`pop`. Both work; the
marker states the constraint once, on the type, instead of threading exclusive ownership
through every caller to say the same thing.

**Proof — and it cannot be a runtime test.** The contract is that a violating program
must FAIL TO COMPILE, and any test that runs has already compiled. So the assertion is a
`const` block. Asserting a *negative* bound needs an inversion, since Rust has no
`T: !Sync`: a blanket trait impl supplies `NOT_SYNC = true`, and an inherent impl on
`IsSync<T: Sync>` supplies `false`, which shadows it whenever the bound is satisfied.

It carries a **positive control** — `assert!(!IsSync::<u32>::NOT_SYNC)` — because without
one, the two real assertions would still pass if the inversion silently stopped working
and `NOT_SYNC` became a constant `true`. A guard that cannot fail proves nothing, and this
kind of guard fails silently by construction.

**Fails before / passes after.** Removing the two `PhantomData` markers (the pre-fix
types) stops the build with the intended diagnostic:

```
error[E0080]: evaluation panicked: Producer is Sync: safe code can now share the write
end across threads, and two concurrent push() calls race on the same slot
error[E0080]: evaluation panicked: Consumer is Sync: safe code can now share the read end
across threads, and two concurrent pop() calls can claim the same slot
```

**And the discipline it protects still works.** New `one_endpoint_per_thread_still_works`
moves the consumer to a spawned thread, produces 200 commands from the main thread and
asserts all 200 arrive in order — so a marker that had accidentally broken `Send` (making
the lab uncompilable in its real shape) would be caught by a test rather than by a user.

**Scope.** The shipped execution path never triggered the race, as the bug says: there is
exactly one UI producer and one audio consumer. This removes the possibility, not a
symptom. No behaviour changed, so nothing renders differently.

**Gates.** `cargo test -p amp-lab` 15 passed / 0 failed; `cargo clippy -p amp-lab
--all-targets -- -D warnings` clean; `cargo fmt --check` clean. (amp-lab is excluded from
the workspace gate by `.deltic-integrate.toml`, so these were run explicitly.)

## Notes

The Acquire/Release publication protocol and `push_midi()` preflight are sound
under a genuine single-producer/single-consumer discipline. This bug is that the
types do not enforce that discipline.
