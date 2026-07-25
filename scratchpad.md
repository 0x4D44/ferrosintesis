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

- [ ] 2026.07.25 — **`render-diff` is not bank-aware, so an alt-bank-only voice
  change is misclassified as contamination or not-reached** —
  `tools/render-diff/render_diff.py:scan` records only program numbers and drum
  keys; it ignores CC0/CC32. KILN-00049 changed DRIVE_LEAD only on GM29/30
  alternate banks: the full 124-MIDI diff moved exactly 11 tracks, and a
  bank-aware scan proved those same 11 are the complete CC0-nonzero GM29/30 set,
  but the tool called them contamination without that context. Extend the
  touched identity and MIDI scanner to include bank selectors.

- [ ] 2026.07.24 — **8 clean body-knock (tap) samples were captured in the GM120 fret-noise
  session but PARKED** — `DR0000_0204` (the taps at ~26/56/60/61 s, and more), soundboard/side
  knocks. They are the raw material for fixing the guitar's thin note-off `stop_thump`
  (currently modeled). Not folded into the fret-noise change (kept it focused, Arthur's steer).
  Source archive: `samples/fret-noise-eastman-e1d/DR0000_0204.opus`. A future job: cut the taps,
  bake, and drive the guitar note-off thump from them.

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

- [ ] 2026.07.22 — **GM6 Harpsichord fails the M-CAL velocity guard at 9.6 dB** — its
  ferro-vs-SC-55 level difference changes by 9.6 dB between v72 and v110, i.e. a
  velocity-RESPONSE mismatch, not a level offset (a static `PROGRAM_TRIM_DB` entry cannot
  fix it). It is the flagship +6 dB piano-family trim, so worth a look.
  Evidence: `_cal/derivation_v3.txt`, GM6 row (`vel 9.6`); reproduce with
  `derive_trims.py` on a full-128 certified run. Raised from the M-CAL v3 derivation review.

- [ ] 2026.07.22 — **M-CAL residual watchlist: the metric disagrees with ear-vetted trims
  on the slow-attack families** — GM56/57 brass (−6.7/−6.3 dB), GM67 (−4.8), GM48/50/51
  ensembles (+3.7..+4.3). Either the single-held-note probe biases slow-attack voices, or
  those shipped trims are stale. Only listening settles which; do NOT renumber them on the
  metric alone. Evidence: residual-oracle section of `_cal/derivation_v3.txt`.

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

- [ ] 2026.07.19 — **Steel (GM25) high-key wrap-gain LEVEL parity: the peak-normalized
  recorded take speaks ~4× (12 dB) above the now-ringing model at key 76, at EVERY
  velocity (measured 3.6–4.0× seam excess 2026.07.19 via a since-removed temp probe,
  `crates/ferrosintesis/src/sampler.rs`).** The decay cliff is fixed; what remains is a
  calibrated per-key wrap-gain taper for the guitar LA layer (sample gain should track
  the model's spoken level vs key, like item-1's velocity law did per velocity). Nylon
  passes (1.6–1.7×) — steel's take/model gap is the outlier. Also still documented:
  the vel-40 decay limit (corner scales with the velocity law; canary row pins it).

- [ ] 2026.07.18 — **Other LA banks' zones are unguarded against fade dry-out at
  non-44.1 kHz rates** — the source-domain fade-budget guard + ~5 ms end taper added for
  guitars (`guitar_zone_fade_budget`, `LaVoice.end_taper`) cover GM24/25 only; any other
  wrapped zone whose `fade_end × 44100 × (f/root)` exceeds its length at 48/96 kHz still
  steps at dry-out (code-review A2). Generalize the taper (arming it globally breaks LA
  bit-identity pins, so it needs a coordinated re-pin) or assert budgets across all banks.

- [ ] 2026.07.18 — **Closed vs pedal hi-hat are identical in the MODELED path, and the
  pedal hat carries a stick click it should not have.** Keys 42|44 share one `CymSpec`
  with `click: Some(...)` (`crates/ferrosintesis/src/drums.rs:~1661`). The sampled path
  distinguishes them (`HH_CLOSED` vs `HH_PEDAL`, `sampler.rs:~1942`), so this only bites
  `--no-samples`. Give 44 its own shorter/darker spec with the click removed.

- [ ] 2026.07.18 — **Ride bell (key 53) skipped the MetalPlate upgrade in the modeled
  path.** It is a fixed 6-mode inharmonic `d()` stack (`drums.rs:~1828`) while 49/51/52/
  55/57/59 route to `metal_plate`; the sampled `RIDE_BELL` has only 3 round robins. A busy
  bell ostinato is the most likely cymbal to sound mechanical. Modeled-path-only + niche.

- [ ] 2026.07.18 — **Blown bottle (GM 76) still reads over-noisy vs a clean Helmholtz
  tone** (tonal 0.68 vs SC-55 1.00; roadmap Open Question 1). Round-1 made noise the
  primary source; the walk-back was never shipped, and its LA layer is a single C6 zone
  (`~1 octave` credible). Unused in committed albums → nil blast radius, hence parked.

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

- [ ] 2026.07.18 — **No denormal (FTZ/DAZ) protection in recursive filters / reverb
  feedback.** `Biquad::process` (`dsp.rs:~519`), Comb/Allpass and CathedralLine states can
  enter denormal range as tails decay → per-sample CPU stalls on x86 (offline-render
  performance only, not an audio defect). Set MXCSR FTZ for the render, or add a tiny DC.

- [ ] 2026.07.18 — **`embedded_wav()` resolves by bare filename across 8 crates,
  first-match-wins, with no collision guard** (`sampler.rs:~49`, sequential `.or_else`
  chain keyed only on `name`). Harmless today (prefixes distinct) but a future generic
  name (`flute_A4.wav`) could silently shadow. Add a build-time global-uniqueness assert.

- [ ] 2026.07.18 — **Two shipped drumkit banks are unreachable dead payload:**
  `CRASH_SIZZLE` and `SNARE_OFF` exist in the drumkit crate but no GM key maps to them
  (`sampler.rs:~2313` comment; absent from `sampled_drum` dispatch). Compiled-in but never
  selectable — GM has no dedicated key for either. Drop or wire behind a CC0 alt-bank.

- [ ] 2026.07.18 — **Asset-crate/doc count drift.** `ferrosintesis-samples-orchestral`
  README says "embeds 147" but `FILE_COUNT=157`; drumkit README says "109 … WAVs" but
  `FILE_COUNT=188`. Also `crates/ferrosintesis/README.md:~87`'s feature-flags counts
  ("264 recorded attack transients … ~22 MiB") predate the newer asset crates — unverified.
  Fold into the next docs-curation sweep (code constants are the truth).
  (2026-07-20 partial: the `DESIGN.md:~99` GM 120–127 "toneless" clause that was also
  tracked here is fixed by the docs-drift sweep.)

- [ ] 2026.07.16 — **`LA_PROGRAMS` in voices.rs tests (~:19255) is stale vs the make()
  wiring.** It lists GM 2 (fully modeled electric grand — the samples flag changes
  nothing) and omits GM 41 (which DOES wrap the violin bank since round 2). Consequence
  today: the pitch-case harness skips 41's sampled leg and runs a no-op sampled leg on 2.
  The perceptual oracle's `sample_layer_engaged_at_probe_keys` (testutil.rs) carries the
  code-true list — sync `LA_PROGRAMS` to it, or derive both from one shared const.

- [ ] 2026.07.14 — **`check_dual_bank_registers` is dead code with a latent unpack bug.**
  `demos/ferrosintesis_reference/programs.py` (`check_dual_bank_registers`) is never
  called from verify.py or anywhere else, and its loop unpacks `ALT_BANK.items()` values
  as 3-tuples (`for program, (alt_register, _gesture, label) in ...`) while ALT_BANK
  values are strings — it would ValueError on first call. Its premise is obsolete: alt
  slots now INHERIT the default's register in `melodic_slots` (and STANDALONE_ALT
  entries carry their own), so registers can no longer silently diverge. Delete the
  function and the comment references to it, or rewrite it against REGISTER_MAY_DIVERGE
  if any check is still wanted. (Spotted during the round-2 tam-tam audition work.)

