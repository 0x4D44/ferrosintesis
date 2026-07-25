# MM-BUG-KILN-00105 — velocity compensation is chosen by program number, not by the voice actually built

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** voices / velocity law
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
- **Attempts:** fix=2, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, raised by Claude Opus 4.5 while draining the `--no-default-features` failures of MM-BUG-KILN-00090; the drums half landed there and the melodic half was parked) → Fixed (2026-07-25, GPT-5.6 Codex on KILN-Windows — velocity calibration now follows the constructed sample/composite or modeled fallback, including runtime sample opt-out and pitch-range rejection)

## Observation

`VEL_LEVEL_EXP` (`crates/ferrosintesis/src/voices.rs:12586`) is a `[f32; 128]` velocity-
compensation exponent **indexed by GM program number**. A program number does not determine
which voice was built: many arms of `make_uncorrected` build a sampled composite or a bare
model depending on the `samples` flag, and the single constant — fitted for the sampled
composite — is then applied unchanged to the model.

The call order makes it plain (`voices.rs:12761`):

```rust
pub fn make(program, key, vel, sr, seed, samples) -> Box<dyn Voice> {
    let voice = make_uncorrected(program, key, vel, sr, seed, samples);
    //          ^ first statement clamps: `samples && embedded_samples_available()`
    apply_vel_correction(voice, program, vel)
    //                          ^ exponent from PROGRAM ALONE; takes no `samples` at all
}
```

The voice is chosen *after* the clamp; the exponent is chosen *without reference to the flag*.

### Two halves, one root cause

**DRUMS — FIXED in this change.** `drums::drum_vel_level_exp(kit, samples, key)`
(`drums.rs:1498`) *does* take the flag, but `drums::make` passed the **caller's raw**
`samples` while `make_uncorrected` clamped it internally — so a modeled voice could be
corrected by the sampled exponent. `drums::make` now clamps once, before both. Byte-identical
in the default build, where `embedded_samples_available()` is `true` and the clamp is a no-op.
This alone fixed `velocity_law::tests::drums_follow_the_same_law_as_melodic_voices`.

**MELODIC — PARKED.** There is no flag at the melodic lookup to clamp. `apply_vel_correction`
has no `samples` parameter, so the drums remedy is inapplicable — a clamp there would be a
provable no-op, since `make_uncorrected` already clamps at `voices.rs:12857`.

## Measured impact

Derived with the repo's own `velocity_census` dev tool
(`cargo test -p ferrosintesis [--no-default-features] --lib velocity_census -- --ignored --nocapture`),
run in **both** build configurations. `k` is the least-squares slope of max-momentary-LUFS
against `20·log10(v/127)` over v = 32…127, at keys 48 and 60. Target `k = 2.0`.

**Eight programs measurably off in modeled-only and clean in the default build:**

| GM | default k (48/60) | modeled-only k (48/60) | note |
|---|---|---|---|
| 24 nylon guitar | 1.904 / 2.101 | **1.704 / 1.723** | fails the ±0.2 band; honest modeled exponent ≈ 2.405 |
| 56 trumpet | 2.108 / 1.892 | 1.820 / 1.892 | latent — key 48 only |
| 57 trombone | 2.101 / 1.900 | 1.674 / 1.862 | latent — key 48 only |
| 59 muted trumpet | 2.090 / 2.003 | 2.278 / 2.166 | latent, both keys |
| 64 soprano sax | 1.932 / 2.033 | 2.194 / 2.373 | no table entry (t[64] = 2.0) |
| 65 alto sax | 1.906 / 2.093 | 2.311 / 2.452 | |
| 66 tenor sax | 2.067 / 1.933 | 2.407 / 2.474 | |
| 67 baritone sax | 1.890 / 1.885 | 2.391 / 2.412 | no table entry |

GM 56/57/59 escape `every_gm_program_follows_the_square_law` only because it probes key 60
with a ±0.25 tolerance — **latent, not absent**.

A further nine programs are structurally at risk (their arm builds a different voice by
flag) but measure clean today: GM 48, 49, 58, 60, 68, 69, 70, 105, and GM 76 (which is
already compensated correctly — see below).

## Why the melodic half is parked rather than fixed

Making the lookup samples-aware **requires new measured constants** — a fitting exercise, not
a clamp. Guessing one would silently change how loud every note of those programs is. The
house rule (`lessons_learnt.md`, 2026-07-25) is that *a compensation constant marks an
unfixed upstream bug — fix the cause and delete it*, which argues for the larger change, not
a second hand-maintained table.

