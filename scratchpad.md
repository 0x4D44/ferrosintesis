# Scratchpad — out-of-scope observations (triage separately)

- [ ] 2026.07.25 — **`percentile_uses_nearest_rank` pins the historical failing value, not the
  convention** — `crates/ferrosintesis/src/voices.rs` (the test beside `fn percentile`). It
  asserts one case, p95 of nine values. An adversarial review of the KILN-00055 closure showed
  at least three broken variants still pass it: `sorted[((len-1) as f32 * q).ceil()]`,
  `(q*n).round()`, and `sorted[(q*n) as usize]` — each selecting a different element for the
  two live callers. It never exercises **q=0.05**, which is the value BOTH live consumers
  actually use, never hits the `clamp(1, ..)` lower branch, and never uses an n where `q*n` is
  integral. KILN-00055 is correctly Closed (the fix is right, and the red-before/green-after
  was run against the real body) — this is test strength, not a defect. Add a q=0.05 case and
  an integral-`q*n` case.

- [x] 2026.07.25 — **`render-diff` is not bank-aware, so an alt-bank-only voice
  change is misclassified as contamination or not-reached** —
  `tools/render-diff/render_diff.py:scan` records only program numbers and drum
  keys; it ignores CC0/CC32. KILN-00049 changed DRIVE_LEAD only on GM29/30
  alternate banks: the full 124-MIDI diff moved exactly 11 tracks, and a
  bank-aware scan proved those same 11 are the complete CC0-nonzero GM29/30 set,
  but the tool called them contamination without that context. Extend the
  touched identity and MIDI scanner to include bank selectors.
  (Promoted 2026-07-25: MM-REQ-KILN-00033. Re-verified first - `scan()` still returns only
  (programs, drum keys) and its event loop lumps CC into the skip-2-bytes arm, and albums really
  do author bank selects (every Slipstream movement sends CC0 on four channels). Filed rather
  than fixed here because it is not a one-liner: it needs a new CLI axis, a third return value,
  per-channel (program, bank) pairing at note-on, and a decision on MSB-vs-LSB semantics - the
  repo uses CC0 AND LSB 96. The sibling ch-10 mis-attribution defect IS fixed in this pass.)
