# Lessons learnt

Distilled, non-obvious gotchas for future sessions in this repo. **Cap: 20 entries.**

Format (`index-v1`): an entry's **first line is the whole lesson** — the surprise, the fix,
and a `file:symbol` pointer, in ONE plain-text line (≤~120 chars). The SessionStart hook
injects **only those first lines**, so each must stand alone; the indented lines beneath are
lookup detail and are never injected. Newest first. Durable project facts and conventions
belong in `CLAUDE.md`, not here.

<!-- lessons-format: index-v1 -->

- 2026.07.25 — **A file with a pinned SHA-256 needs `-text` — core.autocrlf greens it locally, reds every fresh clone** (`.gitattributes:_readme_and_license_*.txt`).
  - The retained Freesound licence manifests are committed as byte-exact EVIDENCE: their SHA-256 is recorded in
    `crates/ferrosintesis-samples-ccby/PROVENANCE.md` and checked by `crates/ferrosintesis/src/provenance.rs`.
    With `core.autocrlf=true` (the fleet default on Windows) git rewrote them to CRLF on checkout, so every
    recorded hash missed — but only on a FRESH clone, never on the machine that committed and hashed them, which
    is exactly why the attestation looked green to its author and to every local re-run.
  - Verify a byte-pinned file by re-hashing the COMMITTED TREE, never the working copy: `git checkout-index` into
    a scratch prefix and hash there. A working-copy hash attests the bytes your own filters produced, not the
    bytes anyone else gets. The same trap waits for any hash, signature or golden pinned on a `text`-eligible file.
