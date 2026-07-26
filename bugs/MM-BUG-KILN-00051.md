# MM-BUG-KILN-00051 — after the plucked t60 re-fit, the LA guitar sample→model crossfade seam blooms (~5%): the sample onset fades out before the now-hotter model sustain peaks

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sampler
- **Raised:** 2026-07-23
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
- **State history:** Open (2026-07-23, raised by Claude Opus 4.8 (1M) — surfaced by the plucked-family t60 re-fit; `la_level_continuity` now carries a bounded exception for the guitar labels) → Fixed (2026-07-26, GPT-5.6 Codex on KILN-Windows — re-fitted GM24's high-register, medium-velocity sample gain and retired both guitar bloom allowances) → Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: GPT-5.6 Codex on KILN-Windows), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree at b0b93d9: `cargo fmt --all --check`, `clippy --workspace --exclude amp-lab --all-targets -D warnings`, `clippy -p ferrosintesis --no-default-features --all-targets -D warnings`, `test -p ferrosintesis --no-default-features --locked` (628 passed) and `test --workspace --exclude amp-lab --locked` (731 passed) - 1461 tests, 0 failures. Original observation re-run at source: the bounded `guitar` bloom allowance (`bloom <= 1.15`) is gone from `assert_attack_is_peak` (`sampler.rs:8199`), whose only surviving label special case is the documented, unrelated `piano-low` attack-window widening. Every struck row in `la_level_continuity` - including `steel-guitar-low`, the row whose failure the bug quotes verbatim (late 0.04411 above attack 0.04223) - now goes through the shared `late <= attack * 1.01` no-bloom rule and passes. `guitar_low_velocity_seam_continuity` covers GM24 key 76 at velocities 56/72/86 as the resolution claims, and `nylon_seam_gain` (`voices.rs:9221`) is exactly 1.0 through key 64, at velocity 40 and from velocity 100 up, so the correction is confined to the measured medium-velocity high-register corner. Both tests green.)

## Observation

**Symptom.** The nylon/steel guitars (GM24/25) carry an LA sample layer that crossfades a
recorded pick onset into the modelled string. The 2026.07.23 plucked-family t60 re-fit
(nylon 3.8 → 7.7, steel 4.5 → 7.0) raised the MODEL sustain level, so at the crossfade
seam — where the sample onset has faded out but before the (now hotter) model fully takes
over — the envelope dips and then blooms ~5 % (≈ 0.4 dB) a few 50 ms windows into the note.
`la_level_continuity` caught it: `steel-guitar-low: attack is not the peak — late window
0.04411 above attack 0.04223`.

**Expected.** The attack (the pick) owns the peak; the sample→model handoff is seamless in
level.

**Actual.** A small mid-note bloom at the crossfade seam. Small (0.4 dB) and unlikely to be
audible, but the attack is no longer strictly the peak.

**Reproduce.** `cargo test -p ferrosintesis --release -- la_level_continuity` — the guitar
labels now take a bounded exception (`bloom <= 1.15`, `sampler.rs`); remove the `guitar`
branch to see the raw failure.

## Root cause

`crates/ferrosintesis/src/sampler.rs` — the LA guitar layer's onset gain / fade
(`LA_GUITAR`, `LA_STEEL` and the crossfade to `[fade_end, ∞): the MODEL owns the sustain`)
was level-matched to the pre-re-fit model, which decayed faster. With the model now
sustaining ~1.5–2 dB louder, the fade schedule leaves a dip-then-bloom at the seam.

## Fix direction

Re-match the LA guitar crossfade to the new model sustain level: either raise the sample
fade-out tail slightly or trim the model level at the seam so the handoff is monotone.
Then remove the bounded `guitar` exception in `la_level_continuity` (it is bounded on both
sides precisely so the fix cannot pass silently). Needs the render-diff inventory.

## Notes

- Cosmetic today (0.4 dB, mid-note). Filed so the exception is not permanent.
- Same class as MM-BUG-KILN-00030 (the harpsichord LA onset not tracking a `vel_sense`
  model) — both are LA-onset-vs-model level tracking gaps.

## Resolution — 2026-07-26

Intervening trunk work had already made every velocity-100 guitar row satisfy the
common attack-owns-the-peak rule, so removing that allowance passed fail-first.
The amplified low-velocity case remained real: GM24 key 76 placed its model crest
1.41×, 1.33×, and 1.08× above the sampled attack at velocities 56, 72, and 86.
Keys through 64 and GM25 already passed without an allowance.

`nylon_seam_gain()` now applies a measured key/velocity make-up surface only to
GM24's sampled onset. It is exactly 1.0 through key 64, at velocity 40, and from
velocity 100 upward; it interpolates to the calibrated key-76 gains only across
the affected medium-velocity band. This preserves the already-hot velocity-40
corner and every unaffected guitar path. Both temporary guitar exceptions are
gone, and the low-velocity seam test now covers velocities 56/72/86 at key 76.

## Verification — 2026-07-26

- Fail-first without the low-velocity allowance reproduced the key-76/velocity-72
  bloom: attack `0.026704`, late crest `0.035604` (1.333×).
- Corrected key-76 attack/late readings are `0.023269/0.021811` at velocity 56,
  `0.037919/0.035600` at velocity 72, and `0.044646/0.042181` at velocity 86.
  Each now clears the shared 1% no-bloom rule with about 5–6% margin.
- The complete default suite passed (726 tests, 27 ignored), the model-only suite
  passed (625 tests, 22 ignored), and both doc-test sets passed (4 tests each).
- Strict workspace clippy and true model-only clippy passed with warnings denied;
  formatting and `git diff --check` passed.
- Fresh release binaries from exact baseline `28ef858`, full 124-MIDI inventory
  at 11.025 kHz: 10 expected GM24 pieces changed, 113 stayed byte-identical, and
  contamination was zero. The one scanner-reported GM24 non-reach is expected:
  all 83 nylon-guitar notes in that piece are keys 53–64, where the correction is
  deliberately exactly 1.0.
