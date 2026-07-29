# Scratchpad — out-of-scope observations (triage separately)

- [ ] 2026.07.27 — **GM40 violin, GM41 viola and GM110 fiddle mode-lock an octave
  high at velocity 127 for hard production-seed bow draws.** Found while widening
  MM-BUG-KILN-00146's cello register oracle across velocity. With engine seed index
  19 (`slope 2.876`), the current `BowedString` loses f0 at 24 violin, 20 viola and
  9 fiddle key/draw points; representative failures are violin key 67, viola key
  48 and fiddle key 56, all near +1200 cents. Their existing register gates use
  velocity 100 and therefore stay green. This is outside the cello-specific bug
  and requires a violin-family playable-region decision like MM-BUG-KILN-00029,
  not an incidental test-driven retune. See
  `crates/ferrosintesis/src/voices.rs:bowed_string_register_failures_full`.

- [ ] 2026.07.26 — **ASK ARTHUR BEFORE TOUCHING THIS.** He asked for it to be parked, not
  actioned: do not start work on it without checking with him first, whatever the item looks
  like on a later read. **The b1-upright re-bake breaks its own crate's inventory gate** —
  `D:\language\midi-music\tools\ferrosintesis-samples\prepare.py` (`_bake_b1upright`) and
  `D:\language\midi-music\crates\ferrosintesis-samples-b1-upright\src\lib.rs:254`
  (`assert_eq!(packaged.len(), FILE_COUNT)`). Running the documented
  `python prepare.py --only=b1upright` emits **74** WAVs where the crate ships **52**: 22
  stray `b1_soft_*.wav` from a velocity layer that was deliberately deleted to get the crate
  under the crates.io 10 MiB package limit. The bake was never updated to stop producing the
  layer, so a fresh re-bake fails the crate's own `FILE_COUNT` assert. Observed 2026-07-26 by
  baking into a scratch dir during the offline-rebuild audit; not fixed there because that
  task was scoped to the workspace-resolution and VCSL-pin defects.
  Why it matters: b1-upright is the **largest first-party bank and the GM0 default**, built
  from Arthur's own performances — the one bank we most need to be able to re-derive. It is
  currently the only first-party bank whose documented re-bake command cannot succeed.
  Shape of the fix (unverified, needs his steer on which he wants): either stop emitting the
  soft layer in `_bake_b1upright`, or emit it and have the crate ship it (reopening the 10 MiB
  question). There is also **no `_validate_generated_output_inventory` guard for this
  family** — that guard exists only for headroom (`prepare.py:3150`) and honkytonk
  (`prepare.py:2734`), which is why the drift went unnoticed; adding one for b1-upright would
  turn a silent 74-vs-52 mismatch into a bake-time error. Given the repo's
  hand-maintained-list defect class, the enumeration question ("which families lack the
  guard?") is probably the real unit of work rather than b1-upright alone.

- [x] 2026.07.25 — **`percentile_uses_nearest_rank` pins the historical failing value, not the
  convention** — `crates/ferrosintesis/src/voices.rs` (the test beside `fn percentile`). It
  asserts one case, p95 of nine values. An adversarial review of the KILN-00055 closure showed
  at least three broken variants still pass it: `sorted[((len-1) as f32 * q).ceil()]`,
  `(q*n).round()`, and `sorted[(q*n) as usize]` — each selecting a different element for the
  two live callers. It never exercises **q=0.05**, which is the value BOTH live consumers
  actually use, never hits the `clamp(1, ..)` lower branch, and never uses an n where `q*n` is
  integral. KILN-00055 is correctly Closed (the fix is right, and the red-before/green-after
  was run against the real body) — this is test strength, not a defect. Add a q=0.05 case and
  an integral-`q*n` case.

- [ ] 2026.07.22 — **M-CAL residual watchlist: the metric disagrees with ear-vetted trims
  on the slow-attack families** — GM56/57 brass (−6.7/−6.3 dB), GM67 (−4.8), GM48/50/51
  ensembles (+3.7..+4.3). Either the single-held-note probe biases slow-attack voices, or
  (Done 2026-07-29: added both cases. The q=0.05/n=9 case exercises the lower-rank
  clamp; q=0.05/n=20 pins one-based nearest-rank indexing when q*n is integral.)
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

- [ ] 2026.07.18 — **BusGlue compression keys off the raw pre-normalization internal
  level.** `BusGlue thr=0.32` detects on raw level (`engine.rs:~676`) and runs *before*
  `normalize_loudness`, so two albums both landing at −18 LUFS can receive different glue
  (a hidden program-level dependence in the master character). Effect small ("a dB or
  two"); making it loudness-relative would re-voice every album, so treat as deliberate.

- [ ] 2026.07.18 — **Rotating-phasor `Sine` is never renormalized** (`dsp.rs:~50`, 2-D
  rotation, no periodic 1/|z| rescale), so float error slowly drifts amplitude (and
  marginally frequency) on long held tones from the additive banks (pads/organ). Cheap
  occasional rescale would fix it. Very low audible impact.
  (Measured and adversarially reviewed 2026-07-25; NOT filed as a bug, 2 of 3 independent
  skeptics refuted it. The MECHANISM is real and worse than "float error": f32 rounding of
  cos/sin bakes in a fixed |c| != 1 bias, so |z| follows |c|^n - systematic, growing LINEARLY in
  dB (I measured +0.022 / +0.089 / +0.397 dB at 200k / 800k / 3.2M ticks, x4 per 4x ticks; a
  random walk would be x2). What kills it as a defect is EXPOSURE, and this is the correction
  worth keeping: there is no `Sine` in `engine.rs` at all - all 24 sites are per-note voice
  fields, control-rate LFOs, or bounded table loops - so the accumulator lives for a NOTE, not a
  track. The longest held note on a sustaining program in the whole catalogue is 114.72 s (GM 16
  organ, Through Lines 14), where the drawbar partials spread only ~1.6 dB, and any voice that
  retunes under vibrato destroys the bias entirely (a fresh (cr,ci) draws a fresh random-sign
  delta - measured 100x smaller). So: inaudible in-repo, and a fix would move every render for
  no gain. Keep open, low priority, because ferrosintesis is a GENERIC GM player: a foreign
  10-minute drone or a held note on the realtime `live.rs` path still reaches ~8 dB of
  inter-partial spread. `dsp.rs::sine_stays_bounded` does NOT cover this - it runs 1 s.)
- [ ] 2026.07.18 — **Two shipped drumkit banks are unreachable dead payload:**
  `CRASH_SIZZLE` and `SNARE_OFF` exist in the drumkit crate but no GM key maps to them
  (`sampler.rs:~2313` comment; absent from `sampled_drum` dispatch). Compiled-in but never
  selectable — GM has no dedicated key for either. Drop or wire behind a CC0 alt-bank.

- [x] 2026.07.13 — `distinctness::Why` (`crates/ferrosintesis/src/testutil.rs:1139`)
  is now a **single-variant enum** (`Collapse(u8)`) after Stage 4 deleted the last
  `Legit` pair (synth strings 50/51). Not wrong, but a mild smell: it forced a
  plain destructuring `let Why::Collapse(stage) = why;` at the once-`if let` site.
  If it stays single-variant through Stages 5/7a/7b (none of which add `Legit`),
  collapse it to a bare stage id: `ALLOW: &[(u8, u8, u8)]` and `allow_reason ->
  Option<u8>`. Deferred to avoid widening Stage 4 into a shared-infra refactor.
  (Re-verified 2026-07-25: still single-variant, and the Stages 5/7a/7b condition the note set has
  been met - no `Legit` came back. One correction: it is ONE destructure site but TWO consumption
  sites (the irrefutable `let Why::Collapse(stage) = why;` and a `Some(Why::Collapse(_)) =>` arm
  in the diagnostic printer), so the collapse touches five places, not two. Deliberately NOT done
  in this pass: it is cosmetic, and `testutil.rs` is a hot file in a repo where several agents
  work concurrently, so the conflict risk outweighs the tidy. Note the sibling
  `perceptual_distinctness::Why` IS genuinely two-variant - do not collapse that one.)
  (Done 2026-07-29: collapsed only `distinctness::Why` to a bare `u8` stage ID
  across its five sites. The sibling `perceptual_distinctness::Why` remains intact.)
- [ ] 2026.07.15 — **Drum-bus glue compressor (ch9) — unshipped idea recovered from the
  superseded `dry-drum-bus-for-forward-kit` branch before reaping it.** A feed-forward
  3:1 peak compressor + makeup gain on the channel-10 bus (sibling of the existing
  `BusGlue`), so kit prominence rides through the −18 LUFS / −1 dBTP master as RMS body
  instead of getting shaved off as peaks. Compiled clean; never gated, never A/B'd by
  ear, never committed. Full rationale, constants (`DRUM_COMP_THR`/`_MAKEUP`/`_ATK_S`/
  `_REL_S`) and code sketch are preserved in `wrk_journals/2026.07.15 - JRN - recover
  DrumGlue bus-compressor idea before reaping dry-drum-bus branch.md`. Would slot into
  `crates/ferrosintesis/src/engine.rs` next to `BusGlue`. Worth a look if "kit still
  not prominent enough" comes back up after the shipped `kit_balance()` fix.

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
- [ ] 2026-07-25 - **BowedString keys 43-45: for some bow-force draws the bass regime turns noisy
  enough to bury the vibrato FM entirely.** Split out of the 2026.07.14 wolf-band entry, whose main
  claim (keys 46-50 mode-locking onto 3*f0) was fixed by MM-BUG-KILN-00012 (beta 0.127 -> 0.140).
  This part was NOT fixed: pitch lands correctly on f0 at 43-45, but the vibrato oracle still routes
  AROUND those keys, and the comment recording why is still live in `crates/ferrosintesis/src/
  voices.rs` at the vibrato test ("same instability family as the wolf band"). Probed across seeds
  7/11/13/17/23; keys 38 and 55 are clean on every seed. Re-parked so the residual does not
  disappear with its parent entry.

- [ ] 2026-07-26 - **`gen_crate_lib.py`'s generated doc header has drifted from the 25 committed
  crate `lib.rs` files: only 1 of 25 matches what the generator now emits.** The generator was
  changed to derive the header from the crate's actually-packaged legal docs
  (`Licence/provenance: see <files>`), but only `-gong` appears to have been regenerated: 12 crates
  still carry the old fixed "Attribution/licence: see NOTICE / PROVENANCE.md" line and 12
  carry neither form. Measured by running TRUNK's own generator against the committed
  `-rain/src/lib.rs` - it differs on that line, so the drift is in the committed files, not in the
  generator. Nothing catches it: no test regenerates a crate and compares. Consequence is a
  published docs.rs front page that names the wrong provenance files for 24 of 25 crates - and,
  worse, the old line names `NOTICE` for crates that do not ship one. Same recurring shape as the
  three lists in CLAUDE.md: a per-crate value maintained by hand instead of derived. Fix is a
  regen sweep plus an oracle that regenerates each crate in a temp dir and diffs. Spotted during
  the 2026-07-25 scratchpad triage while re-verifying the rustfmt fix after rebasing onto it.

- [x] 2026-07-26 — `engine.rs:amp_protocol_has_one_definition` scrapes the NRPN knob table by
      matching ANY `| <int> | <text> |` row in the WHOLE of `crates/ferrosintesis/README.md`
      (`crates/ferrosintesis/src/engine.rs:4331`), rather than the rows of its own table. Adding
      an unrelated numbered table to that README silently doubles its count and fails the oracle
      — which is what a new GM0 CC0 table did on 2026.07.26 (worked around by giving that table a
      `CC0=N` first column instead of a bare integer). Scope the scan to the NRPN section so the
      next numbered table does not have to know about it.
      (Done 2026-07-29: the parser now scans only the score-authored amp section.
      An adversarial test places numbered tables both before and after it and proves
      they are ignored.)
