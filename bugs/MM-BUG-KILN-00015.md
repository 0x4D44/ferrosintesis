# MM-BUG-KILN-00015 — Chromatic percussion (GM 8–15) has no LA onset layer despite being the ideal onset-only candidate

- **State:** Fixed
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit) → Fixed (2026-07-20, Claude Opus 4.8 (1M) — batch 2 landed: vibes `7cd06da`, tubular `943c6f2`, celesta `302a0dd`, music box + dulcimer `b8d47e1`)

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

### Batch 1 (marimba 12 / xylophone 13 / glockenspiel 9) — LANDED

Built under loop-build on branch `task/20260718-FIX-HUM-ferrosintesis-chromatic-perc-la-marimba`
(U1 `0847721` → U4 `fdbdfd4`). VSCO-2-CE Percussion mallets (CC0, already-pinned rev) baked into
`-orchestral2` (22 WAVs: 10 marimba, 8 xylo, 4 glock — glock G4/C6 dropped as mis-measured
zones), banked in `sampler.rs`, routed via `LaVoice::wrap` over the modal `bell()`/`wood_bar()`
bodies. Roots measured clean. `class_identity_ranges_hold` (MM-BUG-KILN-00006) confirmed the
onsets keep GM 8-15 in the DECAY class; `o_pitch`'s Modal branch was extended (Arthur-approved)
to accept an in-tune n·f0 harmonic when a bright sample's dominant partial differs from the model
mode (the VSCO xylo is 2f-bright vs the wood_bar model's 3f). Full workspace suite green;
render-diff GM 9/12/13-only reach, `--no-samples` bit-identical, zero contamination.
**State stays Open** — batch 2 remains.

### Batch 2 — LANDED (2026-07-20)

All five gained a real sampled onset as the default over the modeled body, with the pure model
preserved as the CC0!=0 alt: vibraphone 11 (VCSL, `7cd06da`), tubular bells 14 (VCSL, `943c6f2` —
plus a CC0=3 model alt, since 14's CC0!=0 slot was already the tam-tam/gong), celesta 8 (MS Basic
SF3 MIT, `302a0dd`), music box 10 (moodyfingers CC0) + dulcimer 15 (iternetcone CC-BY, new `-ccby`
crate, `b8d47e1`). Each: `altbank_sampled_programs_preserve_pure_model_and_default_layers` oracle
green, render-diff clean (0 contamination), `--no-samples` byte-identical. Sources + licensing per
the 2026-07-19 sourcing HLD (which also corrected the round-3 jRhodes/celesta premises).

## Notes

- Enhancement filed as a bug per the maintainer routing decision (2026-07-18).
- Net-new sourcing (find/vet/SHA-pin/measure CC0 samples), so sequence after the
  reuse-only fixes (viola bank, cubic interpolation, Passport oracle).
