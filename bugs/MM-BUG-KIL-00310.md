# MM-BUG-KIL-00310 — routed_banks() hand-maintains the 13-bank list instead of deriving from the crates' BANKS exports

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** sampler / drum-kit test derivation
- **Raised:** 2026-08-19T09:33:22Z
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
- **State history:** Open (2026-08-19T09:33:22Z, raised via `deltic bugs new`)

## Observation

The consumer-side per-take asset guard iterates a hand-copied bank list.
`routed_banks()` (`crates/ferrosintesis/src/sampler.rs:7129-7145`) enumerates ten
`kitbank::` banks and three `kitbank2::` banks as a fixed `[&Bank; 13]` literal.
Both asset crates export exactly that set —
`ferrosintesis_samples_drumkit::BANKS` (`[&Bank; 10]`, drumkit `src/lib.rs:684`)
and `ferrosintesis_samples_drumkit2::BANKS` (`[&Bank; 3]`, drumkit2
`src/lib.rs:213`) — but neither export is referenced anywhere in
`crates/ferrosintesis/src` (grep for `kitbank::BANKS`/`kitbank2::BANKS` returns
nothing).

`routed_banks()`'s one caller, `sampled_drum_has_no_boundary_click`
(`sampler.rs:7363`), is the only test that checks every take's head/tail energy, so
the list is load-bearing. Repro: add a bank to either kit half and route it in
`sampled_drum` (`sampler.rs:5006-5028`) — everything compiles, both crates' own
oracles pass (each proves only internal consistency), the package-prewarm oracle
passes (it checks packages, not banks), and the new bank's takes ship with no
boundary-click check. On a box with no ears the symptom is a click on every hit,
found only by a listener. This is CLAUDE.md's "hand-maintained lists are the
recurring defect — derive them" class (KILN-00059/00060/00069 lineage), sitting on
the exact drumkit/drumkit2 seam no single crate's tests can span.

Expected: the routed-bank set is derived from the crates' exports and tied to
`sampled_drum`'s match arms. Actual: it is a third, hand-written copy. The three
lists agree today; false-green-by-omission awaits the next bank.

## Fix

Derive it: chain `kitbank::BANKS` and `kitbank2::BANKS` instead of the literal
array, and assert the yielded set matches the banks reachable from `sampled_drum`
(source-scan its match arms for `kit::<NAME>`/`kit2::<NAME>`, the same technique
`sampler.rs` already uses to scan `prewarm()`'s body). Prove the derivation catches
an omission by removing one entry from a crate's `BANKS` and watching the
cross-check go red.

## Notes

Raised by the 2026-08-19 static review of `crates/ferrosintesis-samples-drumkit2/`
(worktree 20260819-REV-MM-CLA@KILN-code-review-101941), devil's-advocate lens.
Estimated effort: Small.
