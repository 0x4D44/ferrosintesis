# Scratchpad — out-of-scope observations (triage separately)

- [ ] 2026.08.01 — **Root `Cargo.toml` still describes a gate flag that is gone.**
  `D:\language\ferrosintesis\Cargo.toml:39` says the failure hit "even for the
  `--workspace --exclude amp-lab` invocation the integration gate itself uses" — present
  tense, but `.deltic-integrate.toml` dropped `--exclude amp-lab` when amp-lab left the
  workspace. The sentence sits inside a past-tense explanation, so it is a wording nit,
  not a wrong instruction. Spotted while verifying MM-BUG-CRUCIBLE-00015, which fixed the
  same class of drift in `crates/amp-lab/README.md`.

- [x] 2026.07.22 — **M-CAL residual watchlist: the metric disagrees with ear-vetted trims
  on the slow-attack families** — GM56/57 brass (−6.7/−6.3 dB), GM67 (−4.8), GM48/50/51
  ensembles (+3.7..+4.3). Either the single-held-note probe biases slow-attack voices, or
  those shipped trims are stale. Only listening settles which; do NOT renumber them on the
  metric alone. Evidence: residual-oracle section of `_cal/derivation_v3.txt`.
  (Re-verified 2026-07-25 and it REPRODUCES - every parked number lands within ~0.5 dB on a fresh
  two-reference panel run on a different build. Evidence pointer moved: `_cal/derivation_v3.txt`
  is git-ignored scratch and is gone; use `wrk_docs/2026.07.25 - M-CAL closed-loop re-derive
  report.md` (appendix). Two things the note could not know: the AGGREGATE residual oracle passes
  (median -0.22 dB SC-55 over 38 vetted programs), so these six are tails rather than a systemic
  failure; and commit `4c24cb9` later changed the MODELED velocity exponents for GM 56/57/67 -
  three of the six - so the residuals above predate it and should be re-read before acting.
  MM-BUG-KILN-00118 covers the systemic half, that there is no committed residual baseline.
  Re-measured 2026-07-29 on the current build: all six residuals remained within 0.33 dB
  of the accepted baseline. Direct left/right listening settled the discrepancy:
  GM48 was raised 0.5 dB to the existing +6 dB ceiling; GM50/51 stayed unchanged;
  GM56/57 stayed unchanged because only their loud-note sustains were hotter; GM67
  stayed unchanged because its level evidence conflicts and sampled-sustain defects
  contaminate the comparison. The GM67 defects were promoted to MM-BUG-KILN-00176.
  Done 2026-07-29.)
- [x] 2026.07.18 — **Cathedral reverb send skips the 150 Hz send high-pass and is boosted
  1.30×.** `send_cathedral` goes straight to `cathedral.process` (`engine.rs:~2446`) with
  no `rev_hp` (contrast the hall send) at `CATHEDRAL_WET_SCALE=1.30`, so sub-150 Hz feeds
  the long FDN tail at +2.3 dB — possible LF mud. Scoped to GM19 CC0=2 organ, so contained.
  (Measured 2026-07-29 through the real engine path. The 150 Hz candidate loses 2.179 LU
  before matching. A matched, wet-return-only blind pair is at
  `_cal/listening/cathedral/`. Arthur preferred B, the current full-band send,
  for its greater presence. Retired 2026-07-29: keep the shipped routing unchanged.)

- [x] 2026-07-19 FINGERED BASS (GM 33, `BASS` preset) and UPRIGHT bass (GM 32, `UPRIGHT`) sound "more or less the same" to Arthur (showcase audition), despite the v0.12 §2.12 "widened 32/33 split". Expected: an electric flatwound (muffled, pickup-comb identity) vs a woody ACOUSTIC upright (corpus modes, fingertip thud, no pickup) should be clearly distinct. Investigate whether the split is audibly insufficient (or the showcase phrase just does not reveal it). Separate from the pluck redesign (a distinctiveness issue). crates/ferrosintesis/src/voices.rs BASS (~2773) + UPRIGHT (~2903).
  (Re-verified 2026-07-25: the CODE does not corroborate "more or less the same" - the presets now
  differ on t60 3.2 vs 2.6, out_lp 1150 vs 2200 Hz, sub 0.72 vs 0.28, attack_noise 0.12 vs 0.90,
  and different body topologies. Two leads that survive anyway. (1) The framing is off: BASS has
  `pickup: 0.34` but `pickup_rlc: (0,0)` - the electric bite is deliberately switched OFF for the
  flatwound voicing - so the "pickup comb vs corpus modes" contrast does not actually exist.
  (2) The real gap is oracle-shaped: `bass_articulations_distinct` only checks UPRIGHT.t60 <
  BASS.t60 plus a body mode; NOTHING asserts the two RENDER distinguishably. Add that oracle
  before touching the presets. Both `pos` values are ~0.37, i.e. effectively identical pluck
  position, which is a plausible cause of the impression.
  Re-measured 2026-07-29 with a 12-note dry phrase. The current defaults render
  measurably different signals: GM32 has 2.9% vs GM33's 1.5% energy at 400–2000 Hz,
  decays 1.86 dB faster over the held-note comparison, and the loudness-matched null is
  only -3.16 dB relative to either signal. Added a rendered factory-routing oracle.
  The -20.0 LUFS blind pair is at `_cal/listening/bass/`. Direct Ferro-left
  comparisons against SC-55 and S-YXG50 are at `_cal/listening/bass-lr/`.
  Arthur preferred the GM33 electric bass unchanged and found GM32 convincingly
  SC-55-like. GM32's A2 decay matches SC-55 within 0.1 dB over 1.1 seconds; its
  D2 fades only 1.6 dB more over 0.95 seconds, while Yamaha sustains materially
  longer than both. Retired 2026-07-29: keep both presets unchanged.)