- 2026.07.25 — **A tanh drive normalised by `tanh(g)` is a VOLUME knob — solve make-up at the level the voice really runs at** (`voices.rs:LEAD84_NOMINAL`).
- 2026.07.25 — **A compensation constant marks an unfixed upstream bug — fix the cause and delete it** (`voices.rs:VEL_LEVEL_EXP`).
  - `t[6] = 1.500` was added to drag GM6's composite back under the <3 dB velocity contract, justified in its own
    comment as "its LA sample layer does not inherit that compression" — i.e. purely to paper over MM-BUG-KILN-00030.
    But `ScaledVoice` applies it to the WHOLE voice, so `(v/127)^-0.5` made the harpsichord body 5.02 dB LOUDER at
    v40 than v127 — backwards — and applied under `--no-samples` too, where there is no sample layer to compensate.
  - That collateral damage was filed separately as MM-BUG-KILN-00044, and the two then deadlocked: 00044's record
    said "do not fix 00030 separately before this is decided", while fixing 00030 properly was exactly what made the
    constant removable. Fixing the cause (`LaFx::vel_sense`, so the onset inherits the model's compression)
    dissolved both. **Read a compensation constant's comment as a bug report — it names the defect it hides.**
  - The guard for this class must be DERIVED from the compensation table itself:
    `velocity_law::corrected_programs_still_rise_with_velocity` walks every program the table corrects and requires
    it still get louder with velocity. A hand-listed exception would have inherited the same blind spot.
- 2026.07.24 — **Bank layers must differ in TIMBRE, not level — `vel_amp` owns loudness** (`sampler.rs:LaVoice`).
  - `LaVoice` scales the sample by `vel_amp(vel)`, the SAME law as the wrapped model, so a multi-velocity
    bank's soft/hard captures supply spectrum, never gain. Per-file peak-normalise-to-0.9 in
    `prepare.py:trim_to_onset` is therefore CORRECT, not a calibration bug: baking a measured soft-to-hard
    level span into the samples would fight `vel_amp` and unbalance the bank against every other instrument.
  - Corollary for tuning: set `Zone.root` = the MEASURED f1 and the engine repitches to exact ET
    (`ratio = target_hz/zone.root`), so a flat, Railsback-stretched real piano plays in tune while keeping the
    per-note inharmonicity that makes it sound like itself. Normalise intonation, keep timbre.
  - Corollary for LAYER COUNT: measure the captures against each other before shipping one per dynamic. The
    B1 upright's soft pass sat +0.8 dB from normal in noise-subtracted tilt — the same timbre — for 11 dB less
    SNR, so it was hiss with no tone to pay for it and got dropped. Two captures, split at velocity 60.

- 2026.07.24 — **Commit bulky sample sources as 160 kbps opus — roots re-slice to <0.75 cents** (`prepare.py:_bake_b1upright`).
  - The raw DR-05 takes are hundreds of MiB as WAV, far too big to commit, which would leave the baked crate
    unreproducible. `ropusenc` then `ropusdec` at 160 kbps is transparent enough to be the SOURCE OF RECORD:
    re-slicing the decoded takes reproduced every measured root to under 0.75 cents, so `prepare.py` regen stays
    byte-identical to what ships. One marginal note (a -15 dBFS B7) fell below the onset detector after the lossy
    pass and needed a `--assign` override — expect a handful of those, not a systematic shift.

- 2026.07.23 — **Measure a sample's root, width, format and onset ISOLATION — never trust its name or label** (`prepare.py:trim_to_onset`).
  - Isolation, not tuning or note availability, is usually the BINDING constraint: `trim_to_onset` needs ~30 dB
    of pre-onset quiet and grabs the PREVIOUS note without it. On Arthur's Eastman E1D it cut ~80 notes per take
    to 48/56 usable and forced two substitutions in the picked bank (B2 for A#2, A#4 for B4). That is free,
    because zone roots are MEASURED, not nominal — the nylon bank already stands B2 in for a missing A#2. A
    SELF-cut bank does not need that 30 dB at all: cut at the local envelope minimum before onset and fade; the
    isolation gate is only for blind onset-trimming.
  - Octave traps, four of them, all fixed by measuring rather than trusting. (1) A bare harmonic template scores
    a SUBHARMONIC exactly as well as the fundamental — score `energy x harmonic-coverage` instead, since a
    subharmonic misses all its odd multiples. (2) A dominance-weighted detector calls a normal dreadnought low E
    an octave high (the picked E2's H1 sits 3.5 dB under H3); settle it against the SHIPPED reference, never an
    absolute threshold — perceived pitch follows the harmonic series, not the loudest partial. (3) Autocorr grabs
    the 2nd harmonic whenever the F0 ceiling admits it (ocarina, recorder, banjo all did): keep a zone span UNDER
    one octave so one ceiling separates f from 2f, or add the family to `TWO_F_STRONG` for a per-note ceiling of
    label×1.5 — probe first, `measure_f0(x, sr, 150, label*1.5)` vs a generous ceiling. (4) File labels lie in
    BOTH directions — VCSL keyboard/ocarina sit an octave BELOW sounding pitch, ganjo banjo an octave ABOVE;
    name the destination by the MEASURED pitch, never the source label. Independently corroborated:
    `banjo_extract.py`, landed the same day by another task, arrived at the same two gates.
  - Measure the root over the RING, not the strike: the CdM Gong Ageng strikes ~80 Hz but its sustained partial
    is ~99 Hz (G2) → `sampler.rs:GONG_ROOT_HZ=99.4`; an 80 Hz root rendered every key a major third sharp.
  - Check `getsampwidth()` and the format tag BEFORE any numpy probe. FreePats WAVs are 24-bit (`sw=3`) — reading
    them as 16-bit yields noise that folds FLAT and looks like a perfect loop, so a "candidate fix" measures
    better than the real one (`prepare.py:read_wav` handles sw==3; numpy `frombuffer('<i2')` does not). Cost me
    and an independent subagent a cycle each. ganjo WAVs are IEEE-float (fmt tag 3) and stdlib `wave` errors
    "unknown format: 3" — transcode to 16-bit PCM with ffmpeg at fetch (`ensure_banjo_sources`).
  - The spectrum, not the name or licence, decides fitness: a licence-only search called VCSL "Gong 1" a
    near-pitchless tam-tam, but it is a PITCHED gong (sharp 143 Hz/D3, 95%-concentrated) — wrong for a CC0=1
    tam-tam. Three sourcing dead-ends in one build were all invisible to name/licence.
  - Gate a candidate on the CHARACTER you want, not on a proxy for it: a fret RASP is quasi-periodic, so a "no
    ringing note under the rasp" harmonicity gate rejected ALL 42 clean GM 120 candidates — the winding-pass
    rate gives a real slide autocorrelation of 0.28–0.44, and that IS the zip we want. The genuine note
    contaminants separate on spectrum instead: they peak at 50–160 Hz with the 125 Hz band AT the peak, while a
    rasp peaks at 1–3 kHz with low-mid 20–30 dB below. Gate on peak band 1–3 kHz, ≤20 % energy >4 kHz, low-mid
    ≤ −15 dB — never on periodicity or pitch (`voices.rs:gm120_sampled_is_a_narrowband_rasp_not_a_hiss`).
  - Re-micing cannot create low end the instrument never produced: Virtuosity's 18" jazz kick has NO 30–70 Hz sub
    in ANY mic set (fundamental ~80 Hz; the overhead's "sub" reading is room rumble). A deep-kick ask needs a
    modeled-sub layer or a ~100 Hz-hinged shelf on the fundamental.

- 2026.07.23 — **A bank-wide MEAN level is the wrong statistic for an LA gain that TREBLE oracles police** (`voices.rs:LA_EASTPICK`).
  - Fitting the new steel gain on mean crossfade-window RMS (0.05-0.28 s over all zones) gave 0.229 and looked
    right, but a real guitar's top zones are far quieter relative to peak than its middle (A#4 0.110 / F5 0.095
    against the Martin's 0.206 / 0.210), so keys 76/79 landed at 0.78-0.80 — astride
    `la_steel_high_key_level_parity`'s 0.8 floor. The mean hides the only region under test.
  - Fit with `print_steel_wrap_level_ratios` (the `#[ignore]` harness exists for exactly this) and re-check the
    sweep's maximum against the 2.2 ceiling. Corrected to 0.26 picked / 0.242 plucked.
  - Corollary: an oracle that measures only the DEFAULT bank silently stops covering a program once it grows
    alternates — `altbank_steel_alternates_are_level_sane` restores that cover.

- 2026.07.23 — **Sweep the worst COMBINATION — a one-knob-at-a-time oracle misses a shared-budget breach** (`engine.rs:amp_drive_knob_holds_alias_floor`).
  - The driven-guitar amp exposes six knobs that all draw on ONE −40 dBc alias budget. The oracle swept Drive
    while holding every other knob neutral, so it passed at −42.5 dBc — but Drive 127 + Tone 127 measured −39.0,
    and adding Presence −35.0, i.e. 5 dB over. **The breach SHIPPED to trunk** and surfaced only when a later
    task widened a range and re-tested pairs.
  - Post-clip is NOT automatically safe. "Cabinet EQ is after the shaper, so it cannot alias" is wrong for a
    RATIO metric: Presence boosts 2.6–2.8 kHz — exactly where alias lands, and ABOVE the fundamental — so it
    lifts alias-to-signal without creating one new alias product.
  - A shallow constraint curve hides the cliff: alias moved only −42.5→−33.7 dBc as `k` went 1.2→3.0, so nothing
    looked dramatic while the budget was being consumed.
  - Wherever several controls spend ONE budget (alias headroom, gain staging, voice count, CPU), the worst case
    is a combination — assert it explicitly, and treat a per-parameter green as evidence about that parameter
    only.

- 2026.07.23 — **Prove a metric can SEE your change — check its band support; zero-crossing pitch and log-bin `centroid` lie** (`testutil.rs`).
  - Driven-guitar lead amp A/B (scratch `_cal/amp_ab` harness, not in-tree): bands from 200 Hz said the new
    amp/cab moved main-vs-alt separation +0.08 dB with some probes going the WRONG way; the identical
    comparison with bands from 80 Hz says +0.80 dB, rising on every probe — because the two biggest moves
    (pre-clip HPF 90→120 Hz, cab resonance 100→120 Hz) sit BELOW 200 Hz. I nearly concluded my own change
    did nothing.
  - Score against a CONTROL render, not an absolute bound. `engine.rs:gm22_cc1_is_harmonica_vibrato_not_leslie`
    held its `reset_late <= reset_early + 2.0` "no CC1 leak" bound only because the setup's authored `CC93=0`
    was being DISCARDED at the next Program Change (MM-BUG-KILN-00033), and the restored chorus wash suppressed
    the envelope detector; fix the discard and the harmonica's own delayed-onset vibrato surfaces (AM 0.00→6.00).
    A never-modulated GM22 control settles it in ONE measurement — 0.00→6.00, spread 3.11, identical to the
    post-reset channel, so there was no leak. The control is also STRICTER than the bound (it pins reset *to* the
    un-modulated voice, not to a range), so switching to it is a fix, not a weakened assertion. Corollary: when a
    test authors a controller purely as scaffolding, check the engine actually honours it — ours silently did not.
  - A SIGNED two-band ratio through the full engine is dominated by which harmonics land in which band — it
    swung −1.7…+8.8 dB across ADJACENT keys for a FIXED pair of amps. Use a direction-agnostic multi-band
    DISTANCE, scored as a register mean plus a per-key non-collapse floor.
  - A large gap in a long-tail metric can coexist with "sounds identical": the driven banks' sustain-index gap
    is 14→60 dB over keys 45–69, yet they sound the same — a lead line's notes last a few hundred ms, and over
    THAT span both ran the same amp.
  - Pitch estimators (merged from 2026.07.17): zero-crossing counters read the 2nd harmonic leaking through their
    lowpass (452.5 Hz for a true 440) — three separate "pitch broke" scares were this. Use the Goertzel
    `testutil::peak_locate` + parabolic refinement; keep crossings for pure-sine calibration only. A fixed
    Goertzel bin (~1.5 Hz) misses harmonics wandering ±60 Hz under vibrato — use band-integrated FFT fractions.
    Never `peak_locate` an FM carrier when β≳0.5 (the first sideband can outrank it) — use the known pitch.
    Reading a harmonic ratio inside a vibrato'd window under-reads upper partials (harmonic n carries n× the
    modulation index, so its energy leaks into sidebands a fixed bin misses) — read harmonics strictly PRE-vibrato.
  - Centroid: the 20-log-bin `testutil::centroid` is leakage-dominated on a clean harmonic lattice — a real 3×
    filter-cutoff sweep reads as ~1.1×, because its fixed Goertzel bins almost never land on a harmonic. Use the
    Hann-windowed exact-DFT `testutil::spectral_centroid` on a settled window. It is also magnitude-weighted, so
    an amplitude taper inside the measurement window drags it toward the loud end (a sin-windowed chirp read
    ×1.17 where the sweep was ×1.4) — flatten the envelope or move the window.
  - Noise: any tilt/centroid statistic puts broadband noise in its NUMERATOR, so the NOISIEST capture scores
    brightest — exactly backwards. The B1 upright's soft layer (28 dB SNR) sat ~1 dB from its normal layer
    (39 dB) and raw the gap was unreadable; estimating the noise PSD from each strike's own pre-onset gap and
    subtracting it in the power domain showed the +0.8 dB was genuine, which is what justified deleting a whole
    recorded layer (`sampler.rs:b1upright_bank`). Match SNR across the takes you compare, or subtract — never
    compare tilts across unequal noise floors.
  - Prove the A/B actually DIFFERS before measuring it. `tools/gm0-audition/renders/_tb_b1.mid` is the OUTPUT of
    `prep_audition.py`, so it already carries `CC0=5`; a mid-piece excerpt tool replayed that latched controller
    as carried-forward state and it beat the bank being injected, making five "variants" byte-identical. Every
    one sounded plausible. An A/B harness must compare samples and say "IDENTICAL — no-op" before reporting any
    number.
  - Levels: `Rng::white()` is UNIFORM in [-1,1), so its RMS is 1/√3 ≈ 0.577, not 1.0 — the WD-O5 breath-fraction
    oracles were designed against a unit-RMS assumption and every band came out ≈1/0.61× too high while the model
    was correct throughout. `Biquad::bandpass(fc,Q)` on white outputs RMS ≈ √(π·fc/(Q·sr)) — a narrow, cheap way
    to size a tracked breath bed. `spectral_band_rms` is Hann-windowed, so ratioing it against raw `rms()` bakes
    in the window's power factor and deflates any "band fraction" — compare spectral-vs-spectral only.
  - A single-harmonic ratio ("h3 re h1") is an UNSTABLE timbre proxy — it swings ±40 dB with which harmonic lands
    on a formant. The choir "hollow-notch" fork chased the SC-55's aah h3 "−14 at k60", but the SC-55's own h3
    swings +26 (k52) → −12 (k60) → +14 (k64): the whole target, and a prototype "validated" at k60, was a
    register-snapshot artifact. The real, stable defect was centroid over-brightness, fixed by preset darkening
    (`CH2_HUM_LP` 8000→3400, cluster/F2 trims), not a Klatt cascade. Measure brightness as centroid across the
    REGISTER at 5–6 keys, and never freeze a vowel ordering from one key ("GM54 is darkest" held ONLY at k60).
  - A "spread" oracle across instruments must fix PITCH, or it measures pitch not timbre. Four v0.9 oracles
    measured the wrong thing while the mechanism was fine: brass `centroid/f0` ordered tuba<trumpet, but at
    E1-vs-C5 the 100 Hz centroid floor drops the tuba's fundamental and inverts it; the reed anti-alias test used
    the bari (best case) not the soprano (worst); choir shimmer's ±3–7 Hz FM grid overlapped the static detune
    cluster; the crash-twin oracle measured a window where the twins were already −70 dB. Render at matched pitch
    / worst case / the feature's live window, clear of confounding static structure.
  - `--solo` stems are INDEPENDENTLY peak-normalized, so a solo-stem RMS measures crest/decay, NOT the channel's
    level in the mix — un-normalize via the CLI's reported `peak`, and judge lead audibility band-limited
    (700–2500 Hz), not broadband (a single lead sits ~18–24 dB under a full mix by nature).
  - Auditioning voices one at a time (`demos/ferrosintesis_reference/`) has four load-bearing harness facts.
    CC120 is the ONLY MIDI lever that stops a ringing voice — CC121 only note-offs *held* notes
    (`engine.rs:1468`) and CC123 is a release, while plucks decay up to 14 s, so without it the tail bleeds into
    the next slot. CC120 does NOT flush the reverb/chorus/echo tanks (the gap is silent only because the sends
    are zeroed), and CC91=0 alone is not dry: a program change re-derives a NON-ZERO CC93/CC94 from `fx_profile`
    for ~76/128 programs, so author CC91/93/94=0 *after* every PC. Oracles there must be RATIOS, never absolute
    floors — the CLI peak-normalises the whole render (`normalize_to_i16`, `scale=target/peak`), so one louder
    voice rescales every other slot. And a "raw voice" reset must OMIT CC71/CC74 (they instantiate the wah
    filter, `engine.rs:1286`); an effects track that DOES use the filter must reset with CC121 between demos, or
    the resonance section colours everything after it. Measured: CC120 + zeroed sends hits the −96 dB dither
    floor within 50 ms.

- 2026.07.21 — **Level measurements lie until you gate out the unconditional master `BusGlue` — it squashes what you're measuring** (`engine.rs`).
  - It compresses 2:1 above `thr=0.32` with a +1.5 dB 95 Hz shelf, is applied unconditionally to the master, and
    cannot be disabled through the public API; bass-heavy programs trigger it first. A per-program calibration
    needs a throwaway build that gates it out — zeroing `PROGRAM_TRIM_DB` alone is NOT sufficient.
  - There is NO per-instrument loudness normalization, only whole-mix −18 LUFS; per-program balance is nudged
    toward the SC-55 by `engine::PROGRAM_TRIM_DB[128]` (melodic strip `g*=trim`, ch9 exempt, level-only and
    timbre-neutral since `g` feeds dry+sends together). A solo-probe corrected voice still lands ±0.5 dB off its
    nominal trim because the glue is nonlinear (benign).
  - Metric traps: whole-note RMS unfairly penalizes DECAYING voices (ferro guitars read −15 dB "quiet" vs the
    SC-55, but that is faster decay, not level — use an early-window RMS for plucked/percussive, whole-note only
    for sustained); instantaneous PEAK is too spiky.
  - Reusing a percentile helper as a MAX put median 0.41 / max 18.77 dB of error into the derived trims:
    `voices.rs::percentile` was floor-rank, not the nearest-rank its doc comment claimed, so at n=9
    `percentile(x, 0.95)` returned the SECOND-largest (MM-BUG-KILN-00055 — now fixed and pinned by
    `voices.rs:percentile_uses_nearest_rank`). For a single-note window use an explicit `max`;
    `crates/ferrosintesis-cli/examples/calmeter.rs` documents the three conventions and why they are not
    approximations of each other below n≈20.
  - `voices::VEL_LEVEL_EXP` is PROGRAM-indexed, so a program whose samples-ON and samples-OFF voices have
    different RAW velocity laws can't be compensated for both from the table (GM76: samples-on
    `BottleLoopVoice` k≈0.39, samples-off modeled Wind bottle k≈2.49). Wrap the MODEL in `ScaledVoice` inside its
    route arm — the comp must track the VOICE, not the `samples` flag. The velocity sweep runs `samples=true`
    ONLY, so a samples-off regression is invisible; drums solved this via
    `drums.rs:drum_vel_level_exp(kit, samples, key)`. Guarded by
    `velocity_law::modeled_gm76_follows_the_square_law_in_no_samples_builds`.
  - A true-peak ceiling on the WAV does NOT survive lossy Opus: ropusenc's 96k VBR + 44.1→48 kHz resample adds
    ~1.6 dB of inter-sample true peak typically, up to ~2.9 dB on the brightest/densest material — hence
    `render-catalog`'s `TP_CEILING = -4.5`. Probe the BRIGHTEST/DENSEST track before picking a ceiling; a milder
    track under-predicts the overshoot and costs whole-catalog re-render cycles. Loudness normalization under a
    peak ceiling leaves high-crest tracks below target (limiting removes loudness), so `normalize_loudness`
    iterates and converges from below so it never overshoots.
  - Probe MIDI period is tick math, not intended seconds (960+240 ticks = 1.25 s, NOT 1.5).

- 2026.07.21 — **Flush denormals at 1e-34: 1e-20 is a NORMAL f32, so flushing there is not byte-transparent** (`dsp.rs:flush_denormal`).
  - MM-BUG-KILN-00027. Every f32 add's round-to-nearest is a discontinuity (one threshold per ULP), so zeroing a
    state the baseline kept makes δ teleport to a full 1-ULP jump the first time an exact sum straddles a
    boundary; BusGlue's transient-displaced `if level>env` atk/rel branch then amplifies it to ~2 LSB (measured
    on Wire and Wake: one 4.8 s −84 dBFS self-healing burst). 1e-34 keeps the perf fix (still ≫ subnormal
    1.18e-38) and drops the per-add tie hazard ~1e-12 → ~1e-26.
  - Localize such diffs by flush-site bisect on the RAW f32 dump (`crates/ferrosintesis-cli/examples/raw_dump.rs`),
    not the normalized WAV — the true-peak limiter/normalizer smears a sub-LSB signal diff into a visible span
    and will mislead you.
  - `cargo build -p ferrosintesis-cli --example X` does NOT rebuild the `ferrosintesis.exe` bin (use `--bins`).

- 2026.07.20 — **A SysEx event in a MIDI *file* is `F0 <vlq len> <payload>`, not the raw wire bytes.**
  - Emitting `F0 7E 7F 09 01 F7` (GM System On) makes every parser read `0x7E` as a 126-byte length and swallow
    the rest of the track, so the file renders as SILENCE on ferrosintesis, the SC-55 and the S-YXG50 alike.
  - A malformed probe fails identically on every engine — if *all* references go quiet at once, suspect your
    generator, not the engines.

- 2026.07.20 — **Score a sustain loop by `wrap_error_db` + amplitude balance — seam value+slope rates the BROKEN window better** (`prepare.py:find_loop`).
  - Value+slope at ONE sample pair is 2 constraints, satisfied at ~2H phases per cycle, so it is degenerate on a
    rich tone: it rated a broken non-integer-period chanter_G5 window 11× better than the good one. Score against
    the source's real continuation instead. Oracle: `sampler.rs:looped_sustain_banks_are_loopable`.
  - Unit-test a loop finder with a HARMONICALLY RICH tone — a single sine identifies its phase from value+slope,
    so the broken search passes. Search the START too, not just the endpoint.
  - Keep the window SHORT: a 0.4 s loop repeats at ~2.5 Hz where the ear counts clicks, and cannot dodge the
    take's own drift (two chanter zones carried a 4 dB monotone ramp INSIDE the loop).
  - Seam-clean is NOT flat. Integer-period + low value/slope only guarantees the WRAP joins; the interior can
    still ramp, and a long "clean" loop spans the note's decay and pulses loud→silence→loud at ~3 Hz. Cost must
    add |rms(first half) − rms(second half)| and cap length (0.05–0.13 s, `le` < ~0.50 s, clear of the recorded
    release) — `sampler.rs:find_sax_loop`, oracle `sax_loop_level_parity_and_flat`. Measure steadiness by
    spectral-centroid drift across the loop halves, not the raw region's liveness (which includes the note's own
    envelope). One output gain can't level-match GM 64–67: the samples are peak-normalised uniformly but the
    modeled reeds differ ~7 dB, so use a per-program `SAX_LOOP_GAIN[4]` calibrated to the model each replaces.
  - Don't trust a soundfont's own loop points: ffmpeg's Ogg-Vorbis decode of SF3 drops ~80–100 trailing frames
    (Vorbis priming/padding), so `endloop` lands PAST the decoded end, and clamping it shortens short low-note
    loops below one period and DETUNES them (clavinet G1 read +200 cents). Loop PITCH-SYNCHRONOUSLY — carve an
    exact integer number of periods (`T = sr/originalPitch`, accurate to a few cents) from the steady body with a
    length-preserving crossfade at the wrap (`prepare.py:_bake_clavinet_note`). SF3 `shdr` start/end are BYTE
    offsets into `smpl` (each a self-contained Ogg), NOT PCM frames as in SF2; the sample NAME octave is +1 vs
    `originalPitch` (name "C4" = MIDI 48 = C3). RIFF-walker gotchas: a chunk header's size field is a SIZE not an
    end offset (`end=off+size`); a `LIST` body starts after its 4-byte type (`data=off+12, size-4`).
  - `foldZ` (a z-score of folded novelty) SATURATES — it reads 5.7–6.5 on signals whose true excess is 1.02. A
    looped signal is exactly periodic, so a fold at the loop lag peaks whether or not the wrap is where the
    energy is. Use peak/median with explicit DECOY-LAG nulls (×0.73/×1.37/×1.91), or you will "confirm" an
    artifact that isn't there — it falsely convicted the bagpipe DRONES while the chanter was the true culprit.