- [x] 2026.07.24 — **8 clean body-knock (tap) samples were captured in the GM120 fret-noise
  session but PARKED** — `DR0000_0204` (the taps at ~26/56/60/61 s, and more), soundboard/side
  knocks. They are the raw material for fixing the guitar's thin note-off `stop_thump`
  (currently modeled). Not folded into the fret-noise change (kept it focused, Arthur's steer).
  Source archive: `samples/fret-noise-eastman-e1d/DR0000_0204.opus`. A future job: cut the taps,
  bake, and drive the guitar note-off thump from them.
  (Promoted 2026-07-25: MM-REQ-KILN-00034. Re-verified: the archive is still there, the bank's own
  README still records the reservation, and `stop_thump` is still a synthetic Burst through a
  250 Hz lowpass with no sample layer. Filed rather than actioned - it is a multi-step build
  (cut, bake, wire, oracle) AND a default-on timbre change needing the render-diff inventory and
  Arthur's ear, so it does not belong in a triage pass.)
- [x] 2026.07.24 — **Workspace MSRV is broken by a transitive dep, pre-existing on origin/main**
  — `cargo +1.87 check --workspace` fails: `image@0.25.10` requires rustc 1.88 (pulled via the
  eframe/egui GUI stack, i.e. `amp-lab`). Not from the audio crates — `ferrosintesis` + the
  sample crates all pass `+1.87`. So the fleet's "prove MSRV with `check --workspace`" gate
  cannot pass here until `image` is pinned back (`cargo update image --precise <1.88-compatible>`)
  or amp-lab's MSRV is bumped. Confirmed identical on the `dfbf1f7` baseline.
  (Done 2026-07-25: neither pin nor bump was needed — the command was wrong. `amp-lab` is a
  dev-only GUI with `publish = false`, and `.deltic-integrate.toml` already excludes it from
  clippy and test for exactly this reason. `cargo +1.87 check --workspace --exclude amp-lab
  --locked` passes on this box, so every SHIPPED crate really is 1.87-clean; CLAUDE.md now
  documents that form and says why the exclusion is not a dodge.)

- [x] 2026.07.22 — **GM6 Harpsichord fails the M-CAL velocity guard at 9.6 dB** — its
  ferro-vs-SC-55 level difference changes by 9.6 dB between v72 and v110, i.e. a
  velocity-RESPONSE mismatch, not a level offset (a static `PROGRAM_TRIM_DB` entry cannot
  fix it). It is the flagship +6 dB piano-family trim, so worth a look.
  Evidence: `_cal/derivation_v3.txt`, GM6 row (`vel 9.6`); reproduce with
  `derive_trims.py` on a full-128 certified run. Raised from the M-CAL v3 derivation review.
  (Already fixed: MM-BUG-KILN-00044, Closed 2026-07-25. The defect half was a stale
  `VEL_LEVEL_EXP[6] = 1.500` correction worth -1.837 dB across v72->v110, which actually
  INVERTED the response; commit `d1245e9` deleted it and `voices.rs` now carries a load-bearing
  "GM6 harpsichord has NO entry, and must not get one". The remainder is an accepted design
  exception, A/B'd by Arthur: `HARPSICHORD.vel_sense` stays 0.15 because a real jack plectrum is
  near-velocity-flat. The note's own reasoning - that `PROGRAM_TRIM_DB` could not fix a velocity
  RESPONSE error - was right. `_cal/derivation_v3.txt` is git-ignored scratch and is gone; the
  numbers survive in `wrk_docs/2026.07.22 - M-CAL v3 certified derivation report.md`.)
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
- [x] 2026.07.20 — **`gen_crate_lib.py` emits a non-rustfmt array for a SINGLE-file
  sample crate** — a one-element `static SAMPLES: [...] = [ (..),\n ];` that rustfmt
  rewrites to a one-line `= [(..)];`. Multi-file crates are unaffected (the multi-line
  form is already fmt-clean), so it only bites single-file crates (e.g.
  `ferrosintesis-samples-rain`), and only shows up in the workspace `cargo fmt --all
  --check` gate — a per-crate build looks fine. Fix at source in
  `tools/ferrosintesis-samples/gen_crate_lib.py` (emit the single-element case on one
  line, or run rustfmt on its output) so a future single-file regen is gate-clean
  without a manual `cargo fmt` pass.
  (Done 2026-07-25: the generator now shells out to rustfmt, which covers this case and
  the wider long-name one below. Verified by regenerating `-rain` into a scratch dir —
  byte-identical to the committed `src/lib.rs`.)

<!-- 2026.07.18: the items below are the low-value tail of the ferrosintesis
     subsystem audit; the meaningful findings were raised as MM-BUG-KILN-00005..00022.
     Parked here (not ledgered) per Arthur's "meaningful items; park trivia" call. -->

- [x] 2026.07.19 — **Steel (GM25) high-key wrap-gain LEVEL parity: the peak-normalized
  recorded take speaks ~4× (12 dB) above the now-ringing model at key 76, at EVERY
  velocity (measured 3.6–4.0× seam excess 2026.07.19 via a since-removed temp probe,
  `crates/ferrosintesis/src/sampler.rs`).** The decay cliff is fixed; what remains is a
  calibrated per-key wrap-gain taper for the guitar LA layer (sample gain should track
  the model's spoken level vs key, like item-1's velocity law did per velocity). Nylon
  passes (1.6–1.7×) — steel's take/model gap is the outlier. Also still documented:
  the vel-40 decay limit (corner scales with the velocity law; canary row pins it).
  (Already fixed: MM-REQ-KILN-00027, Satisfied 2026-07-25. The ~12 dB excess closed incidentally
  with the Phase-2 STEEL seam re-baselines plus the k=2 velocity law - no per-key taper was ever
  needed - and `la_steel_high_key_level_parity` now pins 0.8..2.2 wrapped/model over keys
  76/79/83 x vel 60/100. GM25 also moved to the Eastman picked bank. The stale `sampler.rs`
  comment that still called the gap open is corrected in this pass.)
- [ ] 2026.07.18 — **Other LA banks' zones are unguarded against fade dry-out at
  non-44.1 kHz rates** — the source-domain fade-budget guard + ~5 ms end taper added for
  guitars (`guitar_zone_fade_budget`, `LaVoice.end_taper`) cover GM24/25 only; any other
  wrapped zone whose `fade_end × 44100 × (f/root)` exceeds its length at 48/96 kHz still
  steps at dry-out (code-review A2). Generalize the taper (arming it globally breaks LA
  bit-identity pins, so it needs a coordinated re-pin) or assert budgets across all banks.
  (Re-verified 2026-07-25, and RESCOPED - the "at 48/96 kHz" framing is wrong. Source-domain
  consumption is `fade_end x 44100 x ratio`, which is rate-INDEPENDENT (the 44100/sr in `step`
  cancels the longer output-domain fade), and KILN-00061 already fixed the eligibility guard to
  key off the pitch ratio. What is real, at 44.1 kHz, is a SHORT zone against a LONG fade:
  `end_taper` is armed in exactly one constructor (`wrap_var_classified`, guitars only) and
  `guitar_zone_fade_budget` iterates only the four guitar banks, so ~25 other wrap sites are
  unguarded. Candidates found on disk: LA_CELESTA fade end 0.30 s vs celesta_F#6 0.222 s /
  celesta_C7 0.263 s; LA_SITAR 0.20 s vs sitar_G6 0.163 s / sitar_C6 0.192 s. Audibility is
  UNPROVEN - the tail may already be near-silent, and `rel_gain` may have closed. Next step is a
  measurement (extend `assert_wrap_seam` to celesta ~key 90 and sitar ~key 91), NOT a fix:
  arming `end_taper` globally moves every LA voice and needs the full render-diff inventory.)
- [ ] 2026.07.18 — **Closed vs pedal hi-hat are identical in the MODELED path, and the
  pedal hat carries a stick click it should not have.** Keys 42|44 share one `CymSpec`
  with `click: Some(...)` (`crates/ferrosintesis/src/drums.rs:~1661`). The sampled path
  distinguishes them (`HH_CLOSED` vs `HH_PEDAL`, `sampler.rs:~1942`), so this only bites
  `--no-samples`. Give 44 its own shorter/darker spec with the click removed.
  (Re-verified 2026-07-25, and WIDER than parked: not `--no-samples`-only. Key 44 also reaches the
  shared arm in a DEFAULT sampled build through ch-10 program change - PC 25 (Kit::V1) and PC 24
  (Kit::Synth, which forces samples=false) - and the brush kit collapses 42|44 too
  (`42 | 44 => brush_closed_hat`). Several albums are on the V1 kit. A `drums.rs` timbre change,
  so it needs the full render-diff inventory; the pedal-hat voicing itself is an ear call.)
- [ ] 2026.07.18 — **Ride bell (key 53) skipped the MetalPlate upgrade in the modeled
  path.** It is a fixed 6-mode inharmonic `d()` stack (`drums.rs:~1828`) while 49/51/52/
  55/57/59 route to `metal_plate`; the sampled `RIDE_BELL` has only 3 round robins. A busy
  bell ostinato is the most likely cymbal to sound mechanical. Modeled-path-only + niche.

- [x] 2026.07.18 — **Blown bottle (GM 76) still reads over-noisy vs a clean Helmholtz
  tone** (tonal 0.68 vs SC-55 1.00; roadmap Open Question 1). Round-1 made noise the
  primary source; the walk-back was never shipped, and its LA layer is a single C6 zone
  (`~1 octave` credible). Unused in committed albums → nil blast radius, hence parked.
  (Obsolete 2026-07-25: GM 76 no longer has an onset-only LA layer. The whole voice is now the
  `-bottle` recording via `BottleLoopVoice`; the modeled Wind bottle survives only as the
  `--no-samples` / out-of-range fallback. The single-C6-zone construction this describes is gone.)
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

- [x] 2026.07.18 — **No denormal (FTZ/DAZ) protection in recursive filters / reverb
  feedback.** `Biquad::process` (`dsp.rs:~519`), Comb/Allpass and CathedralLine states can
  enter denormal range as tails decay → per-sample CPU stalls on x86 (offline-render
  performance only, not an audio defect). Set MXCSR FTZ for the render, or add a tiny DC.
  (Already fixed: MM-BUG-KILN-00027 and -00100. `dsp.rs::flush_denormal` (floor 1e-34) runs inline
  every sample in `Comb::process`, `Allpass::process` and `CathedralLine`, and per block on bus
  biquads via `Biquad::flush`. Two things remain deliberate and documented, not gaps:
  `Biquad::process` does NOT flush inline (a flush there caused measured 24-LSB drift through
  near-unity voice feedback), and no global CPU FTZ/DAZ mode is set, which would not be
  bit-transparent. This was also the root cause of the `--solo 8` render hang below.)
- [x] 2026.07.18 — **`embedded_wav()` resolves by bare filename across 8 crates,
  first-match-wins, with no collision guard** (`sampler.rs:~49`, sequential `.or_else`
  chain keyed only on `name`). Harmless today (prefixes distinct) but a future generic
  name (`flute_A4.wav`) could silently shadow. Add a build-time global-uniqueness assert.
  (Done 2026-07-25: `payload.rs::no_two_asset_crates_ship_the_same_wav_basename`. The chain
  is 24 crates now, not 8, and there is no live collision today — 1156 WAVs, zero duplicate
  basenames — so this guards a future crate rather than fixing a present bug. It scans every
  `ferrosintesis-samples-*/samples/` on disk, a superset of the lookup chain, so no feature
  combination can slip past it. Adversarially verified per the repo's own rule: planting a
  duplicate `rain_loop.wav` in `-gong` turns it red with both crate names, and removing it
  turns it green again — an oracle nobody has seen fail is not evidence.)

- [ ] 2026.07.18 — **Two shipped drumkit banks are unreachable dead payload:**
  `CRASH_SIZZLE` and `SNARE_OFF` exist in the drumkit crate but no GM key maps to them
  (`sampler.rs:~2313` comment; absent from `sampled_drum` dispatch). Compiled-in but never
  selectable — GM has no dedicated key for either. Drop or wire behind a CC0 alt-bank.

- [x] 2026.07.18 — **Asset-crate/doc count drift.** `ferrosintesis-samples-orchestral`
  README says "embeds 147" but `FILE_COUNT=157`; drumkit README says "109 … WAVs" but
  `FILE_COUNT=188`. Also `crates/ferrosintesis/README.md:~87`'s feature-flags counts
  ("264 recorded attack transients … ~22 MiB") predate the newer asset crates — unverified.
  Fold into the next docs-curation sweep (code constants are the truth).
  (2026-07-20 partial: the `DESIGN.md:~99` GM 120–127 "toneless" clause that was also
  tracked here is fixed by the docs-drift sweep.)
  (Done 2026-07-25: enumerated ALL 25 crate READMEs rather than fixing the three named —
  the reported items are evidence of an unmaintained list, not a spec of the work. Only
  three claims were actually wrong. Orchestral: 147 → 166, bagpipe 8 → 17, and a missing
  10-file harpsichord row. Drumkit: 109 → 140, and its whole instrument list was wrong —
  today's cymbal split moved crash/sizzle/splash/china to `-drumkit2` and the README still
  described the crate as cymbals-only. `ferrosintesis/README.md`'s "264 transients / 22 MiB"
  was ALREADY fixed (now 1156 WAVs / 111 MiB, and `payload.rs` derives it). Mandolin's
  README is wrong too — deliberately left alone, it is tracked as open MM-BUG-KILN-00089.)

- [x] 2026.07.16 — **`LA_PROGRAMS` in voices.rs tests (~:19255) is stale vs the make()
  wiring.** It lists GM 2 (fully modeled electric grand — the samples flag changes
  nothing) and omits GM 41 (which DOES wrap the violin bank since round 2). Consequence
  today: the pitch-case harness skips 41's sampled leg and runs a no-op sampled leg on 2.
  The perceptual oracle's `sample_layer_engaged_at_probe_keys` (testutil.rs) carries the
  code-true list — sync `LA_PROGRAMS` to it, or derive both from one shared const.
  (Obsolete 2026-07-25: both claims are stale - `LA_PROGRAMS` has NOT contained GM 2 and HAS
  contained GM 41 since the 2026-07-14 voice-quality overhaul. It differs from `testutil.rs`'s
  `LA_WRAPPED` by {7, 76, 109} only, and that difference is correct and documented: the two lists
  answer different questions ("samples change the signal at all" vs "a `LaVoice::wrap` arm whose
  sample engages at probe key 48 or 72"). Nothing to sync.)
- [x] 2026.07.14 — **`check_dual_bank_registers` is dead code with a latent unpack bug.**
  `demos/ferrosintesis_reference/programs.py` (`check_dual_bank_registers`) is never
  called from verify.py or anywhere else, and its loop unpacks `ALT_BANK.items()` values
  as 3-tuples (`for program, (alt_register, _gesture, label) in ...`) while ALT_BANK
  values are strings — it would ValueError on first call. Its premise is obsolete: alt
  slots now INHERIT the default's register in `melodic_slots` (and STANDALONE_ALT
  entries carry their own), so registers can no longer silently diverge. Delete the
  function and the comment references to it, or rewrite it against REGISTER_MAY_DIVERGE
  if any check is still wanted. (Spotted during the round-2 tam-tam audition work.)
  (Done 2026-07-25: deleted, with all three claims proven first — no caller anywhere, and
  calling it really does raise `ValueError: too many values to unpack (expected 3)`, which
  I observed rather than inferred. Its premise is gone: `melodic_slots` passes
  `default.register` to the alt slot, so a divergence is unconstructable. The contrabass
  A/B-rigging story from its docstring is preserved on `melodic_slots`, which is where the
  invariant now lives — the knowledge was worth keeping even though the code was not.)

- [x] 2026.07.14 — **BowedString (GM 42/43) has a wolf band at keys 46–50 (B♭2–D3): the
  waveguide abandons its fundamental and mode-locks onto ~3·f0** (both programs, all seeds
  tried). Found by the `measure_bowedstring_loop_latency` sweep during the B4 tuning work
  (`crates/ferrosintesis/src/voices.rs`, `BowedString::new` / the `#[ignore]`d harness at the
  end of its test module): healthy keys imply a consistent loop latency L ≈ 4.0, but at keys
  46–50 the crossing-train period collapses to ~130–155 samples vs the ~300–380 ideal, and
  O-PITCH's spectrum check confirms the render's ONLY lattice is 3·f0 (f0/2f0/4f0 all
  ≤ 2.4 % of the 3·f0 line). A seed-dependent fringe extends to keys 43–45: pitch still
  lands on f0 there, but for some bow-force draws the regime turns noisy enough to bury
  the vibrato FM entirely (probed across seeds 7/11/13/17/23; keys 38 and 55 are clean on
  every seed). Likely the bow-friction operating point vs the delay-split (beta 0.127) in
  that register. Real audible defect in the cello/bass range of committed albums; O-PITCH
  and the vibrato oracle route around it (comments at `o_pitch_cases` and the vibrato
  test) — needs its own slice to fix the waveguide's mode stability, then move the oracle
  keys back in.
  (Already fixed: MM-BUG-KILN-00012, Closed. `beta` moved 0.127 -> 0.140 (near 1/7) in
  `BowedString::new`, and a LIVE oracle `bowed_string_wolf_band_holds_fundamental` covers all 5
  keys x 3 seeds x both programs at <=30 cents; `o_pitch_cases` now says "former wolf band".
  The keys 43-45 vibrato-burial residual is NOT fixed - re-parked as its own item below.)
- [x] 2026.07.14 — **altbank.rs Bowed vibrato is the same 16×-slow idiom bug as
  MM-BUG-KILN-00004**: `altbank.rs:191` builds `vib: Sine::new(vib_rate·…, sr, 0.0)` at the
  FULL sample rate but `render` advances it only under `is_multiple_of(CTRL)`
  (`altbank.rs:215-217`), so the CC0 alt-bank bowed voices' vibrato runs at rate/16 — the
  systemic audit in the voice-quality HLD §2.3 predicted exactly this fourth instance.
  Fix is one line (route through `voices.rs::control_lfo` or build at `sr/CTRL`); left
  untouched here because the B3 slice's mandate was BowedString-only.
  (Already fixed: `altbank.rs` now builds the LFO at `sr / CTRL as f32`, with an explanatory
  comment and a regression test pinning that it is ticked once per CTRL samples.)
- [x] 2026.07.13 — **No reusable render-diff harness exists, though CLAUDE.md mandates the
  render-diff inventory** for any voices.rs/engine.rs/drums.rs/sampler.rs change. Every task
  hand-rolls it (build a baseline binary in a throwaway worktree, render `render_opus.py::ALBUMS`
  with both binaries, `cmp`). A worktree-hygiene pass found one agent's ad-hoc scripts
  (`renderdiff.ps1`/`refresh_affected.py`/`spotcheck.py`) but they were hardcoded to specific
  worktree paths and not reusable, so they were retired with the `salvage-orphan-scraps` archive.
  Worth writing a small parameterized `tools/render-diff` (baseline-ref + head-ref → per-album
  WAV-hash DIFF/same/FAIL table) so the mandated inventory isn't re-invented each task. Note the
  workflow shifted: `.opus` is now git-ignored build output rendered via `build.py`, so a fresh
  harness should diff `.wav` renders, not committed assets.
  (Obsolete 2026-07-25: superseded - `tools/render-diff/render_diff.py` was built on 2026.07.13 and
  is now the mandated harness cited by CLAUDE.md. This entry is the request; the swept `[x]`
  entry recording its delivery was the answer. Two of its residual defects are handled in this
  pass: the ch-10 mis-attribution is fixed, and bank-awareness is promoted to a requirement.)
- [x] 2026-07-20 — **Stale `.rs` doc comments the docs-drift sweep verified but could not fix
  (docs-lane branch, no source edits):** `drums.rs:1358` claims `make` returns "`None` for
  unmapped keys" — false, every arm returns `Some` (generic tick at `drums.rs:2023`);
  `sampler.rs:903/:1137/:1479` grand/kawai/honkytonk bank docs still describe the pre-07.18
  GM 0-centric piano mapping (kawai is now the GM 1 DEFAULT, honkytonk the GM 3 default);
  `voices.rs:22978` justifies the SFX tuning-test exclusion with the retired "toneless-noise
  fallbacks" claim; `engine.rs:1-11` header lists only the v0.7 controllers (omits
  CC2/CC66/CC84/poly-AT); orphaned MS Basic bottle onset bank still embedded + prewarmed
  (`sampler.rs:2154-2164`, `:2389`) with stale WD-O10/dispatch comments
  (`voices.rs:22416-22419`, `:12115`). One comment-only source pass, no bump (pure docs in
  code). Also verify `CLAUDE.md`'s publish-order claim ("`-core` → `-orchestral` →
  `ferrosintesis`") against the actual `=x.y.z` pins — there are ~22 sample crates now.
  (Done 2026-07-25, all comment-only — `git diff` confirms not one non-comment line moved,
  so no render-diff applies. `drums.rs::make` now says the `Option` is never `None`;
  grand/kawai/honkytonk banks state their real routes (GM 0 CC0 alt 1 / GM 1 default /
  GM 3 default); the SFX exclusion cites "unpitched by design" instead of the retired
  toneless-noise claim; the `engine.rs` header adds CC2, CC84 and poly-AT and drops the
  v0.7-specific framing. CC66 was already listed — that part had been fixed. The orphaned
  `bottle_bank` accessor now says outright that it is a RETIRED route kept only because the
  crate is published; whether to actually drop it is a payload decision left for Arthur.
  The CLAUDE.md publish-order half is fixed in its own commit. The WD-O10 comments the note
  flagged turned out to be ACCURATE — verifying beat fixing on those.)

- [ ] 2026.07.13 — `distinctness::Why` (`crates/ferrosintesis/src/testutil.rs:1139`)
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
- [x] 2026.07.13 - `render_opus.py --jobs 4` can emit a different Opus container
  from a subsequent `--jobs 1` render of the same MIDI and synth, while decoded
  float PCM is SHA-256 identical. Seen on Atlas of Becoming 05 during cello-v2
  recovery: the first parallel encode changed container hash on a single-worker
  repeat; two subsequent single-worker encodes were byte-identical. Do not use raw
  Opus equality as the audio oracle. Investigate whether `ropusenc` stream serial
  assignment depends on parallel launch timing, then make it deterministic or
  compare decoded PCM in render-refresh tooling.
  (Obsolete 2026-07-25: `render_opus.py` no longer exists, and nothing in the repo compares opus
  BYTES any more. `render-catalog`'s only goldens are the argv handed to `ropusenc` (a text
  comparison), it passes no serial argument, and `.opus` is git-ignored build output so no
  refresh-diff can trip over container non-determinism. The `ropusenc` behaviour may well still
  exist; nothing here depends on it.)
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

- [x] 2026-07-13 — **MSRV could be lowered from 1.87 to ~1.70** by replacing `is_multiple_of`
  (`altbank.rs:215,527`, `voices.rs:2311,2340`) with `% CTRL == 0` and `is_none_or`
  (`altbank.rs:471`) with `map_or(true, ..)`. Both are provably equivalent on unsigned ints,
  but they sit in DSP hot loops, so the synth-change policy applies: needs the render-diff
  inventory to confirm bit-identical output. Low value, non-zero cost — only worth it if a
  low MSRV is a goal for the published crate.
  (Obsolete 2026-07-25: the premise is measurably false. `Cargo.lock` is `version = 4`, which
  requires cargo 1.78, and every gate runs `--locked` - so 1.78 is a hard floor no source edit
  can lower. `engine.rs` also uses `div_ceil` (1.73). The real ladder is 1.87 -> 1.82 (drop
  `is_multiple_of`, 19 sites not 4) -> 1.78 (drop `is_none_or`), and clippy's
  `manual_is_multiple_of` would flag the rewrite back. No stated consumer needs a lower MSRV.)
- [x] 2026-07-13 — **Ship a `PROVENANCE.md` inside each samples `.crate`.** The per-file
  source map (202 outputs → upstream URLs) lives only in `tools/ferrosintesis-samples/prepare.py`,
  which is outside both packages' `include` lists — so a crates.io consumer gets the prose
  summary and the CC0 text, but must follow a GitHub link for the evidence. CC0 requires no
  attribution so this is not a legal gap, but crates.io tarballs are immutable forever while
  repos are not. `prepare.py` already holds every field needed to emit it.
  (Already fixed: commit `96e2a47`, closing MM-BUG-KILN-00069. All 25 sample crates ship a
  `PROVENANCE.md` AND list it in their Cargo `include`, and two oracles hold the line -
  `inventory.rs` checks both existence and packaging, `provenance.rs` pins a SHA-256 for every
  committed upstream source. The named worry - evidence reachable only through `prepare.py`,
  outside the include lists - no longer applies.)
- [ ] 2026-07-13 — **`ferrosintesis-cli` is `publish = false`**, so `cargo install ferrosintesis`
  will not work — the library publishes, the renderer binary does not. Deliberate per the
  2026.07.09 HLD, but it is a product decision worth restating (and worth revisiting at 1.0):
  if the CLI should ship, it needs `README.md`, `LICENSE-*`, an `include` list, and to be
  published last.

- [ ] 2026-07-16 — **The 8 `drum_*` WAVs in `ferrosintesis-samples-orchestral` are DEAD
  WEIGHT — nothing loads them.** `crash1`/`kick_v3`/`snare2_v5`/`sus_cymb1` (2 RRs each) are
  referenced only by the crate's own inventory array
  (`crates/ferrosintesis-samples-orchestral/src/lib.rs`); no `ferrosintesis` code reads them
  (`grep -rn '"drum_' crates/ferrosintesis/src/` is empty). They are the pre-drumkit VSCO
  overlays, superseded when `ferrosintesis-samples-drumkit` (Virtuosity, 188 files) landed and
  `sampler::sampled_drum` started routing every ch10 key to `kit::*` instead. They still cost
  ~400 KB of `include_bytes!` payload in every binary, and they still get regenerated by
  `prepare.py`'s `DRUM_SOURCES`. Found while measuring the fade-in blast radius (they were 8 of
  the 66 re-cut files — and provably could not have affected a single render). Removing them
  means: drop `DRUM_SOURCES` from `prepare.py`, drop the 8 rows + 8 files, `FILE_COUNT` 139 ->
  131, and re-pin `test_all_samples_route_to_the_expected_package`. Check nothing external
  depends on the names first — the crate is published.
  (Re-verified 2026-07-25: dead in the synth - `grep -rn '\"drum_' crates/ferrosintesis/src/` is
  still empty and nothing outside the crate's own inventory array names them. Two corrections to
  the note's numbers: FILE_COUNT goes 166 -> 158, not 139 -> 131, and `test_prepare.py`'s pins go
  210 -> 202 and 139 -> 131. And one thing the note did not know: two HLDs
  (`2026.07.13 - HLD - cymbal plate synthesis`, `2026.07.14 - HLD - MetalPlate V4`) cite
  `drum_crash1_ff_rr1.wav` as the REAL-CYMBAL MEASUREMENT REFERENCE for the shipped MetalPlate
  model. No code reads it, but deleting it deletes the provenance of a shipped model's
  calibration. Still a published-payload decision for Arthur; the README now at least states the
  files are superseded. NOTE the CLAUDE.md rule that unused-by-our-albums is not evidence of
  death - the stronger claim here is that no GM key can reach them, which does hold.)