- [ ] 2026.07.14 — **BowedString (GM 42/43) has a wolf band at keys 46–50 (B♭2–D3): the
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

- [ ] 2026.07.14 — **altbank.rs Bowed vibrato is the same 16×-slow idiom bug as
  MM-BUG-KILN-00004**: `altbank.rs:191` builds `vib: Sine::new(vib_rate·…, sr, 0.0)` at the
  FULL sample rate but `render` advances it only under `is_multiple_of(CTRL)`
  (`altbank.rs:215-217`), so the CC0 alt-bank bowed voices' vibrato runs at rate/16 — the
  systemic audit in the voice-quality HLD §2.3 predicted exactly this fourth instance.
  Fix is one line (route through `voices.rs::control_lfo` or build at `sr/CTRL`); left
  untouched here because the B3 slice's mandate was BowedString-only.

- [ ] 2026.07.13 — **No reusable render-diff harness exists, though CLAUDE.md mandates the
  render-diff inventory** for any voices.rs/engine.rs/drums.rs/sampler.rs change. Every task
  hand-rolls it (build a baseline binary in a throwaway worktree, render `render_opus.py::ALBUMS`
  with both binaries, `cmp`). A worktree-hygiene pass found one agent's ad-hoc scripts
  (`renderdiff.ps1`/`refresh_affected.py`/`spotcheck.py`) but they were hardcoded to specific
  worktree paths and not reusable, so they were retired with the `salvage-orphan-scraps` archive.
  Worth writing a small parameterized `tools/render-diff` (baseline-ref + head-ref → per-album
  WAV-hash DIFF/same/FAIL table) so the mandated inventory isn't re-invented each task. Note the
  workflow shifted: `.opus` is now git-ignored build output rendered via `build.py`, so a fresh
  harness should diff `.wav` renders, not committed assets.

