# MM-BUG-KILN-00213 — Sampled GM76 notes eagerly construct and discard the modeled fallback

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis / GM76 voice construction
- **Raised:** 2026-08-16T11:38:34Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T191407Z-8bcb5494
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00213-run-verify-20260913T191407Z-8bcb5494
- **Owner base:** 31eb54d242b6bb38a40ede86ad8ac64c7c90110b
- **Owner fingerprint:** sha256:cb715973f65c9bb59acc18f5db0867173d5e2e69f3dddd02396d60384a6f65ea
- **Owner since:** 2026-09-13T19:14:07Z
- **Owner until:** 2026-09-13T21:14:07Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-16T11:38:34Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:42:25Z, deltic:auto role=fix run=fix-20260913T153429Z-3c547ddf branch=task/bug-MM-BUG-KILN-00213-run-fix-20260913T153429Z-3c547ddf code=97c2083ef6d904f714eee673c8557e1e461bfba3 gate=manual)

## Observation

The GM76 arm in `crates/ferrosintesis/src/voices.rs:15012-15020` constructs a modeled
`Wind`, boxes it inside `ScaledVoice`, and boxes that wrapper before it asks
`bottle_loop_voice()` for the sampled voice. The sampled result is then selected with
`Option::unwrap_or(model)`. Rust evaluates the `unwrap_or` argument eagerly, so every
in-range samples-enabled GM76 NoteOn that successfully returns a `BottleLoopVoice`
immediately drops the fully initialized modeled fallback.

`Wind::from_preset` at `crates/ferrosintesis/src/voices.rs:8811-8877` initializes the
oscillator bank, filters, envelope, RNG and bottle resonator. The current ordering also
performs two avoidable heap allocations and their deallocations per successful sampled
NoteOn. Voice construction occurs in the deadline-bearing realtime render path, so a
fast GM76 passage pays deterministic CPU and allocator work that cannot affect its
audio.

Expected: build the modeled voice only for `--no-samples` or when the sampled voice
returns `None`. Actual: it is built and discarded even when the sample wins. Static
source review only; no app, test, build, render or benchmark ran, so audible dropout was
not claimed.

## Fix

<unfixed — raised only>

Move modeled-bottle construction into a closure/helper and call it from the no-samples
arm or `unwrap_or_else` fallback. A regression should count modeled constructor calls:
zero for a representative in-range sampled key, one for an out-of-range fallback, and
one when samples are disabled, while retaining the existing render oracles.

## Notes