- 2026.07.17 — **ChoirV2 CC70 cluster-shade is coupled to the F3 formant gain** (`sf_open =
  vgains[2]/sf_ref_g3`, voices.rs:6103; the F5 adversarial finding). It SATURATES when the program's
  default F3 gain is on the floor, so a dark-voiced preset silently kills the CC70 vowel morph's
  cluster differentiation. Worked around in the darkening slice by keeping aah's default `vgains[2]`
  at 0.15 (off the floor). A clean fix: give `sf_open` its own state driven by an EXPLICIT cluster-open
  control from the CC70 path, independent of the F3 formant gain — a dedicated CC70 slice, not urgent.
  (Re-verified 2026-07-25: still real, `sf_open = (vgains[2] / sf_ref_g3).min(1.3)`, and the aah
  workaround is still load-bearing and commented as such. One thing to check first when someone
  picks this up: the oracle `choir2_singers_formant_cluster` documents aah's default vgains[2] as
  0.08 while the source says 0.15 - one of the two is stale.)
- 2026.07.18 — XG/GS extra drum channels: XG bank MSB (CC0) == 127 is now routed to the
  drum path (`engine.rs` `Strip.xg_drum` / `Active.is_drum`), but two adjacent cases are
  deferred: (1) **Roland GS** declares a rhythm part via SysEx (`F0 41 .. 40 1x 15 mm F7`,
  "Use for Rhythm Part"), not bank select — needs SysEx part-mode parsing to give GS files
  the same fix. (2) **XG SFX kit** (bank MSB == 126) is a note-mapped effects bank, distinct
  from GM drums; it currently stays melodic (routing it through `drums::make` would be wrong).
  Add a dedicated path if a corpus file needs it. See `wrk_docs/2026.07.18 - HLD - XG
  drum-kit bank routing (CC0=127).md` (non-goals).