- 2026.07.19 — **LA sampling is ONSET-ONLY — a sustain or noise complaint needs MODEL work, never a new sample** (`sampler.rs`).
  - Proven: brass HOLDS render bit-identical with `--no-samples` (the LA layer has crossfaded out by ~0.3 s). So
    an IDENTITY/attack complaint (40==41 viola sameness, recorder identity, timpani strike) wants a new CC0 onset
    bank; a SUSTAIN/noise complaint (brass "holds synthetic", sax "fuzz", flue "sshsshssh", choir) wants model
    work and is usually a handful of constants. Round-3 feedback: most complaints were the model side, i.e. cheap.
  - A/B every voice against a REAL GM module: `mdmidiemu --synth sc55|mu80` (ROMs at `D:/language/mdsc55/roms`).
    SC-55 is the reliable spectral reference (~40 ms onset, no swell); MU-80 is often reverb/swell-dominated
    (character only).
  - Watch for oracles that ENCODE the defect — three were found blocking the correct fix (`harp_46_shimmers`
    rewards the octave-hollow balance; choir CH2-O2 pins GM54 bright; recorder WD-O1 asserts `h2≥h3` backwards).
    Recalibrate them against hardware IN the fix commit.
  - `wrap_var` DETUNES the wrapped MODEL ±6c (`sampler.rs:wrap_var` → `set_pitch(var_mult)`), so an
    exact-multiple Goertzel on a wrapped guitar render under-reads harmonics ~sinc(k·f·Δc·T) — −9 dB at h6 over a
    0.25 s window. Write spectral oracles on the BARE model, or measure at k·f·var_mult.
  - A fast-decaying plucked-KEYBOARD layer needs a LOWER wrap gain than the guitars (`voices.rs:LA_HARPSICHORD`
    0.28 vs `LA_GUITAR` 0.42): a real harpsichord's high strings damp fast in the MODEL but the recording's body
    still rings, so at 0.42 the sampled 50–150 ms window sits 2.9× above the model's decay shape and trips
    `la_level_continuity` at C5. The quill spike (0–50 ms) is before that seam window, so lowering the gain keeps
    the attack character.