**The correct shape already exists in-tree.** GM 76 (`voices.rs:13461-13484`) wraps the
**model branch only**, in-arm, with its own `ScaledVoice { exp: 1.512 }`, and its comment
states the rule outright: *"Apply it HERE, wrapping the MODEL only, because the decision
tracks the VOICE, not the `samples` flag."* GM 76 consequently has **no** `VEL_LEVEL_EXP`
entry. That is the shape the rest of the family wants, program by program, each with a
measured constant.

**And it cannot be done as a byte-identity change.** GM 64–67 fall back to the modeled
`reed()` **in the default build too** — `SaxLoopVoice::new` returns `None` when the repitch
ratio leaves `[0.5, 2.05]` (`sampler.rs:3809`) and the arm at `voices.rs:13415` does
`.unwrap_or_else(|| Box::new(reed(...)))`. That fallback is keyed on **note pitch**, not on
the flag. Correcting it changes the default render at those keys, so it needs its own
render-diff and must not be folded into a byte-identical change.

## Fixed in this change

- `drums::make` clamps `samples` once (above).
- `velocity_law::looped_recording_voices_keep_their_documented_velocity_behaviour` gated its
  GM 76 clause on `embedded_samples_available()`. It asserted `BottleLoopVoice`'s deliberately
  *compressed* taper `[2.5, 7.0] dB`; under `--no-default-features` GM 76 is the modeled
  `Wind`, which correctly renders the full square law (25.15 dB measured) and so failed the
  band **for the right reason**. The modeled path stays pinned by the existing
  `modeled_gm76_follows_the_square_law_in_no_samples_builds`, so no coverage was lost.
- Two stale doc references to `voices::melodic_vel_level_exp` (`velocity_law.rs:378`, `:510`)
  corrected. **That function does not exist** — `grep -rn melodic_vel_level_exp crates/`
  found only those two comments. The test file documented the intended samples-aware
  compensation; the code never received it. Left uncorrected, they read as a guarantee the
  synth does not provide.

## Still failing, and owned elsewhere

`melodic_voices_follow_the_square_law` and `every_gm_program_follows_the_square_law` remain
red in the modeled-only build. That is this bug, honestly unfixed, not an oversight.

## Verification of what did land

```
cargo test -p ferrosintesis --no-default-features --lib   9 failed → 7 failed
cargo test -p ferrosintesis --lib --release               690 passed, 0 failed
```

Default-build byte-identity is by construction, not argument: `velocity_law` is
`#[cfg(test)] mod` (`lib.rs:114`) so it is compiled out of every shipped build, and the
`drums.rs` clamp is a no-op wherever `embedded_samples_available()` is `true`.

## Resolution — 2026-07-25

The melodic constructor now carries the correction selected for the voice it actually
built:

- `LaVoiceBuild` reports whether an LA composite was constructed or whether the
  extreme-repitch guard returned the bare model.
- `UncorrectedVoice` carries an optional measured model exponent from that result to the
  single outer `ScaledVoice`. The raw census hook discards this metadata and therefore
  remains genuinely uncorrected.
- GM24, GM56/57/59, and GM64–67 select their measured model calibration only on explicit
  sample opt-out, missing embedded assets, or actual repitch fallback. Eligible sampled
  and composite voices keep the existing default program-table calibration byte-for-byte.
- The compile-time modeled-only table fork is gone. The same construction rule now covers
  default and `--no-default-features` binaries without guessing from a Cargo feature or the
  caller's raw `samples` flag.

The two nylon model canaries now transport only the exact analytic exponent delta in both
feature configurations. Their pitch, spectrum, and envelope expectations did not move.

## Verification — 2026-07-25

- New routing coverage proves all eight explicit model paths select their model exponent,
  eligible sample paths retain the program-table exponent, and an extreme-pitch
  samples-on request selects the modeled fallback exponent.
- A new rendered-law oracle covers all eight programs at keys 48 and 60 in a
  default-feature binary with runtime samples disabled. Every path fits `k = 2.0 ± 0.2`.
- `$null | cargo test -p ferrosintesis --locked`: **714 unit tests and 4 doc tests passed;
  27 diagnostics ignored**.
- `$null | cargo test -p ferrosintesis --no-default-features --locked`: **614 unit tests
  and 4 doc tests passed; 22 diagnostics ignored**.
- Strict all-target clippy passes with default features and with
  `--no-default-features`; formatting and `git diff --check` pass.
- Fresh release binaries from exact baseline `c0c6f82`, full 124-MIDI inventory at
  11.025 kHz: **3 expected fallback-path changes, 121 byte-identical, 0 contamination**.
  The changed tracks are `Big Weather/03 - Run the Rooftops.mid` (GM57),
  `Atlas of Becoming/02 - Wire and Wake.mid` (GM65), and
  `Atlas of Becoming/06 - Late for the Ordinary.mid` (GM56/57). The other 19 tracks
  using a listed program remained byte-identical because their notes stayed on eligible
  sample paths.
