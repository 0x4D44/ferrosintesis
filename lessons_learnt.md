# Lessons learnt

Distilled, non-obvious gotchas for future sessions in this repo. **Cap: 20 entries.**

Format (`index-v1`): an entry's **first line is the whole lesson** — the surprise, the fix,
and a `file:symbol` pointer, in ONE plain-text line (≤~120 chars). The SessionStart hook
injects **only those first lines**, so each must stand alone; the indented lines beneath are
lookup detail and are never injected. Newest first. Durable project facts and conventions
belong in `CLAUDE.md`, not here.

<!-- lessons-format: index-v1 -->

- 2026.07.30 — **A one-case bar hides fitting; census every value it would flag** (`sampler.rs:best_cycle_correlation`).
  - The retired `baritone_sax_key58_avoids_a_rough_source_zone` asserted `> 0.996` on the
    single zone key 58 selects. Applying its own metric to all 20 baritone zones: the real
    defect was 0.779, but five HEALTHY shipping zones sat at 0.993–0.9960, below the bar.
    It separated "the zone we removed" from "the zone we kept", not rough from smooth, and
    passed only because one key happened to land above it (MM-BUG-KILN-00180).
  - Copy the fixed shape, `sampler.rs:baritone_sax_bank_rejects_the_rough_source_population_outlier`:
    census the whole runtime population, set the bar RELATIVE to it (`10 x median`), and
    keep both a positive control (must be flagged) and a negative one (must not be).
  - Check the bar lands in a real gap, both sides: worst healthy 0.00704 roughness, bar
    0.03105, real defect 0.22135. Then prove it — restoring the rough take must fail the
    oracle AND restoring the healthy one must pass it. The old bar failed that second test.

- 2026.07.29 — **Archive tests inherit ancestor Cargo config; unpack outside the repo** (`.cargo/config.toml:[build]`).
  - `cargo test --manifest-path target/package/...` still discovers the checkout's
    `.cargo/config.toml`, so it enables repository-only cfgs and is not a consumer test.
  - Copy or unpack the normalized crate under OS temp, outside the checkout, before
    claiming its registry test suite is self-contained.

- 2026.07.26 — **Equal f32 formulas can change bits; preserve original expressions** (`voices.rs:bow_force_ceiling`).
  - `2.9 - 2.2` is `0.70000005`, not literal `0.69999999`; likewise `0.36 + 0.82` and
    literal `1.18` differ by one f32 step.
  - A stick-slip waveguide amplifies that difference across every later sample. Keep the
    original expression, and use the mandated render diff to test claims of byte-inertness.

- 2026.07.26 — **Default tests miss alternate banks; test each selectable voice** (`sampler.rs:assert_attack_is_peak`).
  - The B1 upright swelled above its attack at CC0=5 while attack, gap-release and damper
    oracles all passed program 0. Promotion to the default slot finally exposed it.
  - Re-measure each alternate: raising LA make-up cured the swell but worsened the
    fast-repeat gap, leaving a narrow valid gain window around 1.2–1.3.

- 2026.07.23 — **Measure sample roots, formats and isolated onsets; never trust labels** (`prepare.py:trim_to_onset`).
  - Blind onset trimming needs about 30 dB of pre-onset quiet or it grabs the previous note.
    A self-cut bank can instead cut at the local envelope minimum and fade.
  - Harmonic templates confuse a fundamental with its subharmonic, and autocorrelation can
    choose 2f. Score harmonic coverage, keep a zone span below one octave, and name the
    destination from measured pitch rather than the source label.
  - Measure a sustained instrument over its ring, not its strike. Check WAV sample width and
    format first: 24-bit PCM read as 16-bit looks like flat noise, while IEEE-float WAV makes
    the stdlib `wave` reader fail with `unknown format: 3`.
  - Gate the character you need, not a proxy such as periodicity. Re-micing also cannot add
    low frequencies the instrument never produced.

- 2026.07.23 — **Fit LA gain to the oracle's worst register, not the bank mean** (`voices.rs:LA_EASTPICK`).
  - A mean crossfade-window fit gave 0.229, but the quieter top zones put keys 76/79 at
    0.78–0.80 against the treble oracle's 0.8 floor.
  - Use `print_steel_wrap_level_ratios`, fit the binding register, and re-check the global
    ceiling. The measured gains became 0.26 picked and 0.242 plucked.