- [ ] 2026-07-20 — **Stale `.rs` doc comments the docs-drift sweep verified but could not fix
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

- [ ] 2026.07.13 — `distinctness::Why` (`crates/ferrosintesis/src/testutil.rs:1139`)
  is now a **single-variant enum** (`Collapse(u8)`) after Stage 4 deleted the last
  `Legit` pair (synth strings 50/51). Not wrong, but a mild smell: it forced a
  plain destructuring `let Why::Collapse(stage) = why;` at the once-`if let` site.
  If it stays single-variant through Stages 5/7a/7b (none of which add `Legit`),
  collapse it to a bare stage id: `ALLOW: &[(u8, u8, u8)]` and `allow_reason ->
  Option<u8>`. Deferred to avoid widening Stage 4 into a shared-infra refactor.

- [ ] 2026.07.13 - `render_opus.py --jobs 4` can emit a different Opus container
  from a subsequent `--jobs 1` render of the same MIDI and synth, while decoded
  float PCM is SHA-256 identical. Seen on Atlas of Becoming 05 during cello-v2
  recovery: the first parallel encode changed container hash on a single-worker
  repeat; two subsequent single-worker encodes were byte-identical. Do not use raw
  Opus equality as the audio oracle. Investigate whether `ropusenc` stream serial
  assignment depends on parallel launch timing, then make it deterministic or
  compare decoded PCM in render-refresh tooling.

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

- [ ] 2026-07-13 — **MSRV could be lowered from 1.87 to ~1.70** by replacing `is_multiple_of`
  (`altbank.rs:215,527`, `voices.rs:2311,2340`) with `% CTRL == 0` and `is_none_or`
  (`altbank.rs:471`) with `map_or(true, ..)`. Both are provably equivalent on unsigned ints,
  but they sit in DSP hot loops, so the synth-change policy applies: needs the render-diff
  inventory to confirm bit-identical output. Low value, non-zero cost — only worth it if a
  low MSRV is a goal for the published crate.

- [ ] 2026-07-13 — **Ship a `PROVENANCE.md` inside each samples `.crate`.** The per-file
  source map (202 outputs → upstream URLs) lives only in `tools/ferrosintesis-samples/prepare.py`,
  which is outside both packages' `include` lists — so a crates.io consumer gets the prose
  summary and the CC0 text, but must follow a GitHub link for the evidence. CC0 requires no
  attribution so this is not a legal gap, but crates.io tarballs are immutable forever while
  repos are not. `prepare.py` already holds every field needed to emit it.

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

- 2026.07.17 — **ChoirV2 CC70 cluster-shade is coupled to the F3 formant gain** (`sf_open =
  vgains[2]/sf_ref_g3`, voices.rs:6103; the F5 adversarial finding). It SATURATES when the program's
  default F3 gain is on the floor, so a dark-voiced preset silently kills the CC70 vowel morph's
  cluster differentiation. Worked around in the darkening slice by keeping aah's default `vgains[2]`
  at 0.15 (off the floor). A clean fix: give `sf_open` its own state driven by an EXPLICIT cluster-open
  control from the CC70 path, independent of the F3 formant gain — a dedicated CC70 slice, not urgent.

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

