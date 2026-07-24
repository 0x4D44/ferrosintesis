# MM-BUG-KILN-00080 — amp-lab's safe ring API can violate its unsafe SPSC invariant

- **State:** Open
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

## Notes

The Acquire/Release publication protocol and `push_midi()` preflight are sound
under a genuine single-producer/single-consumer discipline. This bug is that the
types do not enforce that discipline.
