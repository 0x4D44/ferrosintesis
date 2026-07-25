# MM-BUG-KILN-00102 — modeled-only builds panic on GM 25: the sample bank is an eager argument, evaluated before the fallback

- **State:** Closed
- **Priority:** Must
- **Severity:** High
- **Area:** voices / sampler
- **Raised:** 2026-07-25
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, found while classifying the 28 `--no-default-features` failures of MM-BUG-KILN-00090; a first classification pass proposed gating most of the affected tests, and an adversarial second pass caught that the failures were one shipped panic rather than a test problem) → Fixed (2026-07-25, Claude Opus 4.5; `steel_layered` now takes the bank lazily. Modeled-only failures fell 28 → 9 from this one change. Awaits independent two-eyes closure.) → Closed (2026-07-25, Codex GPT-5; independently reproduced the GM25 modeled-only sample-bank panic on the pre-fix parent, proved the same focused render test passes after the lazy-bank fix, confirmed the remaining nine modeled-only failures are the separate MM-BUG-KILN-00090 set, and passed the complete repository gate.)

## Observation

**`--no-default-features` — a shipped, documented configuration offered in the README —
panicked whenever a MIDI file selected GM program 25 (steel guitar).**

```
thread '…' panicked at crates/ferrosintesis/src/sampler.rs:102:5:
sample eastpick_E2.wav requested from a modeled-only ferrosintesis build
```

Backtrace: `engine::render` → `EngineCore::handle_event` → `voices::make` →
`voices::make_uncorrected` → `sampler::eastman_picked_bank` → `sampler::eastpick` →
`embedded_wav` (panic).

`steel_layered` (`crates/ferrosintesis/src/voices.rs:8807`) had the correct fallback and
it was **unreachable**:

```rust
pub(crate) fn steel_layered(zones: &'static [Zone], …, samples: bool) -> Box<dyn Voice> {
    let model = Box::new(Pluck::new(&STEEL, key, vel, sr, seed));
    if !samples { return model; }        // correct, and never reached
```

`zones` is an **eager argument**. Rust evaluates it at the call site, so
`crate::sampler::eastman_picked_bank()` ran and panicked *before* `steel_layered` was
entered. The GM 25 arm at `voices.rs:12943` was the only arm in `make_uncorrected` written
this way — every other arm reads `if samples { wrap(bank(), …) } else { model }`, keeping
the accessor inside the branch. Two more call sites in `altbank.rs:1146` and `:1155` (the
CC0=1 and CC0=2 alternates) had the same shape and were latent: a foreign GM file
authoring bank-select on program 25 would have panicked a modeled-only build the same way.

## Why this was worth finding rather than gating

The panic surfaced as **20 of the 28 failing tests** in MM-BUG-KILN-00090, most of them
tests whose subject has nothing to do with samples — `solo_mutes_other_channels`,
`cc74_brightness_filter`, `portamento_glides_from_previous_pitch`. They use GM 25 merely as
"a channel that plays a note", and several already set `samples: false` in their own
options, so they had *explicitly asked for the modeled voice* and still got a sample
request.

A first classification pass proposed `#[cfg(feature = "embedded-samples")]` on most of
them. That would have compiled the evidence out of existence and left a shipped panic in
the modeled-only build permanently invisible. MM-BUG-KILN-00090's instruction not to
mass-gate is what this bug exists to justify.

## Fix

`steel_layered` now takes `zones: fn() -> &'static [Zone]` and calls it *after* the
`if !samples { return model; }` early return, so the accessor runs only on the path that
actually wants a sample. All three call sites pass the function item instead of its result.

Deliberately fixed at the callee, not by reordering the three call sites: the callee is
where the `samples` decision lives, so a fourth caller written in the old shape cannot
reintroduce the bug — it will not type-check.

## Verification

```
cargo test -p ferrosintesis --no-default-features --lib   28 failed → 9 failed
cargo test -p ferrosintesis --lib --release               679 passed, 0 failed (unchanged)
```

Render-diff over the catalog: expected byte-identical in the default build, where the
bank is resolved on exactly the same path in exactly the same order — the change is *when*
the accessor is called, and in a samples-on build that is unconditionally.

## What this does NOT fix

The remaining 9 modeled-only failures are separate findings, tracked under
MM-BUG-KILN-00090: a GM 96 rain voice truncated mid-note (which affects EVERY
configuration, not just this one), program-indexed velocity compensation on GM 24, a drum
compensation table chosen from an unclamped flag, and a deliberate always-red sentinel test
that is Arthur's call.

Note also that this panic was **masking two full sweeps**: `every_gm_program_follows_the_square_law`
and `every_program_renders_at_every_common_rate` both died at GM 25, so programs 26–127
have never actually been exercised modeled-only. The remaining work is not yet sized.

### Independent closure verification (2026-07-25 — Codex GPT-5)

- Inspected the fix at the owning layer. `steel_layered` now accepts a bank function,
  returns the modeled `Pluck` before invoking it when `samples` is false, and resolves the
  bank only on the sampled path. The default, CC0=1, and CC0=2 call sites all pass function
  items, so the eager-call shape no longer type-checks.
- On the pre-fix parent `7cbf8dd4dbb178aa57f5d1bda62cddcbf38fbbdd`, the existing
  `engine::tests::solo_mutes_other_channels` regression under `--no-default-features`
  failed at `sampler.rs:102`: `sample eastpick_E2.wav requested from a modeled-only
  ferrosintesis build`.
- The identical focused test passed on the fixed tree after rebasing onto current
  `origin/main`.
- The full modeled-only library run completed with 575 passed, 9 failed, and 21 ignored.
  None of the nine failures was the GM25 sample-bank panic; they are the distinct,
  already-recorded MM-BUG-KILN-00090 residual set.
- The repository gate passed: formatting, workspace Clippy excluding `amp-lab`, modeled-only
  `ferrosintesis` Clippy, and workspace tests excluding `amp-lab`.