- 2026.07.18 — XG-drum channels use the default V3 kit regardless of the XG kit number
  (16=Rock, 8=Room, 40=Brush…); ch9 only distinguishes 40=Brush. If XG files want kit-accurate
  percussion, map the kit-select program to `drums::Kit` for `xg_drum` strips too
  (`engine.rs` `program_change`, currently gated `ch == 9`).

- 2026.07.18 — Pre-existing (NOT introduced by the GS change): `midi.rs::parse` does not
  reset running status to 0 after a meta (0xFF) or SysEx (0xF0/0xF7) event. Well-formed
  SMFs always emit an explicit status after meta/sysex, so it's correct for valid files;
  a MALFORMED file using running status straight after a meta/sysex would misparse (treat
  data as another meta). Cheap hardening if ever wanted: `status = 0;` in the 0xFF and
  0xF0|0xF7 arms. Flagged by the GS external review; left out of the GS task's scope.
  (Obsolete 2026-07-25 - and the proposed fix is now HARMFUL. MM-BUG-KILN-00096 (Closed) split the
  single `status` variable so `running_status` latches ONLY for channel-voice bytes. The policy
  is deliberate and commented: SMF 1.0 says meta/SysEx cancel running status, but real sequencers
  emit files that continue it, so ferrosintesis carries the latch across rather than desyncing.
  Adding `status = 0;` in those arms would REINTRODUCE a failure on exactly the malformed files
  this now plays. Three tests pin it. Do not apply.)
