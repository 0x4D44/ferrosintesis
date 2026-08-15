# MM-BUG-CRUCIBLE-00026 — Unchecked render options can request allocator-aborting DSP buffers

- **State:** Open
- **Priority:** Should
- **Severity:** High
- **Area:** ferrosintesis / render option validation
- **Raised:** 2026-08-14T11:47:20Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260815T043516Z-p11252-n216628300-c1
- **Owner host:** NMI
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00026-run-fix-20260815T043516Z-p11252-n216628300-c1
- **Owner base:** aa9073543850b1cad3c1d84d67290d177b8bb25c
- **Owner fingerprint:** -
- **Owner since:** 2026-08-15T04:35:16Z
- **Owner until:** 2026-08-15T06:35:16Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-14T11:47:20Z, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh)

## Observation

Public offline and realtime builders accept unchecked sample rates, tail lengths, and echo
times at
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\engine.rs:1791`
and
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\live.rs:59`.
Those values directly size DSP buffers before rendering.

For example, `Options::default().with_echo(100_000.0)` reaches `PingPong::new` at
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\engine.rs:1295`.
At 44.1 kHz it requests about 4.41 billion samples per delay. `DelayLine::new` at
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\dsp.rs:359`
rounds each buffer to 8,589,934,592 `f32` values, about 64 GiB for the pair. The normal
RIFF-length preflight does not account for echo memory. `RealtimeSynth::new` likewise sends
an unchecked `u32::MAX` rate into reverb, chorus, delay, and sympathetic-resonance
constructors at `engine.rs:2150-2175`.

Expected: impossible configuration values are rejected before allocation. Actual: a
typed public API call can abort in the allocator or overflow size arithmetic. Closed
MM-BUG-KILN-00074 recorded that builders validate nothing, but fixed a particular bowed
voice; it did not close this allocation path.

## Fix

Define supported finite ranges for sample rate, tail, echo, wet level, and master gain.
Validate them before `EngineCore` or output allocation, and check every derived length.
Preserve compatibility with fallible `try_*` constructors or return `InvalidInput` from
fallible render entry points. Add non-allocating boundary tests for huge finite values,
NaN/Inf, direct buffered render, scratch render, and realtime construction. Estimated
effort: Medium because the realtime constructor is currently infallible.

## Notes