- 2026.07.19 — **Calibrate an oracle against the OLD code and MEASURED inputs — a plausible "fix" premise is often measurably false.**
  - Input population: take the parameters from measurement, never from the assumption you are trying to verify.
    Fixing `prepare.py`'s de-click fade, I "proved inertness" with a test fed 8–300 ms of lead-in and shipped
    green — but the real bank is trimmed FAR tighter (median onset: piano 120 samples, violin 3, steel 8), so the
    change silently re-cut 131 committed WAVs and would have delayed every layered attack by up to 7 ms.
    `git status` caught it; the passing test did not. **The sample bank IS the oracle** — regenerate and diff the
    committed WAVs before believing any `prepare.py` change is inert.
  - A constant does not have to drift to become wrong; the material underneath it can move instead.
    `prepare.py`'s fixed 2 ms fade-in was sized for day-one violin (`ce99cda`, ONE commit ever) and every family
    added since inherited it — 74 of 210 sources had their onset INSIDE the fade window and their attack crushed.
    Re-measure a shared generator's constants against NEW material.
  - "The file authors nothing, so nothing is applied" is another such false premise: `engine.rs:fx_profile`
    hands GM 8–10 an UNAUTHORED 0.15 echo send, and at the Tubular Bells opening that bus time is a dotted
    quaver (300 ms at 150 bpm) against a metronomic 200 ms quaver ostinato, so every repeat landed 1.5 slots
    late carrying the wrong pitch for its position and ping-ponged hard L/R — the "echoy shimmer". SIDE/mid
    energy is the tell for a stereo bus effect and it finds the mechanism (0.000 dry, 0.033 reverb-only, 0.092
    default; the side signal cross-correlates with the DRY render at exactly the echo time, r = 0.86). Level
    alone would have missed it — inside the dense line the echo sat −21 dB under the programme and lifted the
    off-beats 0.14 dB. Pin the corrected send by RATIO, never as a constant: render again AUTHORING the retired
    value as CC94 and assert the unauthored render sits at new/old of it
    (`engine.rs:mallet_bus_echo_is_off_for_glockenspiel_and_a_trace_for_its_neighbours`). Calibrate against the
    OLD constants before believing the new ones.
  - The "harpsichordy" cathedral organ was assumed integer-buzzy + fast-attack; measurement showed buzz already
    −27 dB (key 84) and onset already 143 ms. The real driver was static-ness — a per-pipe wind-wander (`Drift`
    off `age`, ±2.5 cents, seeded from the STABLE rank/key seed so `--verify` stays byte-identical) dropped the
    steady envelope's 4.5 s-lag autocorrelation 0.44→0.25. Drive a timbre modulation from an internal per-sample
    counter, not `retune`: unit renders call `render()` once and never retune, so a retune-driven modulation is
    absent in exactly the oracle renders.
  - Don't pin a mechanism to the baseline it exists to move away from: preregistering seam-parity-vs-baseline AND
    move-toward-recording in ADJACENT windows caps timbre change at the parity budget, so a feature that succeeds
    must fail one gate (`voices.rs:recmatch_*` r3 park).
  - Re-voicing a common GM voice breaks oracles that use it as a live CONTROL — grep `stats(<prog>)` /
    `make(<prog>,…,true)` before changing its timbre. Swapping GM0 upright→Salamander grand inverted both clauses
    of `voices.rs:harpsichord_jangles_with_a_four_foot_choir`, which measured the harpsichord centroid against a
    GM0 render. Fix by moving the control to GM1 (the upright it was calibrated on) and recalibrating against the
    intended reference IN the commit — don't weaken.
  - A "bug" can be test-pinned as a feature: GM20's reed-organ half-integer partials read as a parallel-fifth
    "organum ghost" but are pinned by `voices.rs:reed_organ_accordion_harmonica_have_free_reed_character` as
    intentional off-harmonic character. When a scoped change passes but the FULL suite fails, the failing test may
    be telling you the "bug" was a design choice — escalate, don't override on an unverifiable ear judgment.