- [x] 2026.07.19 — **Three samples-off tests are not `cfg`-gated to `embedded-samples`,
  so `cargo test -p ferrosintesis --no-default-features` reports them as failures**
  (positive sample-engagement controls that hard-code `samples=true`):
  `gm0_grand_and_gm1_upright_are_distinct_instruments` (`crates/ferrosintesis/src/voices.rs:14185`),
  `keyboard_voices_programs_4_7_do_not_use_acoustic_piano_voice` (`voices.rs:13092`),
  `wd_o10_routing_sample_policy_and_lifecycle` (`voices.rs:21290`). Spotted during the
  MM-BUG-KILN verify-close pass. May be *intended* (MM-BUG-KILN-00020 establishes that
  samples-off is a deliberately-not-green config that should fail loudly) — triage
  whether to `#[cfg_attr(not(feature="embedded-samples"), ignore)]` these three so the
  only samples-off failure is 00020's guard, or leave them as extra loud signal.
  (Already fixed: commit `dfc91dd`, closing MM-BUG-KILN-00090. The triage question is answered too,
  and not with the blanket gate the note offered: only
  `gm0_grand_and_gm1_upright_are_distinct_instruments` is whole-gated on the feature (the
  property is meaningless without two distinct recordings); the other two keep their modeled
  clauses live in BOTH builds and put only the sample-engagement assert behind a runtime
  `embedded_samples_available()`. `--no-default-features` is now a required gate step, so this
  cannot regress silently.)