- 2026.07.23 — **Metrics need the changed band; crossings and sparse centroids lie** (`testutil.rs:spectral_centroid`).
  - A 200 Hz analysis floor hid changes at 90–120 Hz. Confirm the A/B is not byte-identical,
    include the changed band, and score against a control render rather than an absolute bound.
  - Signed band ratios can reverse across adjacent keys. Use a direction-free multiband
    distance across the register and measure the time span listeners actually hear.
  - Zero crossings follow leaked harmonics; use `peak_locate` for stable tones. Fixed Goertzel
    bins miss vibrato sidebands, and FM carriers with beta above about 0.5 need known-pitch
    measurement rather than peak selection.
  - `testutil::centroid` uses sparse log bins and is leakage-dominated. Use the Hann-windowed
    exact-DFT `spectral_centroid`, with a flat envelope or a settled window.
  - Noise biases brightness upward. Match or subtract noise floors; remember uniform
    `Rng::white()` has RMS `1/sqrt(3)`, and compare spectral-windowed values only with other
    spectral-windowed values.
  - Single-harmonic ratios and cross-instrument spreads are register traps. Sweep several
    matched-pitch keys and the feature's live window.
  - `--solo` stems are independently peak-normalized. Undo the reported peak scale before
    comparing level; in reference MIDIs, use CC120 to stop voices and zero CC91/93/94 after
    every program change.

- 2026.07.21 — **Disable master BusGlue before level calibration; it compresses the probe** (`engine.rs:BusGlue`).
  - BusGlue is unconditional, compresses 2:1 above 0.32, and adds a 1.5 dB shelf at 95 Hz.
    Use a throwaway build that bypasses it; clearing `PROGRAM_TRIM_DB` is insufficient.
  - Use early-window RMS for decaying voices and whole-note RMS for sustained voices.
    Instantaneous peak is too sensitive to transients.

- 2026.07.20 — **MIDI-file SysEx is `F0 <vlq len> <payload>`, not wire bytes** (`engine.py:write_midi`).
  - Writing raw `F0 7E 7F 09 01 F7` makes a parser treat `0x7E` as a 126-byte length and
    swallow the track, producing silence.
  - If ferrosintesis and both hardware references all go quiet, inspect the MIDI generator
    before blaming three engines at once.

- 2026.07.20 — **Score loops by continuation + balance; seam value+slope favors bad windows** (`prepare.py:find_loop`).
  - Value and slope at one sample pair provide only two constraints, so rich tones offer many
    false matches. Compare the wrap with the source's real continuation and test with a
    harmonically rich signal.
  - Keep loops short and penalize first-half/second-half RMS imbalance. A clean seam can still
    contain a decay ramp that pulses at the repeat rate.
  - Soundfont loop points may outlive decoded SF3 audio because Ogg priming drops trailing
    frames. Carve an integer-period loop from the steady body and crossfade its wrap.
  - Folded-novelty z-scores saturate on periodic signals. Compare the true lag with explicit
    decoy lags such as `0.73x`, `1.37x`, and `1.91x`.

- 2026.07.19 — **Calibrate oracles on old code and measured inputs, not the proposed fix** (`prepare.py:trim_to_onset`).
  - A fade test used 8–300 ms lead-ins while real banks start as early as three samples.
    Regenerate and diff the committed sample bank before calling a `prepare.py` change inert.
  - Shared constants can become wrong as new material arrives. Re-measure them against the
    current source population.
  - Unauthored controller defaults still apply. Compare against a render that explicitly
    authors the retired value, and pin the corrected ratio rather than a guessed constant.
  - Drive time-varying timbre from an internal sample counter; unit renders may never call
    `retune`, so retune-driven motion vanishes in the oracle.
  - Re-voicing a common GM program can invalidate tests that use it as a live control. Move
    the control to the intended reference and recalibrate in the same change.
  - A full-suite failure may reveal a test-pinned design choice, not collateral damage.
    Escalate unverifiable ear judgments instead of overriding the oracle.

- 2026.07.16 — **Memoryless shaping keeps white noise flat; low-pass turbulence below f0** (`voices.rs:RD_RASP_NLP_F0`).
  - Shifting and summing a flat spectrum stays flat. Low-pass turbulence before the shaper;
    RD10 uses `0.30 * f0`.
  - For an additive voice, redraw harmonic amplitudes instead of waveshaping a summed chord;
    the latter adds aliasing and inter-note modulation without creating non-harmonic skirts.
  - For brass cuivré, split drive across two knees and derate high notes. Pin ADAA with a math
    oracle, then use the voice-level alias guard for real material.
  - Broadband texture contaminates off-lattice alias metrics. Measure it separately, and make
    alias limits absolute rather than drive-differential.
  - A per-voice modulator moves every player coherently. Limit liveness modulation to solo
    voices and use aperiodic value noise rather than a tremolo-like sine.