- 2026.07.19 — **Album-scale generative fan-outs don't fit the shared 5-h window — serialize composers and feed a digest, never parallelize.**
  - Generated album MIDI is committed source today, not a hypothetical future regeneration.
    A copied writer can therefore corrupt many live files at once: six stale overlap-clamp
    lineages left 10,398 ambiguous re-strikes across 39 MIDIs. Regenerate every owned output
    and gate the whole catalog with positional `(track, channel, pitch)` pairing
    (`crates/render-catalog/tests/album_midi_overlaps.rs`), never a pending-note queue.
  - Two parallel fleets died mid-window (10-wide, then 2-wide: ~0.9 M tokens, zero tracks). One-at-a-time
    composers fed a compact pattern digest (Slipstream's `COMPOSER-NOTES.md` instead of re-reading the 1.7k-line
    exemplar) landed 10/10 at ~150–250k tokens/track, with per-track verify+commit making every landing durable.
  - A composer/generator subagent emitting a big module can die on the per-response 64k output-token cap BEFORE
    any file write — instruct it to write the file in several small Write/Edit chunks, never one giant call (The
    Remaining T5, ~900-line module; the worktree was left clean both times, so just relaunch).
  - On Opus, heavy compose/surgery subagents must return PLAIN TEXT, not a StructuredOutput schema — six Winter
    Guests composers each did full work then all failed the schema-emission retry cap while the files were fine.
    Reserve workflow `schema:` for short-output lenses.
  - A verification subagent that runs `cargo test`/`clippy` in YOUR worktree during a live gate corrupts the
    gate's test binary (abnormal exit `0xffffffff`), and a `cargo test … | tail` pipeline returns `tail`'s exit 0,
    MASKING the failure. Run build-executing skeptics in a separate worktree (or after the gate), and grep the
    `test result:` line rather than trusting a tail-masked exit.
  - Shared voice structs are where parallel designs collide: strings (48–51) and choir (52–54) are both
    `SawStack`, and designed in parallel one added a stack-level `vib_depth` the other deleted. Per-family review
    passed both; only a cross-section critic caught it. Add an explicit assembly/critic pass over shared structs
    (`SawStack`, `Layer`, `fx_profile`, the golden fixture) before trusting the union.
  - `deltic timeout <s> python - <<EOF` hangs — deltic timeout gives the child `Stdio::null()` (no stdin
    passthrough, no opt-in flag), so on Windows python takes the REPL path and `_pyrepl` crash-loops on the
    invalid console handle until the deadline (exit 124). STILL TRUE — MDK-BUG-KILN-00115. Write the probe to a
    temp `.py`; redirecting (`… < file`) does NOT help (it redirects deltic's own stdin). (The old "`deltic
    timeout bash script.sh` can't exec `D:/…` paths" gotcha was WSL-bash program resolution, not exec/path
    mangling — FIXED in MDK-BUG-KILN-00107, so current deltic resolves the caller's Git Bash correctly.)

- 2026.07.16 — **White noise through a memoryless nonlinearity stays FLAT — band-limit turbulence below f0 or you get hiss, not growl skirts.**
  - S_y(f) = Σ|W_k|²·S_n(f−k·f0): shifting and summing a flat PSD is still flat, whatever the drive. For skirts
    around partials (the sax G3 gate) the injected turbulence must be band-limited well below f0 *before* the
    shaper — RD10 lowpasses it at 0.30·f0. Corollary for oracles: a single one-pole "sub-audio" probe leaks a
    349 Hz carrier at −6 dB/oct (~3 %) — cascade poles before calling a residue DC.
  - To add drive/"rasp" to an ADDITIVE voice, redraw the harmonic amplitudes (a band-limited "driven" table
    crossfaded in), NOT a waveshaper: for a single periodic pipe a memoryless tanh produces only integer
    harmonics with modified amplitudes — it IS an amplitude redraw — plus aliasing (folding the reed's ~19 kHz
    partials down) and inter-note IMD if it shapes a summed chord. The crossfade shares the pipe's phase
    accumulator, so the wind-wander rides it.
  - For brass cuivré, SPLIT the shaper drive across two knees — don't stack a 2nd stage on an already-hard one.
    At forte the lip-tanh already sits near its alias cap (`kws ≈ 3.1` vs `BR_K_MAX 3.2`), so a second waveshaper
    barely hardens it (on/off 1.04); splitting (stage 1 softens as the cascade opens, a 2nd knee re-hardens)
    gives on/off up to ~1.4 in the top band. In `control_tick` the loudness scalar `L ≤ 1.0` in sustain
    (`0.10 + 0.90·vn`), so any gate on "L>1" or "(bright−1)" is near-dead — gate rasp on `L`/`bright` directly.
    Shed the extra harmonics at high f0 (a quartic derate) to hold the 2× alias floor (BR-O11); first-order ADAA
    (F = ln cosh, applied STAGE-WISE to the cascade) at the existing 2× delivered top-register ff rasp (v0.15.1)
    — a full 4× was not needed. ADAA gotchas: a FLAT rasp floor over-drives the mildly-derated upper-mid (A5–B5
    clamp UP and alias), so gate the floor to the top octave only (`smoothstep(900,1100,f0)`); the binding alias
    guard is A5, not the highest note, partly because A5's 2200 Hz guard bin sits in the BR6 breath band (isolate
    breath=0 when tuning); and a pure sine barely aliases through a tanh, so a spectral unit oracle on the
    ISOLATED shaper reads the noise floor — pin ADAA with a boxcar-mean MATH oracle and lean on the voice-level
    guard for real-world efficacy.
  - Oracle corollaries: a broadband "texture noise" layer contaminates an off-lattice anti-alias oracle (its noise
    raises off-lattice energy exactly like aliasing) — measure texture separately or drop it; and an off-lattice
    anti-alias metric must be ABSOLUTE, not a drive-differential, since louder legit high partials leak more into
    off-lattice Goertzel bins as drive rises, with zero aliasing.
  - A per-voice modulator is phase-COHERENT across a multi-player voice — it pumps the whole "section", unlike
    the decorrelated per-player detune/vibrato/scatter. Brass `l` (`voices.rs:control_tick`) is per-VOICE, so
    folding a living-breath into it would tremolo the 5-player section 61 as one coherent unit (the "wobbly
    synthetic" tell). Gate liveness modulators to SOLO voices (`oversample && spec.players == 1`); leave sections
    alone. Model breath as APERIODIC value-noise (smoothstep between random targets), not a sine — a periodic LFO
    reads as a tremolo. Isolate a new DEFAULT-ON modulation axis from the ~16 existing static-timbre oracles by
    rendering them FROZEN (force the depth field to 0 in the shared `render_brass` helper), and give the axis its
    own DIFFERENTIAL oracle measuring the actual complaint — TIMBRE motion
    (`brass_sustain_breathes_off_the_frozen_hold`, a sliding-centroid p5–p95 wander), not the incidental level AM
    a tremolo also shows.

- 2026.07.15 — **A waveguide detunes FLAT with pitch if `set_freq` under-subtracts loop latency — set `loop_comp` by autocorrelation, not `sr/f−1`.**
  - The bowed loop's in-loop reflection filter + read/write add ~3.8 samples, not the hard-coded 1; the residual
    is a near-constant sample offset, so cents-flat scales with pitch (~50 cents flat by the cello's A4). It
    passed the pitch gate only because the contrabass's test keys topped at E4 (−36c).
  - **UPDATE 2026.07.13: the "inaudible in the contrabass's bass" dismissal was WRONG and cost months.** Measured
    over its OWN compass (E1–G3) the contrabass spreads −6c→−46c = 39.5c, and a pitch-DEPENDENT error corrupts
    INTERVALS (a fifth ~14c narrow → a sustained triad beats against itself) — worst on the bass, the harmonic
    foundation. Arthur heard it as "the alt bank sounds better" (the alt's offset is constant, hence inaudible).
    Fixed to 3.85 (the cello's value — same `refl_sustain`, same latency). The oracle asserts cents-SPREAD ≤ 5
    over each instrument's own compass, not a per-note floor. Never call a pitch error "inaudible" from a
    snapshot; measure the spread over the real compass.
  - A plucked-voice "no sustain" complaint is usually the note-off RELEASE (`rel_t60`), not the natural KS decay:
    album guitar parts are written as SHORT notes (~0.2–0.55 beat, gate < 1), so note-off lands in ~0.2 s and the
    amp release governs. The acoustics inherited `DEFAULTS.rel_t60 = 0.15 s`, a chop that kills the ring 0.3 s
    after note-off; an un-muted string is not damped at note-off, so give non-muted guitars a let-ring `rel_t60`
    (~1.1 s) and keep MUTED's fast chop. Bounded pile-up: no polyphony cap for acoustics, a voice reaps below
    2e-5. Isolated `render_pluck_phased` shows the full chop (−213 dB tail) but the real engine masks most of it
    via the guitar echo send (0.08) + CC91 reverb, so the in-mix win is a modest +4–9 dB — measure in the ENGINE.
  - A one-pole KS damper's MAGNITUDE at f0 (not `loop_gain`/`t60`) rules treble decay — STEEL B5:
    damp_mag(f0) ≈ 0.955/round-trip ≈ −390 dB/s, so the fundamental is dead in ~130 ms whatever the nominal t60.
    Naive `1/|H(f0)|` loop-gain compensation is DC-UNSTABLE (round-trip gain > 1 below f0, since |H(DC)|=1); hold
    a treble carrier with the band-limited saturating `SusDrv` sustainer instead. This is why a fast plucked
    tremolo machine-guns: not only the fresh-spawn re-attack but the inter-stroke release chop + the dead treble
    carrier. Fix = re-PICK the ringing string (voice reuse + stretched release + carrier hold + pick-catch +
    h1-floor). Oracle: f0-carrier p10/p90 — broadband/HF-fraction metrics are FOOLED, because the onset train
    dominates all bands and overlapping released twins fill gaps with hash that gross-envelope metrics credit as
    continuity. One comb-noise period's h1 is Rayleigh-random (20 dB stroke roulette) and additive re-injection
    phase-cancels, so a re-pick must catch (scale) the line and floor its own h1.
  - A held distorted-guitar note dies because the in-loop damper `bright` kills the harmonics that carry the RMS
    — raise `bright`, NOT `t60` (which clamps at pitch and only governs the fundamental); the tanh `amp` adds
    compression sustain for the fastest-decaying high notes.
  - The KS Pluck BASS already emits a strong pitch-TRACKING f0/2 SUBHARMONIC, so "add a sub-octave" is a solved
    problem. Measured dry/isolated/sustained: A2 f0/2 sits +5.7 dB OVER the fundamental, E2 +0.3, F#3 +11.7, and
    the peak TRACKS f0/2 (E2→42 Hz, A2→54 Hz), not the fixed ~50 Hz body peak. It is a LONE f0/2 line (no 1.5·f0),
    so it reads as sub-reinforcement, NOT a wrong-octave pitch. A fully-built sub-octave oscillator was shelved
    once this showed its premise ("~nothing at f0/2") was false — MEASURE what a voice already emits at f0/2
    before building a low-end feature. When a masking layer grows (BASS sub 0.28→0.72), a differential oracle for
    a small parallel feature drops BELOW the rng-realization noise floor — test the MECHANISM on a sub/kick-free
    clone, don't weaken the assertion.

- 2026.07.14 — **Rate jitter decorrelates the SAME take to NCC 0.07–0.19 — warp the rate, diff, then correlate** (`sampled_ride_hits_are_decorrelated`).
  - Plain correlation therefore waves a round-robin repeat straight through an anti-machine-gun oracle. Warp one
    hit over ratio candidates (±the spread of two jitter draws), anchor at the detected onset, and correlate FIRST
    DIFFERENCES — that tilts toward the take-specific HF sizzle and away from the low plate modes every take of
    one cymbal shares — over a window starting past the shared stick transient (30–70 ms). Measured on the
    drumkit ride: distinct takes 0.12–0.48, same take 0.70–0.86, clone 1.0 → a usable threshold at 0.60.
    Raw-waveform and onset-window variants had no margin (adjacent takes correlate 0.71).
  - Deep-velocity-layered libraries with NO round robins (Virtuosity snare 36 vl, toms 16 vl) still yield working
    RRs: fill each target layer's RR slots with ADJACENT source velocity layers. They are distinct recorded takes
    within ~10 velocity points, timbrally near-identical once the prep pipeline peak-normalizes (the synth applies
    velocity gain itself), so they cycle exactly like true RRs (fast-hat NCC ≤0.49 vs 1.0 clone). Where a source
    has no round robins at all, `RR2` = an adjacent VELOCITY layer + `trim_to_onset`'s peak-norm → same level,
    brighter-strike timbre = free variety with no machine-gun on repeats.
  - White rate jitter alone can never bound worst-pair correlation on fast repeated hits — some same-take pair
    always draws near-equal rates. Stratify the rate offsets by hit index, coprime with the round-robin count
    (hats: 5 vs 4).
  - Choke oracles: "choked window quieter than the open ring" FAILS when the choking articulation's own body
    outlasts the window (the pedal chick rings past 200 ms). Measure the RESIDUAL instead — choked-render energy
    minus choker-played-alone energy (`sampled_closed_or_pedal_hat_chokes_open_in_engine`).

- 2026.07.14 — **"Drums too far back" is INTERNAL KIT BALANCE, not bus level — −18 LUFS absorbs a flat lift; fix in `engine.rs:kit_balance`.**
  - The master normalizes to a fixed −18 LUFS and true-peak-limits to −1 dBTP, so a +6.8 dB drum probe moved the
    delivered master ~0.4 dB: the drums become the peak-driving element and the limiter clamps exactly the
    kick/snare transients you hear.
  - Diagnose per-FAMILY balance in a REAL track before reaching for bus tools: an env-gated per-key mute (keep
    only 42/44/46, or only 35/36/38/40) + integrated LUFS on the ch10 solo stem shows which family dominates. On
    a standard backbeat the hats measured 26 dB under the kick/snare (gone); on Hey Jude the crash sat 2 dB under
    (too loud).
  - Root cause: the sampled `sampler.rs:DRUM_LEVEL` table is calibrated to MATCH the modeled kit, so it faithfully
    inherited the model's hat-light/cymbal-heavy voicing. Fix as a per-key trim in the drum MIX
    (`engine.rs:kit_balance`), not in `DRUM_LEVEL` — it then scales the sampled and modeled kits equally and keeps
    their parity.
  - Beware the golden mix-balance fixture (re-pin ch10 only) and the stereo-imaging oracle (a hat-forward kit
    correlates more; give its test pattern a present ride so it still exercises the L/R spread).