- [x] 2026-07-19 ferrosintesis render HANG: `ferrosintesis "<Hollow Hill Pt 1>.mid" --solo 8 -o x.wav` (nylon, prog 24) runs >400s and is killed, on BOTH the pre-Phase-1 baseline binary AND with --peak-normalize (so not LUFS, not my pluck change). The FULL-mix render of the same file finishes in ~2min, and --solo 7/10/14 finish in ~2min — only --solo 8 pathologically slow. Suspect a stuck/never-reaping voice or LA-sample loop specific to that channel. crates/ferrosintesis/src/engine.rs (solo path / voice reap) + sampler.rs. Repro: Hollow Hill Pt 1, --solo 8.
  (Already fixed: MM-BUG-KILN-00027, Closed 2026-07-21, two-eyes verified - and I re-ran the exact
  repro rather than assuming: 65 s, exit 0, full 148.5 MB WAV, max polyphony 8. It was never a
  stuck voice. A sparse `--solo` mix leaves the always-running reverb / chorus / echo /
  sympathetic buses churning DENORMAL arithmetic in their IIR tails - a ~10x crawl of a
  completing render, not a hang. Fixed by per-block `flush_denormal` on bus feedback state.
  Fixed two days after it was parked; nobody came back to strike it.)
- [x] 2026-07-20 **render-diff harness mis-attributes ch-10 (drum) program changes as
  melodic GM programs** (`tools/render-diff/render_diff.py:116-118`). `scan()` does
  `for ch, ps in ch_prog.items(): if ch in ch_sounded: progs.update(ps)` — it adds
  channel 9's program changes to `progs` too, so an album selecting a ch-10 DRUM KIT
  via PC N (e.g. PC 25 = the "Original" kit) is flagged as using "GM N" (melodic). This
  produces spurious NOT-REACHED rows: the 2026.07.20 pluck render-diff reported 8
  NOT-REACHED GM25 albums (Slipstream, Three-Sixty/-One) that actually use PC25 only on
  ch-10. Fix: skip `ch == 9` in the progs loop (ch-10 program = kit, already tracked via
  drum `keys`). Low-risk, isolated to the harness; do when next touching render-diff.
  (Done 2026-07-25: `scan()` now skips `ch == 9` in the program roll-up. Verified on the
  three named albums — Slipstream 01/02/03 reported GM25 before the fix and do not after,
  with their drum keys untouched.)

