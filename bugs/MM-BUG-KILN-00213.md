# MM-BUG-KILN-00213 — Sampled GM76 notes eagerly construct and discard the modeled fallback

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis / GM76 voice construction
- **Raised:** 2026-08-16T11:38:34Z
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
- **State history:** Open (2026-08-16T11:38:34Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:42:25Z, deltic:auto role=fix run=fix-20260913T153429Z-3c547ddf branch=task/bug-MM-BUG-KILN-00213-run-fix-20260913T153429Z-3c547ddf code=97c2083ef6d904f714eee673c8557e1e461bfba3 gate=manual) -> Closed (2026-09-13T19:25:30Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: eager unwrap_or restored fails the constructor-count test; its no-default-features gate break split to MM-BUG-CRU-00062)

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

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `97c2083e`) by an agent other than the fixer.

**Original observation re-derived.** The GM76 arm now builds the modeled bottle only through `unwrap_or_else(|| make_gm76_model(..))` or on the no-samples arm; the eager construct-and-discard is gone.

**Fails-before (method B).** Restoring eager `.unwrap_or(make_gm76_model(..))` fails `voices::tests::gm76_model_fallback_is_constructed_only_when_selected` ("sampled GM76 must not build its fallback", left 1, right 0). Restored; `git diff` empty; passes with default features.

**Residual split to MM-BUG-CRU-00062 (Must).** The test is not gated on `embedded-samples`; in a modeled-only build the fallback is correctly built once, so `cargo test -p ferrosintesis --no-default-features` fails. That is a required gate step on trunk `8b6a6f86`. The voice code needs no change.

## Notes
