# Scratchpad — out-of-scope observations (triage separately)

- [ ] 2026.07.08 — drums review: `impl Default for CymSpec` would remove the
  `v2: None, noise2: None, shimmer: None` boilerplate from ~5 simple cymbal call
  sites (`fable5/hollowsynth/src/drums.rs` china 52 / splash 55 / ride 51|59 /
  closed-hat 42|44 / ride-bell). Deferred as low-value cosmetic (crash_spec
  already removed the worst dup; a little duplication is fine).
- [ ] 2026.07.08 — drums review: `Drum::render` computes `head_amp_now` and a
  `tones[0].phase.sin()` every sample for EVERY drum voice
  (`fable5/hollowsynth/src/drums.rs:271-272`), used only when `wire.is_some()`
  (snare v2). Guard with `if self.wire.is_some()` to skip the per-sample `sin()`
  on non-wire voices. Minor perf; correct as-is.
- [ ] 2026.07.08 — drums review: the DR3 `noise2` band pushes its index into
  `swelled` (`fable5/hollowsynth/src/drums.rs` in `cymbal`), but the only
  `noise2` spec (open-hat 46) has `swell:false`, so it is inert. Latent-wrong if
  a future spec set both `noise2` + `swell` (sizzle should be instant, not
  swelled). Drop the `swelled.push` for noise2 or comment it.
- [ ] **2026.07.08 — ARTHUR'S CALL: pre-existing vibrato bug in the shipped
  Wind + Bowed voices.** The 55-71 review found the reed vibrato ran 16x too slow
  (fixed); the SAME bug is latent in Wind (`voices.rs` ~1730/1747) and Bowed
  (~1841/1860) — an LFO `Sine` built at full `sr` but ticked once per `CTRL`
  samples, so the labelled ~5 Hz flute/whistle/fiddle vibrato is actually a
  ~0.3 Hz drift. It is a genuine quality bug. Fixing it (build at `sr/CTRL`, like
  the corrected reed/brass) CHANGES committed renders — Hollow Hill P1/P2
  (flute 73, whistle 78, fiddle 40), The Signal Fire, Winter Guests, Sub Rosa.
  Left OUT of v0.9 (scope = brass/reeds/orchestral) and flagged for Arthur: fix
  in a follow-up (its own listen), or fold into v0.9 under the relaxed policy.
- [ ] 2026.07.08 — reeds review: `ReedPreset`'s 8 presets each spell out ~13
  fields; a `RD_DEFAULTS` base + struct-update (like `BR_DEFAULTS`) would cut
  ~40 lines (`voices.rs`). Low-value altitude nit; deferred.