- [ ] 2026-07-20 **GOLDEN mix fixture has pre-existing within-tolerance drift on 3
  non-pluck rows** (`crates/ferrosintesis/src/testutil.rs` GOLDEN table). Capturing
  the full fixture at the Phase-2 branch base (963def2) showed ch 0 nylon centroid
  899→819 Hz, ch 4 drive 808→846 Hz, and the ch 8 strings canary 2381→2139 Hz all
  ALREADY read the new values at the base — i.e. the committed rows are stale
  patchwork that only passes on the ±20 % `CENTROID_TOL`. The Phase-2 STEEL/JAZZ
  task deliberately re-pinned ONLY ch 1/ch 2 (its own migrated presets) + master
  peak and left these three stale (not this task's change; verified base==HEAD, so
  no contamination). A golden-hygiene pass should re-run `print_golden_fixture` and
  re-pin all rows so the fixture reflects reality instead of leaning on tolerance.
  (Re-measured 2026-07-25, and the conclusion FLIPPED — do not re-pin yet. The table has
  been re-captured twice since this note (k=2 velocity law, DRUM_FORWARD removal), so none
  of the three quoted "committed" values is current. Running `print_golden_fixture` on this
  box against HEAD gives ch 0 −39.19/1079.7 vs committed −38.45/1048.8, ch 4 −33.04/811.3
  vs −32.54/843.8, ch 8 −34.65/2090.1 — an EXACT match, so the strings canary this note
  named is no longer drifting at all — and master peak 1.37333 vs 1.37866. So ~0.5–0.7 dB
  and ~3–4 % centroid drift is real on two rows. BUT re-pinning is not obviously right:
  ferrosintesis renders are NOT bit-reproducible across fleet machines (the swept
  2026.07.12 entry), and these tolerances are what absorb that. Re-pinning to one box's
  numbers could red the fixture on another. Needs Arthur: either designate a gating machine
  for golden captures, or accept the tolerance as doing its job and drop this item.)

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
- [x] 2026-07-20 GM109 bagpipe zone coverage: the FreePats archive holds 26 WAVs (24 chanter takes + 2 drones) but `BAGPIPE_SOURCES` bakes only 8, ignoring A#4/B4/C#5/D#5/E5/F5/F#5 and every `_32` round robin. With `find_loop` now able to cut a clean short loop from any steady take, filling the ~2.5-semitone gaps (and adding an RR2) is cheap and would cut the repitch stretch. `tools/ferrosintesis-samples/prepare.py:572` (BAGPIPE_SOURCES), `crates/ferrosintesis/src/sampler.rs:2099` (chanter zones).
  (Already fixed: MM-REQ-KILN-00025, Satisfied 2026-07-25. `BAGPIPE_SOURCES` now bakes 17 members
  (2 drones + 10 chanter pitches + 5 `_32` round robins), worst repitch stretch ~1.9 semitones.
  D#5/E5/F5 stay OUT deliberately - both takes are unloopable there (best wrap -12.6/-5.3/+1.3 dB
  against a -14 dB gate) and were excluded rather than weakening `BAGPIPE_MAX_WRAP_DB`. Do not
  re-hunt those three without a better source.)
