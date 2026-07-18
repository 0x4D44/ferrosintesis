# MM-BUG-KILN-00015 — Chromatic percussion (GM 8–15) has no LA onset layer despite being the ideal onset-only candidate

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sampler
- **Raised:** 2026-07-18
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit)

## Observation

Celesta/glockenspiel/music box/vibes/marimba/xylophone/tubular/dulcimer (GM 8–15)
are pure `bell()` / `wood_bar()` / `Pluck` models — the 8..=15 `make()` arms
(`crates/ferrosintesis/src/voices.rs:~10734`) carry no `sampler::` call. These are
mallet-strike instruments whose entire identity is the attack transient — exactly
the case lessons_learnt (2026.07.16) says LA onset sampling fixes and model work
does not. It is the single highest-payoff un-sampled family and structurally the
easiest: short one-shots, no sustain to reconcile.

## Fix

Add a CC0 strike-onset bank (marimba/vibraphone/glockenspiel/xylophone/tubular
first) crossfaded over the existing `bell()`/`wood_bar()` models via the
unchanged `LaVoice::wrap` path. Reuses the proven LA pipeline (roots measured, fade
guard, `la_level_continuity`).

## Notes

- Enhancement filed as a bug per the maintainer routing decision (2026-07-18).
- Net-new sourcing (find/vet/SHA-pin/measure CC0 samples), so sequence after the
  reuse-only fixes (viola bank, cubic interpolation, Passport oracle).