- [ ] 2026.07.19 — **Three samples-off tests are not `cfg`-gated to `embedded-samples`,
  so `cargo test -p ferrosintesis --no-default-features` reports them as failures**
  (positive sample-engagement controls that hard-code `samples=true`):
  `gm0_grand_and_gm1_upright_are_distinct_instruments` (`crates/ferrosintesis/src/voices.rs:14185`),
  `keyboard_voices_programs_4_7_do_not_use_acoustic_piano_voice` (`voices.rs:13092`),
  `wd_o10_routing_sample_policy_and_lifecycle` (`voices.rs:21290`). Spotted during the
  MM-BUG-KILN verify-close pass. May be *intended* (MM-BUG-KILN-00020 establishes that
  samples-off is a deliberately-not-green config that should fail loudly) — triage
  whether to `#[cfg_attr(not(feature="embedded-samples"), ignore)]` these three so the
  only samples-off failure is 00020's guard, or leave them as extra loud signal.

- [ ] 2026-07-19 ferrosintesis render HANG: `ferrosintesis "<Hollow Hill Pt 1>.mid" --solo 8 -o x.wav` (nylon, prog 24) runs >400s and is killed, on BOTH the pre-Phase-1 baseline binary AND with --peak-normalize (so not LUFS, not my pluck change). The FULL-mix render of the same file finishes in ~2min, and --solo 7/10/14 finish in ~2min — only --solo 8 pathologically slow. Suspect a stuck/never-reaping voice or LA-sample loop specific to that channel. crates/ferrosintesis/src/engine.rs (solo path / voice reap) + sampler.rs. Repro: Hollow Hill Pt 1, --solo 8.

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

- [ ] 2026-07-19 FINGERED BASS (GM 33, `BASS` preset) and UPRIGHT bass (GM 32, `UPRIGHT`) sound "more or less the same" to Arthur (showcase audition), despite the v0.12 §2.12 "widened 32/33 split". Expected: an electric flatwound (muffled, pickup-comb identity) vs a woody ACOUSTIC upright (corpus modes, fingertip thud, no pickup) should be clearly distinct. Investigate whether the split is audibly insufficient (or the showcase phrase just does not reveal it). Separate from the pluck redesign (a distinctiveness issue). crates/ferrosintesis/src/voices.rs BASS (~2773) + UPRIGHT (~2903).

- [ ] 2026-07-20 GM109 bagpipe zone coverage: the FreePats archive holds 26 WAVs (24 chanter takes + 2 drones) but `BAGPIPE_SOURCES` bakes only 8, ignoring A#4/B4/C#5/D#5/E5/F5/F#5 and every `_32` round robin. With `find_loop` now able to cut a clean short loop from any steady take, filling the ~2.5-semitone gaps (and adding an RR2) is cheap and would cut the repitch stretch. `tools/ferrosintesis-samples/prepare.py:572` (BAGPIPE_SOURCES), `crates/ferrosintesis/src/sampler.rs:2099` (chanter zones).

- [ ] 2026-07-20 `LoopVoice` has NO intrinsic animation while `SaxLoopVoice` runs a +/-0.22% read-rate random walk explicitly commented "defeats the loop-tell" (`sampler.rs:SAX_DRIFT_MAX`). Now that the bagpipe loops are ~65 ms they repeat ~15x/s; a slow drift would dissolve any residual static "tell". Add the DRIFT only — NOT the sax tremolo: `bp_o1_bagpipe_chanter_is_constant_amplitude_saxes_keep_dynamics` pins constant amplitude, and constant bag pressure is the instrument. `crates/ferrosintesis/src/sampler.rs:LoopVoice::render`.

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

- [ ] 2026-07-24 Offline renders may not PARALLELISE on a 24-core box: one `ferrosintesis` render measured ~12x realtime, but six concurrent renders gave ~10x realtime AGGREGATE (442 MB of WAV in 4m06s) — i.e. six processes did roughly the work of one. Not a controlled comparison (different tracks each way), so it needs a proper A/B on the SAME file set before anyone believes it. Not disk-write bound: `wav.rs:write_wav` buffers and emits the whole PCM block in one `write_all`. Not memory bound (96 GB, 54 GB free). If it holds, `render-catalog --jobs` is buying nothing and a full catalog render is ~2 h instead of ~10 min. Noticed while running the render-diff inventory for the GM 8/9/10 echo-send change. `crates/render-catalog/src/main.rs` (jobs), `crates/ferrosintesis/src/offline.rs`.
