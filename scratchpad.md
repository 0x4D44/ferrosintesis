# Scratchpad — out-of-scope observations (triage separately)

- [ ] 2026.07.22 — **M-CAL residual watchlist: the metric disagrees with ear-vetted trims
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
  MM-BUG-KILN-00118 covers the systemic half, that there is no committed residual baseline.)
- [ ] 2026.07.18 — **Ride bell (key 53) skipped the MetalPlate upgrade in the modeled
  path.** It is a fixed 6-mode inharmonic `d()` stack (`drums.rs:~1828`) while 49/51/52/
  55/57/59 route to `metal_plate`; the sampled `RIDE_BELL` has only 3 round robins. A busy
  bell ostinato is the most likely cymbal to sound mechanical. Modeled-path-only + niche.

- [ ] 2026.07.18 — **Cathedral reverb send skips the 150 Hz send high-pass and is boosted
  1.30×.** `send_cathedral` goes straight to `cathedral.process` (`engine.rs:~2446`) with
  no `rev_hp` (contrast the hall send) at `CATHEDRAL_WET_SCALE=1.30`, so sub-150 Hz feeds
  the long FDN tail at +2.3 dB — possible LF mud. Scoped to GM19 CC0=2 organ, so contained.

- [ ] 2026-07-13 — **No root LICENSE** (`d:\language\midi-music\`). Only the four crate dirs
  carry licence text, so everything outside them — `tools/ferrosintesis-samples/prepare.py`
  (the very file the published crate READMEs cite as CC0 provenance evidence), `albums/`,
  `build.py`, `render_opus.py`, `demos/` — is all-rights-reserved by default, and GitHub
  shows no licence badge. Not a crates.io blocker (the `license` field is what the registry
  requires, and all three publishable crates have it). **Needs Arthur:** a blanket root
  MIT/Apache would also sweep in nineteen albums of creative work, which may not be wanted —
  a carve-out (code MIT/Apache, `albums/` separate) is probably the right shape.

- [ ] 2026-07-19 FINGERED BASS (GM 33, `BASS` preset) and UPRIGHT bass (GM 32, `UPRIGHT`) sound "more or less the same" to Arthur (showcase audition), despite the v0.12 §2.12 "widened 32/33 split". Expected: an electric flatwound (muffled, pickup-comb identity) vs a woody ACOUSTIC upright (corpus modes, fingertip thud, no pickup) should be clearly distinct. Investigate whether the split is audibly insufficient (or the showcase phrase just does not reveal it). Separate from the pluck redesign (a distinctiveness issue). crates/ferrosintesis/src/voices.rs BASS (~2773) + UPRIGHT (~2903).
  (Re-verified 2026-07-25: the CODE does not corroborate "more or less the same" - the presets now
  differ on t60 3.2 vs 1.8, out_lp 1150 vs 2200 Hz, sub 0.72 vs 0.15, attack_noise 0.12 vs 0.90,
  and different body topologies. Two leads that survive anyway. (1) The framing is off: BASS has
  `pickup: 0.34` but `pickup_rlc: (0,0)` - the electric bite is deliberately switched OFF for the
  flatwound voicing - so the "pickup comb vs corpus modes" contrast does not actually exist.
  (2) The real gap is oracle-shaped: `bass_articulations_distinct` only checks UPRIGHT.t60 <
  BASS.t60 plus a body mode; NOTHING asserts the two RENDER distinguishably. Add that oracle
  before touching the presets. Both `pos` values are ~0.37, i.e. effectively identical pluck
  position, which is a plausible cause of the impression.)
