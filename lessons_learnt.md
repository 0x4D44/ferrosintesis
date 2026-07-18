# Lessons learnt

Distilled, non-obvious gotchas for future sessions in this repo. Cap: 20.
(Currently over cap — due a prune pass.)

- 2026.07.19 — **render-diff baseline MUST be the commit you rebased ONTO, not a fresh `origin/main`
  build: in this multi-agent repo local `origin/main` drifts mid-session via concurrent fetch
  (f58aceb→b308fd1 here, 2 commits, AFTER my rebase), so a baseline built from a newer tip reports the
  trunk delta as false CONTAMINATION.** Rebase onto the current tip FIRST, then
  `git worktree add BASELINE origin/main` so baseline == your branch's base; re-check `git rev-parse
  origin/main` right before building the baseline (`tools/render-diff/render_diff.py`).

- 2026.07.18 — **A composer/generator subagent emitting a big module can die on the per-response 64k
  output-token cap BEFORE any file write — instruct it to write the file in several small Write/Edit
  chunks, never one giant call** (The Remaining T5, ~900-line module; relaunch with the chunk
  instruction went first-pass green; worktree was left clean both times, so just relaunch).

- 2026.07.18 — **Class-identity oracle: range-assert the perceptual Passport's OWN fields
  (`sustain_db` is THE class axis), NOT the existing voices.rs class-oracle numbers — those use a
  different estimator (mag_at partial-ratios vs flatness/slope), so pasting them as Passport ranges
  is wrong by construction** (`testutil.rs` `class_identity_ranges_hold`; dump `print_passport_fields`).
  - `sustain_db` = dB(RMS(W5)) − dB(RMS(0.05–0.30 s)): sustained families (organ/bowed/brass/reed/
    pipe/ensemble) hold ~0; struck/plucked (piano/guitar/bass/mallets) decay to −16..−118. One
    threshold split (~≥−6 held / ~≤−10 decayed) separates them; other planned axes (organ flatness,
    brass/reed harm_frac) FAILED in Passport space — measure first.
  - MEASURE before trusting a design carve-out: GM29/30 driven guitar DECAY on a plain held note,
    GM38/39 synth bass HOLD. (Correction 2026.07.18: the GM29/30 decay is not "opposite of design
    intent" — it is round-3 U2's deliberate choice, `DRIVE.sustain=0.0` voices.rs:2503-2511; the
    guitar-v2 sustain intent was superseded, and the sustaining voice is the alt bank's DRIVE_LEAD.
    Don't "fix" it: `driven_main_and_alt_banks_diverge` + `class_identity_ranges_hold` pin it.)
  - Keep honest limits, don't fudge: reed↔flute overlap on flat_L (F2); synth lead/pad 80-95 too
    heterogeneous to gate (F1, unasserted). §6: the Passport encodes CLASS; realism stays ear-only.

- 2026.07.18 — **A seam-clean sustain loop is NOT a flat loop — bias `find_sax_loop` to a SHORT window in
  the steady body + penalise amplitude imbalance, or a long "clean" loop spans the note's decay and pulses
  loud→silence→loud at ~3 Hz** (`sampler.rs` `find_sax_loop`; oracle `sax_loop_level_parity_and_flat`).
  Integer-period + low value/slope seam only guarantees the WRAP joins; the interior can still ramp. Cost
  must add |rms(first half) − rms(second half)|, and cap loop length (0.05–0.13 s) with le < ~0.50 s (clear
  of the recorded release). Corollary: one output gain can't level-match GM 64-67 — the samples are peak-
  normalised uniformly but the modeled reeds differ ~7 dB, so use a per-program `SAX_LOOP_GAIN[4]` calibrated
  to the model each replaces (parity preserves album balance). Measure loop steadiness by spectral-centroid
  drift across the loop halves, not the raw region's liveness (which includes the note's own envelope).

- 2026.07.18 — **A render-diff baseline can be a SILENTLY STALE binary — verify its mtime/version before
  trusting the diff, or "contamination" is really just the trunk work your baseline predates.** A build
  wrapped in a wrong `mdtimeout` path (`No such file or directory`) never ran cargo; the follow-on
  `ls target/release/ferrosintesis.exe && echo READY` found a *previous session's* binary and printed a
  false "BINARY READY" (exit 0 came from the `ls`, not the build). The stale baseline predated the sax LA
  layer, so render-diff reported 107 non-GM6 albums as CONTAMINATION for a provably GM6-only change. Fix:
  before any render-diff, confirm the baseline binary is a FRESH `origin/main` build (throwaway worktree or
  rebuild the clean main clone) and check its mtime; a clean self-check is `render_diff.py --program X` on a
  scoped change should show 0 contamination. Same trap poisons audio measurements — a "samples vs --no-samples"
  probe on a pre-layer binary shows no difference for the wrong reason.

- 2026.07.18 — **Adding an LA sample bank: MEASURE each zone's root before hardcoding — many sources are
  2f-dominant or octave-mislabelled, and a wrong root plays the zone an octave off** (`prepare.py`
  `TWO_F_STRONG` / `_bake_sf_onset`; per-family bank fns in `sampler.rs`).
  - 2f trap: autocorr grabs the 2nd harmonic whenever the F0 ceiling admits it (ocarina, recorder,
    banjo all did). Fix: keep a zone span UNDER one octave so a single ceiling separates f from 2f
    (ocarina), OR add the family to `TWO_F_STRONG` for a per-note ceiling of label×1.5 (recorder, banjo).
    Probe first: `measure_f0(x, sr, 150, label*1.5)` vs a generous ceiling.
  - Octave-label traps: VCSL keyboard/ocarina file labels sit an octave BELOW sounding pitch; ganjo
    banjo labels sit an octave ABOVE. Name the dest by the MEASURED pitch, never the source label.
  - A NEW sample crate's WAVs are gitignored until you add `!crates/<crate>/samples/*.wav` to
    `.gitignore` — else `git add <crate>` commits the crate WITHOUT its samples and it fails to build
    from a clean checkout. Confirm with `git ls-files <crate>/samples` after committing.
  - ganjo WAVs are IEEE-float (fmt tag 3); stdlib `wave` errors "unknown format: 3" — transcode to
    16-bit PCM with ffmpeg at fetch (`ensure_banjo_sources`), like the SF3 Ogg / drumkit FLAC decodes.
- 2026.07.17 — **ferrosintesis has NO per-instrument loudness normalization — only whole-mix −18 LUFS;
  per-program balance is now nudged toward the SC-55 by `engine::PROGRAM_TRIM_DB[128]` (applied at the
  melodic strip `g*=trim`, ch9 exempt).** Two metric traps when auditing levels: (1) whole-note RMS
  unfairly penalizes DECAYING voices (ferro guitars read −15 dB "quiet" vs SC-55 but it's faster decay,
  not level — use early-window RMS for plucked/percussive, whole-note only for sustained); (2) instantaneous
  PEAK is too spiky. Trim is level-only/timbre-neutral (`g` feeds dry+sends together); the master bus-glue
  compressor is nonlinear so a solo-probe corrected voice lands ±0.5 dB off its nominal trim (benign). Probe
  MIDI period = tick math not intended seconds (960+240 tick = 1.25 s, NOT 1.5). Reproducer + SC-55 compare:
  `target/level_audit/` (mdmidiemu ROMs at `D:/language/mdsc55/roms/sc55`). See `wrk_docs/2026.07.17 - CR - instrument level audit + SC-55 trim.md`.

- 2026.07.17 — **Extracting a LOOPED sample from an SF3 soundfont: ffmpeg's Ogg-Vorbis decode drops
  ~80–100 trailing frames (Vorbis priming/padding), so the soundfont's `endloop` lands PAST the decoded
  end — clamping it to the decoded length shortens short low-note loops below one period and DETUNES the
  note (clavinet G1 read +200 cents).** Don't trust the soundfont loop points: loop PITCH-SYNCHRONOUSLY
  — carve an exact integer number of periods (`T = sr/originalPitch`; `originalPitch` is accurate to a
  few cents) from the steady body, length-preserving crossfade at the wrap (`prepare.py`
  `_bake_clavinet_note`). Also: SF3 `shdr` start/end are BYTE offsets into `smpl` (each a self-contained
  Ogg), NOT PCM frames as in SF2; and the sample NAME octave is +1 vs `originalPitch` (name "C4" = MIDI 48
  = C3). Two RIFF-walker gotchas: a chunk header's size field is a SIZE not an end offset (`end=off+size`);
  a `LIST` body starts after its 4-byte type (`data=off+12, size-4`).

- 2026.07.17 — **A fast-decaying plucked-KEYBOARD LA layer needs a LOWER wrap gain than the guitars
  (harpsichord `LA_HARPSICHORD`=0.28 vs `LA_GUITAR`=0.42): a real harpsichord's high strings damp fast
  in the MODEL but the recording's body still rings, so at 0.42 the sampled 50–150 ms window sits 2.9×
  above the model's own decay shape and trips `la_level_continuity` at C5 (key 72).** The quill spike
  (0–50 ms) is before that seam window, so lowering gain keeps the attack character. Also: VCSL keyboard
  file labels sit ONE OCTAVE BELOW sounding pitch (label C3 → 262 Hz = C4), same as the VSCO string
  sections — the bake renames each zone to its sounding pitch and the MEASURED root lands in `sampler.rs`
  (`voices.rs` `LA_HARPSICHORD`, `prepare.py` `HARPSICHORD_URLS`, probe `tools/…` measured 0.91–1.00 conf).

- 2026.07.17 — **Re-voicing a common GM voice breaks oracles that use it as a live CONTROL — grep
  `stats(<prog>)`/`make(<prog>,…,true)` before changing its timbre.** Swapping GM0 upright→Salamander
  grand broke `harpsichord_jangles_with_a_four_foot_choir` (`voices.rs`), which measured the harpsi
  centroid against a GM0 render; the grand is brighter+2f0-rich so both clauses inverted. Fix: move the
  control to GM1 (same upright the oracle was calibrated on) + rebar 1.75×→1.6× — recalibrate against the
  intended reference IN the commit, don't weaken. Two more from this build: (1) a CC-BY sample bank goes
  in its OWN crate (`-samples-grand`, mirroring `-gong`) — core was 9.55/10 MiB, at the crates.io cap;
  (2) when a source has no round robins, `RR2` = an adjacent VELOCITY layer + `trim_to_onset`'s peak-norm
  → same level, brighter-strike timbre = free RR variety, no machine-gun on repeats.

- 2026.07.17 — **Inspect a candidate sample's ACTUAL AUDIO (spectral flatness + dominant-partial
  concentration) before trusting its name/licence for a timbre role.** A licence-only search called
  VCSL "Gong 1" a near-pitchless tam-tam; it is a PITCHED gong (sharp 143 Hz/D3, 95%-concentrated) —
  wrong for a CC0=1 tam-tam. And measure the root over the RING, not the strike: the CdM Gong Ageng's
  strike thumps ~80 Hz but its sustained partial is ~99 Hz (G2) → `GONG_ROOT_HZ=99.4` (`sampler.rs`);
  an 80 Hz root rendered every key a major-third sharp. Three sourcing dead-ends this build were all
  invisible to name/licence and only the spectrum (or a render) revealed them.

- 2026.07.17 — **Album-scale generative fan-outs don't fit the fleet-shared 5-h usage window — serialize composers and feed a digest, never parallelize.** Two parallel fleets died mid-window (10-wide, then 2-wide: ~0.9M tokens, zero tracks); one-at-a-time composers fed a compact pattern digest (Slipstream `COMPOSER-NOTES.md` instead of re-reading the 1.7k-line exemplar) landed 10/10 at ~150-250k tokens/track with per-track verify+commit making every landing durable.

- 2026.07.17 — **"h3 re h1" (a single-harmonic notch) is an UNSTABLE timbre proxy — it swings ±40 dB
  with which harmonic lands on a formant; measure BRIGHTNESS as centroid across the REGISTER, not one
  key.** The choir "hollow-notch" fork chased SC-55's aah h3 "−14 at k60" — but SC-55's own h3 swings
  +26 (k52) → −12 (k60) → +14 (k64); the whole notch target (and a prototype "validated" at k60) was a
  register-snapshot artifact. The real, stable defect was centroid over-brightness (aah 1.6× / GM54 3×
  & inverted), fixed by preset darkening (`CH2_HUM_LP` open 8000→3400, cluster/F2 trims), not a Klatt
  cascade. Corollary: a rompler's per-vowel formant character is register-dependent — "GM54 is darkest"
  held ONLY at k60 (GM53 is darkest below ~k58), so never freeze a single vowel ordering from one key.
  Always measure a candidate voice at 5-6 keys spanning the register (`tools/choir_measure.py`).

- 2026.07.16 — **A differential oracle is only as good as its INPUT POPULATION — take the
  parameters from measurement, never from the assumption you are trying to verify.** Fixing
  `prepare.py`'s de-click fade, I "proved inertness" with a test fed 8-300 ms of lead-in and
  shipped green — but the real bank is trimmed FAR tighter (median onset: piano 120 samples,
  violin 3, steel 8), so the change silently re-cut 131 committed WAVs and would have delayed
  every layered attack by up to 7 ms. `git status` caught it; the passing test did not. The
  sample bank IS the oracle here: regenerating and diffing the committed WAVs is a real-world
  check no unit test replaces — run it before believing any prepare.py change is inert.
  Corollary that fell out: `prepare.py`'s fixed 2 ms fade-in has been wrong since the LA layer
  was born (`ce99cda`, 2026-07-02, `git log -L` shows ONE commit ever) — it was sized for
  day-one violin and every family added since inherited it, so 74 of 210 sources had their
  onset INSIDE the fade window and their attack crushed. A constant does not have to drift to
  become wrong; the material underneath it can move instead. When adding a family to a shared
  generator, re-measure the constants against the NEW material.

- 2026.07.16 — **A per-voice modulator is phase-COHERENT across a multi-player voice —
  it pumps the whole "section," unlike the decorrelated per-player detune/vibrato/scatter.**
  Brass `l` (the loudness/timbre scalar, `voices.rs` `control_tick`) is per-VOICE, shared by
  all players; folding a living-breath into it would tremolo the 5-player section 61 as one
  coherent unit (the "wobbly synthetic" tell). Gate liveness modulators to SOLO voices
  (`oversample && spec.players == 1` → naturals 56-60); leave sections alone (already alive
  from per-player detune+vibrato+onset-scatter). Two more reusable moves from this fix:
  (1) model breath as APERIODIC value-noise (smoothstep between random targets), not a sine —
  a periodic LFO reads as a tremolo/slow-swell; (2) isolate a new DEFAULT-ON modulation axis
  from the ~16 existing static-timbre oracles by rendering them FROZEN (force the depth field
  to 0 in the shared `render_brass` test helper) — the new axis gets its own DIFFERENTIAL
  oracle (`brass_sustain_breathes_off_the_frozen_hold`, a sliding-centroid p5–p95 wander:
  measure the actual complaint = TIMBRE motion, not the incidental level AM a tremolo also shows).

- 2026.07.16 — **ferrosintesis LA sampling is ONSET-ONLY — a missing sample cannot fix a
  SUSTAIN or noise complaint; route every voice fix by cue.** Proven: brass HOLDS render
  bit-identical with `--no-samples` (the LA layer has crossfaded out by ~0.3 s). So an
  IDENTITY/attack complaint (40==41 viola sameness, recorder identity, timpani strike) wants
  a new CC0 onset bank; a SUSTAIN/noise complaint (brass "holds synthetic", sax "fuzz", flue
  "sshsshssh", choir) wants MODEL work, NOT a sample — and is usually a handful of constants.
  Do not confuse the two (round-3 feedback: most complaints were the model side, i.e. cheap).
  Method that nailed all 15 root causes: A/B every voice against a REAL GM module —
  `mdmidiemu --synth sc55|mu80` (ROMs at `D:/language/mdsc55/roms`) renders the actual Roland
  SC-55mkII / Yamaha MU-80; SC-55 is the reliable spectral reference (~40 ms onset, no swell),
  MU-80 is often reverb/swell-dominated (use for character only). Watch for oracles that ENCODE
  the defect — three found blocking the correct fix (`harp_46_shimmers` rewards the octave-hollow
  balance; choir `CH2-O2` pins GM54 bright; recorder `WD-O1` asserts `h2≥h3` backwards) —
  recalibrate them against hardware IN the fix commit. Full analysis:
  `wrk_docs/2026.07.16 - PLN - voice-quality round 3 (15 voices) roadmap.md`.

- 2026.07.15 — **A plucked-voice "no sustain" complaint is usually the note-off
  RELEASE (`rel_t60`), not the natural KS decay.** Album guitar parts are written
  as SHORT notes (~0.2–0.55 beat, gate < 1), so MIDI note-off lands in ~0.2 s and
  the amp release governs the sound. The acoustics inherited `DEFAULTS.rel_t60 =
  0.15 s` — a fast chop that kills the ring 0.3 s after note-off. An un-muted string
  is not damped at note-off; give the non-muted guitars a "let-ring" `rel_t60` (~1.1
  s) and keep MUTED's fast chop. Bounded pile-up: no polyphony cap for acoustics, a
  voice reaps only when it decays < 2e-5, so a long release ≈ note-rate × ring
  voices (fine offline). Isolated `render_pluck_phased` shows the full chop (−213 dB
  tail); the real engine masks most of it via the guitar echo send (0.08) + CC91
  reverb, so the in-mix win is a modest +4–9 dB — measure in the ENGINE, not just the
  voice. Corollary: the `mean_freq` zero-crossing pitch estimator is timbre-brittle
  (any `bright` bump tips it — it mis-counts on the 2nd harmonic leaking past its
  700 Hz lowpass); for precise pitch use the Goertzel `peak_locate` + parabolic
  refinement, never zero-crossings (`rpn_bend_range_and_fine_tune`).

- 2026.07.14 — **"Drums too far back / not prominent" is usually INTERNAL KIT
  BALANCE (hi-hats too quiet, ride/crash too loud vs kick/snare), not a bus level
  or reverb problem — and a flat drum-bus gain cannot fix it.** The master
  normalizes to a fixed −18 LUFS and true-peak-limits to −1 dBTP, so a flat drum
  lift is absorbed: a +6.8 dB probe moved the delivered master ~0.4 dB (the drums
  become the peak-driving element and the limiter clamps exactly the kick/snare
  transients you hear). Diagnose per-FAMILY balance in a REAL track before reaching
  for bus tools: an env-gated per-key mute (keep only 42/44/46, or only 35/36/38/40)
  + integrated-LUFS on the ch10 solo stem shows which family dominates. On a standard
  backbeat the hats measured 26 dB under the kick/snare (gone); on Hey Jude the crash
  sat 2 dB under (too loud). Root: the sampled `DRUM_LEVEL` table is calibrated to
  MATCH the modeled kit, so it faithfully inherited the model's hat-light/cymbal-heavy
  voicing. Fix the balance as a per-key trim in the drum MIX (engine `kit_balance`),
  not in `DRUM_LEVEL` — it then scales both the sampled and modeled kits equally and
  keeps their parity. Beware the golden mix-balance fixture (re-pin ch10 only) and the
  stereo-imaging oracle (a hat-forward kit correlates more; give its test pattern a
  present ride so it still exercises the L/R spread).

- 2026.07.15 — **The KS Pluck BASS already emits a strong pitch-tracking f0/2 SUBHARMONIC —
  so "add a sub-octave" is a solved problem, and a second oscillator is redundant + octave-
  flip-risky.** Measured dry/isolated/sustained: A2 f0/2 sits **+5.7 dB OVER** the fundamental,
  E2 +0.3, F#3 +11.7, and the peak TRACKS f0/2 (E2→42 Hz, A2→54 Hz), not the fixed ~50 Hz
  body peak. It's a LONE f0/2 line (no 1.5·f0), so it reads as sub-reinforcement / "bigness"
  (why a low-voiced bass already sounds big), NOT a wrong-octave pitch. Before building a
  low-end feature, MEASURE what the voice already emits at f0/2 — a Fable-designed sub-octave
  oscillator was fully built then shelved once this showed its premise ("~nothing at f0/2")
  was false. Two corollaries: (1) **Ground bass timbre in a REAL module** — `mdsc55` emulates
  the real Yamaha MU-80 (XG) / SC-55 with ROMs on disk; render the actual passage through
  `mdmidiemu --synth mu80` and measure the onset spectrum (the XG finger bass is LOW-dominated,
  centroid ~100-135 Hz; a mid-forward model reads "twangy"). Its per-key f0/2 level jumps
  non-monotonically = multisample-zone artifact, NOT a design law to copy. (2) When a voice's
  masking layer grows (BASS sub 0.28→0.72), a differential oracle for a small parallel feature
  (the stop thump) drops BELOW the rng-realization noise floor and reads with<without — test
  the MECHANISM on a sub/kick-free clone, don't weaken the assertion.

- 2026.07.14 — **A one-pole KS damper's MAGNITUDE at f0 (not `loop_gain`/`t60`) rules
  treble decay** — STEEL B5: damp_mag(f0) ≈ 0.955/round-trip ≈ −390 dB/s, so the
  fundamental is dead in ~130 ms whatever the nominal t60. Naive `1/|H(f0)|` loop-gain
  compensation is DC-UNSTABLE (round-trip gain > 1 below f0, since |H(DC)|=1); hold a
  treble carrier with the band-limited saturating `SusDrv` sustainer instead. This is why
  a fast plucked tremolo machine-guns: not (only) the fresh-spawn re-attack, but the
  inter-stroke release chop + the dead treble carrier. Fix = re-PICK the ringing string
  (voice reuse + stretched release + carrier hold + pick-catch + h1-floor); see the tremolo
  HLD. Oracle: f0-carrier p10/p90 (tone persists between strokes) — broadband/HFfrac metrics
  are FOOLED (the onset train dominates all bands, so total-energy ratios are invariant; and
  overlapping released twins fill gaps with hash that gross-envelope metrics credit as
  continuity). Corollary: one comb-noise period's h1 is Rayleigh-random (20 dB stroke
  roulette) and additive re-injection phase-cancels — a re-pick must catch (scale) the line
  and floor its own h1.
- 2026.07.14 — **A "bug" can be test-pinned as a feature — check before removing it.** The
  GM20 reed-organ half-integer partials (1.5/2.5/3.5/4.5f) read as a parallel-fifth "organum
  ghost" AND are pinned by `reed_organ_..._free_reed_character` as intentional off-harmonic
  character (off_harmonic_residual ≥ 1.5× church organ). Removing them killed the fifth but
  broke the test. When a scoped-oracle change passes but the FULL suite fails, the failing
  test is telling you the "bug" was a design choice — don't override it on an unverifiable ear
  judgment; escalate to the human, or fix at the right layer (character via reed-noise, not
  clean pitched quints).

- 2026.07.14 — **Virtuosity's 18" jazz kick has NO 30-70 Hz sub in ANY mic set
  (fundamental ~80 Hz; the overhead's "sub" reading is room rumble).** Re-micing
  cannot create low end the instrument never produced — a deep-kick ask needs a
  modeled-sub layer or a ~100 Hz-hinged shelf on the fundamental. Related: white
  rate jitter alone can never bound worst-pair correlation on fast repeated
  hits — some same-take pair always draws near-equal rates; stratify the rate
  offsets by hit index, coprime with the round-robin count (hats: 5 vs 4).
- 2026.07.14 — **Deep-velocity-layered sample libraries with no round robins
  (Virtuosity snare 36 vl, toms 16 vl) still yield working round robins: fill
  each target layer's RR slots with ADJACENT source velocity layers.** They are
  distinct recorded takes within ~10 velocity points, timbrally near-identical
  once the prep pipeline peak-normalizes (the synth applies velocity gain
  itself) — so they cycle exactly like true RRs (fast-hat NCC ≤0.49 vs 1.0
  clone). Corollary for choke oracles: "choked window quieter than the open
  ring" FAILS when the choking articulation's own body outlasts the window (the
  pedal chick rings past 200 ms) — measure the RESIDUAL instead: choked-render
  energy minus choker-played-alone energy (`sampled_closed_or_pedal_hat_
  chokes_open_in_engine`).

- 2026.07.14 — **Plain NCC cannot detect a repeated sample take once per-hit rate
  jitter exists** — ±2.5% playback-rate jitter alone decorrelates a 30 ms cymbal
  window to NCC 0.07–0.19 *for the same take*, so an anti-machine-gun oracle built
  on plain correlation waves a round-robin repeat through. Use a rate-WARP-searching
  NCC: warp one hit over ratio candidates (±ratio spread of two jitter draws),
  anchor at the detected onset, and correlate FIRST DIFFERENCES (tilts toward the
  take-specific HF sizzle, away from the low plate modes every take of one cymbal
  shares) over a window starting past the shared stick transient (30–70 ms).
  Measured on the drumkit ride: distinct takes 0.12–0.48, same take 0.70–0.86,
  clone 1.0 — a usable threshold at 0.60. Raw-waveform/onset-window variants had
  no margin (adjacent takes correlate 0.71). See `sampled_ride_hits_are_decorrelated`.

- 2026.07.13 — **To detect a bad cymbal/plate on a box with no ears, measure decay RATES
  and STRUCTURE, never spectral SNAPSHOTS.** Every cheap scalar (flatness, centroid,
  kurtosis, peak prominence, band ratios) is a time-marginal of the spectrum, and a
  noise-wash's filter corner is free to sit anywhere — so it DOMINATES every snapshot and
  the feature is blind to the actual defect. Proven: 11 of 16 proposed cymbal-oracle clauses
  were measured worthless (already green on the broken voice, or unsatisfiable, or rejecting
  the real recording as a reference). The two real crash round-robins we own agree to the
  decimal on decay features (spectral-tilt −11.0 dB/s both) while disagreeing ~30% on
  snapshots — because decay rates are a property of the PLATE, snapshots of the STRIKE. Use
  a DIFFERENTIAL oracle against the recording, but only in the decay domain (t60(f) shape is
  material physics, so it transfers across cymbals; mode frequencies don't). Also: today's
  `MetalPlate` is a time-invariant highpassed noise wash decayed by ONE scalar with the
  44-mode plate 17 dB under it — t60 flat ~3.0 s from 200 Hz–14 kHz where a real cymbal
  darkens (1.0 s at 10–14 kHz). Full design + oracle in `wrk_docs/2026.07.13 - HLD - cymbal
  plate synthesis and its oracle.md`.

- 2026.07.13 — **Two silent traps that let bad drum voices pass a green suite.** (1) The test
  helper `render_drum` (drums.rs:2313) hardcodes `Kit::V1`, but the engine ships **V3**
  (engine.rs forces it) — so every "V3 cymbal" oracle (`china_splash_crash_are_distinct`,
  `crash_blooms_hat_does_not`, …) is measuring the DEAD legacy voice the engine never
  selects. Any new drum oracle in the house idiom inherits the trap: render via
  `render_drum_kit(…, Kit::V3)`. (2) A golden can PIN a bug: `v3_toms_settle_near_table_pitch`
  asserted key 48 → 240 Hz, which encoded the collapsed `47 | 48 | 50 => tom(240.0)` arm
  (the top three GM toms were bit-identical but for pan). Fix a golden's EXPECTED value, never
  its tolerance. Corollary invariant now enforced in `Modal::new`: `attack_s < strike-noise
  t60`, else the attack ramp gates the very transient it exists to pass (GM 114's alt steel
  pan shipped 10 ms attack vs 8 ms mallet burst → strike at 12% of peak → a steel pan that
  measured as a wooden bar, metalness 0.0002 vs marimba 0.0001).

- 2026.07.14 — **White noise through a memoryless nonlinearity stays spectrally
  FLAT — it cannot make skirts.** S_y(f) = Σ|W_k|²·S_n(f−k·f0): shifting and summing
  a flat PSD is still flat, whatever the drive. To get growl skirts around partials
  (the sax G3 gate), the injected turbulence must be band-limited well below f0
  *before* the shaper (RD10 lowpasses it at 0.30·f0); full-band injection just adds
  hiss and the skirt bands never concentrate. Corollary for oracles: a single
  one-pole "sub-audio" probe leaks a 349 Hz carrier at −6 dB/oct (~3 %) — cascade
  poles before calling a residue DC.

- 2026.07.14 — **The 20-log-bin `testutil::centroid` is leakage-dominated on a clean
  harmonic lattice — a real 3× filter-cutoff sweep reads as ~1.1×.** Its fixed Goertzel
  bins almost never land on a harmonic, so every bin reads sinc-leakage skirts and the
  "centroid" mostly tracks the strongest harmonic's nearest bins (RD-O7's old note
  measured the same compression). For brightness oracles use the Hann-windowed exact-DFT
  `testutil::spectral_centroid` on a settled window (O-PRESSURE's `steady_centroid`
  pattern) — same family as the zero-crossing-pitch lesson: check the estimator can see
  the effect before pinning thresholds on it.

- 2026.07.13 — **An MSRV is only real once a toolchain at that version has compiled it —
  and `rust-version` is what turns the checking lint ON.** Grepping for the newest std API
  gives a LOWER bound, not the answer: an audit concluded "≥1.70" from `OnceLock`/
  `is_some_and` and missed `is_multiple_of` (stable **1.87**) and `is_none_or` (1.82) buried
  in `altbank.rs`/`voices.rs`. Clippy's `incompatible_msrv` lint finds these instantly but
  only fires once `rust-version` is *set* — so declare a floor first, let clippy correct it,
  then prove it with a real `cargo +<msrv> check --workspace`. That last step is not
  ceremony: it caught that `crates/ferrosintesis/Cargo.toml` declared a dependency as a
  **multi-line inline table**, which is invalid TOML 1.0 — cargo ≥1.9x parses it happily,
  cargo 1.87 refuses the manifest outright. We would have published a crate nobody on our
  own declared MSRV could build. Keep every dependency on ONE line.
- 2026.07.13 — **`#[non_exhaustive]` seals LESS than you think, and `pub` fields quietly
  cancel it.** Three traps, all hit in one pre-publish API pass. (1) On an *enum* it only
  reserves the right to add **variants** — the **fields inside** a variant stay exhaustively
  matchable, so `Io { path, source }` still freezes its field list. Every data-carrying
  variant needs its OWN `#[non_exhaustive]`, and tuple variants should become struct variants
  first. (2) On a *struct* it blocks **construction**, not **field assignment** — so
  `#[non_exhaustive]` + `pub` fields is the worst of both worlds: the builder becomes optional
  sugar while every field NAME and TYPE is still frozen. Seal INPUT structs (private fields +
  `with_*` builders + accessors) and leave OUTPUT structs (`Stats`, `Progress`) `pub` — they
  can't be constructed downstream anyway, so adding a field is already safe. (3) The fallback
  (`let mut o = Options::default(); o.f = x;`) trips clippy's `field_reassign_with_default`
  under `-D warnings`, and `..Default::default()` is illegal on a foreign non_exhaustive
  struct — so a builder is the ONLY clean construction path, not a nicety. Also: settle the
  API *before* commissioning the prose about it, or you re-brief the agent writing your README.
- 2026.07.13 — **Never quote a performance number you have not just measured, and re-check a
  doc table against the code before it becomes permanent.** The README claimed ~40x realtime
  for years; the measurement is **5.25x** (245.8 s of audio in 46.8 s) — the old figure
  predates the orchestral voices and the sample layer. An adversarial review of the same
  README also found four *wrong rows* in a GM table headed "GM coverage, honestly" (GM 38/39
  are SynthBass not Karplus-Strong; 42/43 are a stick-slip waveguide with their own sample
  banks, not polyBLEP bows; only 72–73 of the 72–79 winds get the flute sample bank; GM 108
  was missing entirely) plus a DESIGN.md that still described the output as peak-normalised
  three versions after it became loudness-normalised. Docs rot silently and a doc claim on
  crates.io is permanent. Run the render; grep the routing; then write the sentence.
- 2026.07.13 — **A byte-exact test fixture MUST be marked `-text` in `.gitattributes`,
  and the render pipeline IS byte-reproducible across binaries.** Two findings from the
  Rust `render-catalog` port. (1) This repo has `core.autocrlf=true`, so git rewrites LF
  to CRLF on checkout for anything it thinks is text — which silently desyncs every
  length prefix in a length-prefixed golden. `crates/render-catalog/tests/golden/
  .gitattributes` (`*.argv -text`) pins it; verify with `git cat-file -p :<file> | cmp -
  <file>`. (2) The feared cross-binary LTO float divergence did **not** happen: the
  in-process render inside `render-catalog` produced `.opus` **byte-identical** to the
  `ferrosintesis` CLI binary's, all 6 demo tracks, before and after a refactor. So the
  earlier "LTO reorders float ops" lesson applies to *debug-vs-release*, not to two
  release binaries linking the same rlib — a cross-binary byte-compare IS a usable
  parity oracle here (`ropusenc`'s Ogg serial is the fixed constant `0xC0DEC0DE`, so it
  is deterministic too). Corollary: when porting, capture the golden from the OLD
  implementation *before* deleting it — it caught that `render_opus.py` tagged
  `TRACKTOTAL` with the count of *selected* tracks (1 under `--only-list`), not the
  album's true size.

- 2026.07.13 — **A true-peak ceiling on the WAV does NOT survive lossy Opus
  encoding.** ropusenc's 96k VBR + 44.1→48 kHz resample adds content-dependent
  inter-sample true peak — ~1.6 dB typically, but up to ~2.9 dB on the
  brightest/densest material (Bright Matter "Six-Five-Two-One": WAV −3.6 → opus
  −0.7). So `render_opus.py` limits the WAV to −4.5 dBTP (`OPUS_TP_CEILING`) to land
  the encoded `.opus` safely under −1. Probe the BRIGHTEST/DENSEST track (not one
  sample) before picking the ceiling — a milder track under-predicts the overshoot
  and costs whole-catalog re-render cycles. Corollary: loudness normalization under
  a peak ceiling leaves high-crest tracks below target because limiting removes
  loudness; `normalize_loudness` iterates (re-measure → re-makeup → re-limit) to
  recover it, converging from below so it never overshoots the ceiling.

- 2026.07.13 — **To audition ferrosintesis voices one-at-a-time, four facts are
  load-bearing.** (1) **CC120 (All Sound Off) is the ONLY MIDI lever that stops a
  ringing voice** — CC121 only note-offs *held* notes (`engine.rs:1468`), CC123 is a
  release; plucks decay up to 14 s, so without CC120 the tail bleeds into the next
  slot. (2) CC120 does NOT flush the reverb/chorus/echo tanks — the gap is silent only
  because the sends are zeroed; and **CC91=0 alone is not dry**: a program change
  re-derives a NON-ZERO CC93/CC94 from `fx_profile` for ~76/128 programs, so author
  CC91/93/94=0 *after* every PC. (3) **Audio oracles must be RATIOS**, never absolute
  floors — the CLI peak-normalises the whole render (`normalize_to_i16`,
  `scale=target/peak`), so one louder voice rescales every other slot. (4) A "raw
  voice" reset must OMIT CC71/CC74 (they instantiate the wah filter, `engine.rs:1286`);
  an effects track that DOES use the filter must reset with CC121 between demos to
  destroy it, or the resonance section colours everything after it. Measured, not
  assumed: CC120 + zeroed sends hits the −96 dB dither floor within 50 ms
  (sympathetic comb and 7 s koto included). See `demos/ferrosintesis_reference/`.
- 2026.07.12 — **`Rng::white()` is UNIFORM in [-1,1), so its RMS is 1/√3 ≈ 0.577,
  not 1.0.** Any audio oracle that predicts an *absolute* noise level from a
  closed form must carry this factor. The Wind/pipe breath-fraction oracles
  (WD-O5) were all designed against a unit-RMS-white assumption and every band
  came out ≈ 1/0.61× too high until re-pinned; the model was correct throughout.
  Corollary: `Biquad::bandpass(fc,Q)` on white outputs RMS ≈ √(π·fc/(Q·sr)) — a
  narrow, cheap way to size a tracked breath bed. And reading a harmonic ratio
  inside a vibrato'd window under-reads upper partials (harmonic n carries n× the
  FM modulation index, so its energy leaks into sidebands a fixed Goertzel bin
  misses) — read harmonics in a strictly PRE-vibrato window; and never `peak_locate`
  an FM carrier when β≳0.5 (the first sideband can outrank it) — use the known pitch.
  Two more unit traps (2026.07.14, SFX oracles): `spectral_band_rms` is Hann-
  windowed, so ratioing it against raw `rms()` bakes in the window's power factor
  and deflates any "band fraction" — compare spectral-vs-spectral only; and
  `testutil::centroid` is magnitude-weighted, so an amplitude taper inside the
  measurement window drags the centroid toward the loud end (a sin-windowed chirp
  read ×1.17 where the sweep was ×1.4 — flatten the envelope or move the window).
- 2026.07.11 — **`deltic timeout <cmd> bash script.sh` hands the script to a
  bash whose exported-function children can't exec `D:/...` paths** — every
  `render_all.sh` child failed "No such file or directory" on an exe that
  existed, and the failure was first misattributed to a concurrent cargo
  relink. Run repo shell scripts via the harness Git Bash directly (its own
  timeout applies); keep `deltic timeout` for non-script commands (cargo,
  python) where it works fine.
- 2026.07.08 — **A synth "spread" oracle across instruments must fix pitch, or
  it measures pitch not timbre.** Four v0.9 verification oracles measured the
  wrong thing while the voice mechanism was fine: brass `centroid/f0` ordered
  tuba<trumpet but at E1-vs-C5 the 100 Hz `centroid` floor drops the tuba's
  fundamental and inverts it; reed anti-alias tested the bari (best case) not
  the soprano (worst); choir shimmer's ±3–7 Hz FM grid overlapped the static
  detune cluster; the crash-twin oracle measured a window where the twins were
  already −70 dB. Render at matched pitch / worst case / the feature's live
  window, and keep the measurement band clear of confounding static structure.
- 2026.07.08 — **Shared voice structs are where parallel designs collide.**
  ferrosintesis strings (48–51) and choir (52–54) are both `SawStack`; designed
  in parallel, one added a stack-level `vib_depth` the other deleted (moving it
  per-`Layer`). Per-family review passed both; only a cross-section critic
  caught it. When fanning out voice designs, add an explicit assembly/critic
  pass over shared structs (`SawStack`, `Layer`, `fx_profile`, the golden
  fixture) before trusting the union.
- 2026.07.07 — **Put untouched-family canaries in the golden fixture.** The
  ferrosintesis realism build's per-channel golden table included piano/strings
  channels no phase touched; they stayed bit-exact for six phases and caught
  the one real leak (a rebuilt Drive emitting tanh(bias) DC on SILENT
  channels) that every feature oracle missed. Level guards find drift;
  canaries find contamination. **Corollary (2026.07.12): a bit-exact hash of an
  f32 render is NOT a valid *frozen* golden across build profiles.** Release
  (opt-level 3 + LTO) reorders the SawStack's summed-oscillator float ops, so
  `sawstack_v1_canary_frozen` flipped debug↔release (`0x63cb52bc25cbdd4f` vs
  `0x66cf721ab5a542fb` — the same pad, two profiles) and was "re-pinned" for
  months, each pin just reddening the other profile. Freeze *aggregate* features
  (rms / centroid / band energy) with a relative tolerance: they average out
  per-sample reorder noise (~1e-7 across profiles) yet still catch contamination
  (voices differ 30–130%). In-build *relative* bit-compares (two renders in ONE
  build — determinism / two-path equivalence) stay valid; only cross-commit
  frozen hashes are the trap. `drums.rs`'s frozen-hash goldens are the same class
  (green today, latent).
- 2026.07.07 — **Zero-crossing pitch counters lie when a change legitimately
  brightens a voice.** Three separate "pitch broke" scares in the realism
  build were the 2nd harmonic leaking through the counter's lowpass
  (452.5 Hz for a true 440). Measure pitch with a Goertzel peak
  (`testutil::peak_locate`); keep crossings only for pure-sine calibration.
  Corollary (2026.07.11, Big Weather): for controller-audibility probes on
  vibrato'd/moving notes, a fixed-frequency Goertzel bin (~1.5 Hz) misses
  harmonics wandering ±60 Hz — use band-integrated FFT fractions (t05's
  wah/Leslie probes) instead.
- 2026.07.07 — **Noise-fed resonator pairs only beat if they can remember a
  beat.** CYM-1's 6000/6055 Hz pair at the HLD's Q 120-150 has a ~7 ms ring
  time against an 18 ms beat period — decorrelated before one cycle, no beat
  survives. Ring time Q/(πf) must span the beat period (Q ≈ 800 here);
  Δf > f/Q alone is not sufficient.

- 2026.07.06 — **A movement-verified render does not verify the album.**
  Engines with one seeded RNG stream (Hollow Hill / Signal Fire / Through
  Lines engine.py) re-roll every downstream jitter when any upstream movement
  changes an event count — per-movement click scans and velocity means shift on
  the final assembly. Always re-measure the assembled build. Corollary
  (2026.07.11, T16 Three-Sixty-One): a note authored AT a section boundary with
  jt>0 can then jitter ACROSS it into a stricter oracle's counted window — an
  outro harp arp's first note (beat 640, `en.arp` jt=4) bled into the finale's
  [544,640) dive count (385 vs 384) after new notes shifted the stream, even
  while `check_movement_bounds`' 0.05 seam tolerated it. Make boundary-straddling
  emitters jt=0.
- 2026.07.06 — **Same-pitch overlapping notes are a silent GM portability
  bug.** ferrosintesis matches note-offs oldest-first so overlaps render
  fine locally, but kill-newest GM synths chop the re-strike. The Signal
  Fire engine's `Score._resolve_overlaps()` (write-time clamp) is the fix;
  Hollow Hill's engine still has the issue if its files are regenerated.
- 2026.07.06 — **Presence in the MIDI is not audibility in the render.**
  The CC1 Leslie ramp was tick-perfect in the file yet measured flat in
  audio (the organ's idle tremulant was already near LESLIE_FAST). Verify
  headline effects on rendered stems (ferrosintesis `--solo`), not just in
  the event data.
- 2026.07.07 — **On Opus, heavy compose/surgery subagents must return
  PLAIN TEXT, not a StructuredOutput schema.** Six Winter Guests composers
  each did full work then all failed the schema-emission retry cap; the
  files were fine. Light verify agents tolerate the schema. Reserve
  workflow `schema:` for short-output lenses; give big generative agents a
  free-text final report.
- 2026.07.07 — **ferrosintesis mono-collapse comes from the pan Haas
  micro-delay, not the chorus.** A choir-heavy, sparse, wet movement lost
  5.6 dB summed to mono because every off-centre CC10 pan adds a Haas delay
  that comb-filters sustained tonal voices in mono. Fix at the composition
  layer: centre sustained beds (pan 64) and get width from panning
  transient sources — don't touch the shared chorus bus (it's near
  mono-neutral and shared across all albums).
- 2026.07.08 — **Encode the dramatic shape as an oracle, twice.** The
  Ninth Bell's "builds and drops" brief became `check_arc` — inequalities
  on per-bar velocity sums (ascent < ascent, void ≤ 0.25× processional,
  feint bar < 0.6× its neighbour, climax = global max, coda ≤ 0.2× climax)
  — plus an `analyze.py` mirror asserting the SAME contour in render RMS
  dB. Composer agents then compose *to the shape*, and the −60 dB void /
  −18 dB climax landed first assembly. A prose brief ("goes somewhere
  dramatic") is unfalsifiable; a contour of numbers is a target and a test.
- 2026.07.08 — **Reproduce a "verbatim" seed by recomputing it, not
  copying it.** The Veil had to be the demo's ch0 gesture exactly;
  `check_intro_fidelity` re-runs `pad_block`/`voice_lead`/`cc_curve` from
  the engine and pins ch0 note-for-note (sorting by jitter-rounded onset
  so ±4-tick humanisation can't scramble same-beat chords). Continuing the
  ground into movement II then needs the intro's FINAL voicing as the
  voice-lead seed, or bar 9 re-spreads and dents the seam.
- 2026.07.09 — **"Authored-channel" is not the same as old-album
  byte-identity.** MM-REQ-KILN-00008 made existing Modal/Organ pitch controls
  start working, but 13 committed MIDIs had already authored those controls
  while the synth ignored them. Scan `render_opus.py::ALBUMS` for authored
  controls before promising byte identity; then make the waiver set explicit.
- 2026.07.09 — **Full-mix audio deltas must follow the rendered signal, not the
  control's intuition** (extended 2026.07.11). The synth demos' first `analyze.py`
  pass failed because wah/Leslie/vowel checks guessed "darkens"/"louder" while the
  full mix measured the opposite after other parts and normalization. Corollaries
  from the T16 guitar work: `--solo` stems are INDEPENDENTLY peak-normalized, so a
  solo-stem RMS measures crest/decay, NOT the channel's level in the mix —
  un-normalize via the CLI's reported `peak`, and judge lead audibility band-limited
  (700–2500 Hz), not broadband (a single lead sits ~18–24 dB under a full mix by
  nature). And KS sustain: a held distorted-guitar note dies because the in-loop
  damper `bright` kills the harmonics that carry the RMS — raise `bright` (NOT `t60`,
  which clamps at pitch and only governs the fundamental); the tanh `amp` adds
  compression sustain for the fastest-decaying high notes.
- 2026.07.09 — **`render_opus.py::ALBUMS` is the listening blast radius, not just
  `albums/`.** MM-REQ-KILN-00017 left album MIDI byte-identical, but the newly
  committed Synth Feature Showcase listening track used GM109/111 and had to be
  refreshed. Scan every `ALBUMS` entry before declaring a synth change asset-free.
  Every newly committed Opus also needs a three-section listening-guide sidecar:
  the renderer permits an absent optional sidecar, but the repository test does not.
  For long Opus refreshes on Windows, stage temp outputs under `target/` in the
  worktree; `os.replace` cannot move atomically from `%TEMP%` on `C:` into a `D:`
  worktree.
- 2026.07.09 — **Generated GM43 contrabass lanes need a floor and centered pan.**
  Spark and Hours After Rain both wrote `chord["bass"] - 12` into program 43,
  producing MIDI 12-23 sustained notes panned left; ferrosintesis turns that into
  sub-bass flatulence. Clamp/raise contrabass beds to at least C2 (MIDI 36) and
  keep sustained low strings centered unless the track has an explicit reason not to.
- 2026.07.10 — **`build.py --track N --verify` verifies in memory and does NOT
  rewrite the MIDI.** Two independent audio-fix agents lost a full iteration to
  stale renders (the unchanged dB reading was the tell): edit → `--track N`
  (writes) → `--verify` → render → analyze, in that order. Corollary from the
  same session: a hard-panned CONTINUOUS stream is pinned near 3 dB mono loss
  regardless of pan value (the Haas copy stays decorrelated at pan 16 or 22) —
  moderating the pan doesn't help; centre the sustained stream or make it
  genuinely transient.
- 2026.07.11 — **Calibrate a timbre oracle against the OLD code first; a plausible
  "fix" premise can be measurably false.** The "harpsichordy" cathedral organ was
  assumed to be integer-buzzy + fast-attack, but measurement showed buzz already
  −27 dB (key 84) and onset already 143 ms — neither harpsichord-like. The real
  driver was static-ness: each additive pipe is a phase-locked wavetable, and a
  per-pipe wind-wander (`Drift` off `age`, ±2.5 cents, seeded from the STABLE
  rank/key seed so `--verify` stays byte-identical) dropped the steady envelope's
  4.5 s-lag autocorrelation 0.44→0.25. The specced high-key voicing surgery was
  DROPPED after a foundation boost moved upper/fund <1 dB (the RSS normaliser
  re-absorbs it) and broke the buzz guard. Drive a timbre voice with an internal
  per-sample counter, not `retune`: unit renders call `render()` once and never
  retune, so a retune-driven modulation is absent in exactly the oracle renders.
- 2026.07.11 — **To add drive/"rasp" to an additive voice, redraw the harmonic
  amplitudes (a band-limited "driven" table crossfaded in), NOT a waveshaper.** For a
  single periodic pipe a memoryless nonlinearity (tanh) produces only integer
  harmonics of f0 with modified amplitudes — it IS an amplitude redraw — plus two
  things you don't want: aliasing (folds the reed's ~19 kHz partials down) and
  inter-note IMD if it shapes a summed chord. The driven-table crossfade gives the
  same spectrum alias-free at ~zero cost and shares the pipe's phase accumulator, so
  the wander rides it. Two oracle corollaries from the reed rasp: (a) a broadband
  "texture noise" layer contaminates an off-lattice anti-alias oracle — its noise
  raises off-lattice energy exactly like aliasing — so measure texture separately or
  drop it (dense driven partials beating in-band already ARE the roughness); (b) an
  off-lattice anti-alias metric must be ABSOLUTE, not a drive-differential: louder
  legit high partials leak more into off-lattice Goertzel bins as drive rises, with
  zero aliasing.
- 2026.07.11 — **For brass "rasp"/cuivré, SPLIT the shaper drive across two
  knees — don't stack a 2nd stage on an already-hard one.** At forte the brass
  lip-tanh already sits near its alias cap (`kws ≈ 3.1` vs `BR_K_MAX 3.2`), so a
  second waveshaper on top barely hardens it (measured on/off 1.04). Splitting the
  drive (stage 1 softens as the cascade opens, a 2nd knee re-hardens) gives a
  genuinely slower, shock-like rolloff (on/off up to ~1.4 in the top band). Two
  corollaries verified in `control_tick`: the loudness scalar `L ≤ 1.0` in sustain
  (`0.10 + 0.90·vn`), so any gate on "L>1" / "(bright−1)" is near-dead — gate rasp
  on `L`/`bright` directly; and the extra harmonics must be shed at high f0 (a
  quartic derate) to hold the 2× alias floor (BR-O11). Top-register ff rasp needs
  anti-aliasing above ~A4 — and first-order ADAA (F = ln cosh, applied STAGE-WISE
  to the cascade) at the existing 2× delivered it (v0.15.1); a full 4×/Fork-B was
  not needed. Three ADAA gotchas from that work: (a) a FLAT rasp floor over-drives
  the mildly-derated upper-mid (A5–B5 get clamped UP and alias under growl) — make
  the floor frequency-gated so it lifts ONLY the top octave (C6+, `smoothstep(900,
  1100,f0)`), leaving A5 at its natural quartic value; (b) the binding BR-O11 alias
  guard is A5, not the highest note F#6, partly because A5's 2200 Hz guard bin sits
  in the BR6 breath band — the guard half-measures breath noise, so isolate breath=0
  when tuning; (c) a pure sine barely aliases through a tanh (its harmonics decay
  before Nyquist), so a spectral unit oracle on the ISOLATED shaper reads the noise
  floor and can't reproduce the voice's aliasing — pin ADAA with a boxcar-mean MATH
  oracle (divided-difference == the shaper's mean over the step) and lean on the
  voice-level guard (BR-O11/O11b) for real-world efficacy.
- 2026.07.11 — **A digital-waveguide string detunes progressively FLAT with pitch if
  `set_freq` under-subtracts the loop latency.** The bowed loop's in-loop reflection
  filter + read/write add ~3.8 samples, not the hard-coded 1; the residual is a
  near-constant sample offset, so cents-flat scales with pitch — ~50 cents flat by the
  cello's A4 (it passed the pitch gate only because the contrabass's test keys topped at
  E4, −36c). Set each waveguide voice's `loop_comp` from a single-note autocorrelation
  sweep; never assume `sr/f−1` (peak-locate AND autocorrelation agree here — real detune,
  not a zero-crossing lie). **UPDATE 2026.07.13: the "inaudible in the contrabass's bass"
  dismissal was WRONG and cost months.** The contrabass shipped at `loop_comp=1.0` on that
  rationale; measured over its OWN compass (E1–G3) it spreads −6c→−46c = 39.5c, and a
  pitch-DEPENDENT error corrupts INTERVALS (a fifth ~14c narrow → a sustained triad beats
  against itself) — worst on the bass, the harmonic foundation. Arthur heard it as "the alt
  bank sounds better" (the alt's offset is constant, hence inaudible). Fixed to 3.85 (the
  cello's value — same `refl_sustain`, same latency). Oracle asserts cents-SPREAD ≤ 5 over
  each instrument's own compass, not a per-note floor. Lesson: never call a pitch error
  "inaudible" from a snapshot — measure the spread over the real compass.
