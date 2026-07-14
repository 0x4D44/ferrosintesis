# Lessons learnt

Distilled, non-obvious gotchas for future sessions in this repo. Cap: 20.
(Currently over cap — due a prune pass.)

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