- [x] 2026-07-20 `LoopVoice` has NO intrinsic animation while `SaxLoopVoice` runs a +/-0.22% read-rate random walk explicitly commented "defeats the loop-tell" (`sampler.rs:SAX_DRIFT_MAX`). Now that the bagpipe loops are ~65 ms they repeat ~15x/s; a slow drift would dissolve any residual static "tell". Add the DRIFT only — NOT the sax tremolo: `bp_o1_bagpipe_chanter_is_constant_amplitude_saxes_keep_dynamics` pins constant amplitude, and constant bag pressure is the instrument. `crates/ferrosintesis/src/sampler.rs:LoopVoice::render`.
  (Already fixed: MM-REQ-KILN-00026, Satisfied. `LoopVoice` carries `drift`/`drift_target` driven
  by the same walk as the sax, sharing `SAX_DRIFT_MAX`/`SAX_DRIFT_SAMP`. The constraint held -
  drift only, no tremolo - so the constant-amplitude chanter oracle still passes.)
- [x] 2026-07-24 `gen_crate_lib.py` emits a generated `src/lib.rs` that is NOT rustfmt-clean once a bank's WAV names are long: it writes each entry as a one-line `("name.wav", include_bytes!("../samples/name.wav")),` and rustfmt wraps that past ~100 chars. Every existing asset crate happens to have short enough names to fit, so the trap only fires on a NEW bank — the mandolin's `mandolin_G3_rr1.wav` style names crossed the limit and failed the integration gate's `cargo fmt --all -- --check` after everything else was green. Either have the generator emit the wrapped form, or make it shell out to `rustfmt` on the file it just wrote. `tools/ferrosintesis-samples/gen_crate_lib.py`.
  (Done 2026-07-25: shells out to rustfmt. The threshold is not ~100 chars — an entry is
  `2*len(name)+35` wide against rustfmt's 60-char `fn_call_width`, so ANY name over 12
  characters wraps, which is why 23 of the 25 generated crates already carry the wrapped
  form and every past regen was silently followed by a manual `cargo fmt`. Verified a
  long-name crate now passes `rustfmt --check`, and `-rain` still reproduces byte-exactly.)

- [x] 2026-07-24 `tools/ferrosintesis-samples/test_prepare.py` (27 tests) is not run by any gate: `.deltic-integrate.toml`'s `workspace` component lists `tools/` in its paths but every command in its gate is cargo, so a change under `tools/` triggers a Rust-only gate and the Python suite never runs. Noticed while adding the KILN-00062 cache tests — they would have landed unexecuted by CI-equivalent. Same shape as MM-BUG-KILN-00070 (a real configuration no gate builds). Adding `{ program = "python", args = ["-m", "unittest", "discover", "-s", "tools/ferrosintesis-samples"] }` would close it, but check the runner has a `python` on PATH first. `.deltic-integrate.toml`.
  (Done 2026-07-25: added to both the `fallback` list and the `workspace` component gate.
  The suite is now 32 tests, runs green in 7.5 s from the repo root, needs no network — it
  monkeypatches `urlretrieve` — and leaves the tree clean. `python` and `python3` are both
  on PATH here, and the repo already requires python for every album build. CAVEAT for
  Arthur: bare `python` often does not exist on a Debian/WSL runner; if a drain ever fails
  there, the fix is to switch this one step to `python3`.)

- [x] 2026-07-24 Offline renders may not PARALLELISE on a 24-core box: one `ferrosintesis` render measured ~12x realtime, but six concurrent renders gave ~10x realtime AGGREGATE (442 MB of WAV in 4m06s) — i.e. six processes did roughly the work of one. Not a controlled comparison (different tracks each way), so it needs a proper A/B on the SAME file set before anyone believes it. Not disk-write bound: `wav.rs:write_wav` buffers and emits the whole PCM block in one `write_all`. Not memory bound (96 GB, 54 GB free). If it holds, `render-catalog --jobs` is buying nothing and a full catalog render is ~2 h instead of ~10 min. Noticed while running the render-diff inventory for the GM 8/9/10 echo-send change. `crates/render-catalog/src/main.rs` (jobs), `crates/ferrosintesis/src/offline.rs`.
  (Obsolete 2026-07-25: the premise no longer matches the code. That measurement was six
  ferrosintesis PROCESSES - the retired `render_opus.py` model - where each process privately
  decodes its own copy of the 114 MB embedded bank, wholly redundant memory bandwidth.
  `render-catalog` renders IN-PROCESS through the library under one `std::thread::scope` with an
  atomic work cursor, sharing one decoded bank; the only `Mutex` in the synth is `#[cfg(test)]`.
  Nothing to fix. If the number is still wanted, `--jobs 1` vs `--jobs 6` on one file set
  answers it in minutes.)

- [ ] 2026-07-25 - **BowedString keys 43-45: for some bow-force draws the bass regime turns noisy
  enough to bury the vibrato FM entirely.** Split out of the 2026.07.14 wolf-band entry, whose main
  claim (keys 46-50 mode-locking onto 3*f0) was fixed by MM-BUG-KILN-00012 (beta 0.127 -> 0.140).
  This part was NOT fixed: pitch lands correctly on f0 at 43-45, but the vibrato oracle still routes
  AROUND those keys, and the comment recording why is still live in `crates/ferrosintesis/src/
  voices.rs` at the vibrato test ("same instability family as the wolf band"). Probed across seeds
  7/11/13/17/23; keys 38 and 55 are clean on every seed. Re-parked so the residual does not
  disappear with its parent entry.
