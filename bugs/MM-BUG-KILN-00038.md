# MM-BUG-KILN-00038 — GM61 Brass Section has no LA sample layer (pure 5-player waveshaper) and reads synthetic

- **State:** Open
- **Priority:** Could
- **Severity:** Medium
- **Area:** synth
- **Raised:** 2026-07-21
- **Owner:** -
- **Owner role:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner fingerprint:** -
- **Owner since:** -
- **Owner until:** -
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=1, indeterminate=0
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the M-CAL instrument-audition review; "quiet synthetic" — Arthur's ear, code-confirmed) → Blocked (2026-07-25, GPT-5.6 Codex on KILN-Windows — trunk deliberately keeps GM61 model-only because the old sample was a wrong solo trumpet and no licensed brass-section onset exists; Arthur must approve a source or a modeled-section target) → Open (2026-07-26, Arthur approved a modeled heterogeneous natural-brass section after focused brass-synthesis research) → Fixed (2026-07-27, deltic:auto role=fix run=fix-20260727T005703Z-p9812-n849374900-c34 branch=task/bug-MM-BUG-KILN-00038-run-fix-20260727T005703Z-p9812-n849374900-c34 code=08cb7f6ad9c7dfa8407dff5589d36bba647c00d5 gate=cargo model=codex@xhigh) → Open (2026-07-27, deltic:auto role=verify run=verify-20260727T182402Z-p9812-n426934100-c111 verified_fix_run=fix-20260727T005703Z-p9812-n849374900-c34 verdict=doubt reason=engineering-evidence-is-fully-green-and-the-fix-plausibly-addresses-the-root-cau model=claude)

## Observation

GM61 (Brass Section) sounds "quiet synthetic" next to the SC-55's sampled brass. Its LEVEL
is roughly right (M-CAL residual −1.15 dB); the complaint is timbre.

## Root cause

`BR_SECTION` (`crates/ferrosintesis/src/voices.rs:10091`) is a **pure model** — 5 waveshaped
`brass_valve` players with **no LA sample layer**. The dispatch `61..=63 => Box::new(brass(...))`
(`voices.rs:12340`) has no `LaVoice` wrap, and the prior solo-trumpet sample layer was
deliberately dropped (comment `voices.rs:10094`). A 5-player detuned-waveshaper section reads
synthetic against sampled brass.

## Fix direction

Add an LA brass onset/body sample layer for the section (as the solo brass once had), or
enrich per-player spectral variance (breath noise, per-player formant jitter). Level trim
is not the lever. Related: MM-BUG-KILN-00018 (closed) fixed the natural-brass h2–h5 low-mid
formant ring; the section-specific "no sample layer" synthetic quality is separate.

### Blocker — 2026-07-25

Blocking owner: **Arthur**. Current trunk confirms the diagnosis and the
intentional boundary: GM61 remains a five-player model, while its former LA
layer was removed because it replayed a solo trumpet and no CC0 brass-section
sample exists. Restoring that asset would reintroduce the wrong instrument.

Unblock with one of these concrete inputs:

1. **LA section:** provide an owner recording or approve a CC0/CC-BY
   multi-player brass-section source, with retained provenance and the intended
   onset/body crossfade.
2. **Modeled section:** authorize a per-player spectral-variance pass and state
   the listening target—breath/formant diversity that reads as a section while
   remaining distinct from solo GM56–60 and synth brass GM62/63.

Either route changes audible voicing. The Build must add a section-identity
oracle, preserve the existing brass-family controls, and run the full catalog
render-diff required for `voices.rs`/`sampler.rs` changes. Selecting an asset
source or voicing character unattended would guess at both product and
licensing decisions.

### Decision and researched implementation contract — 2026-07-26

Arthur selected the **modeled-section** route. Do not search for or add a
sample layer for this fix.

Relevant prior art:

- Harrison, Bilbao, and Perry split a valved-brass physical model into an
  excitation mechanism, bore/valve resonator, and bell radiation model:
  <https://www.research.ed.ac.uk/files/21857362/DAFx_15_harrison.pdf>.
- Smith's economical digital-waveguide summary uses the same mouthpiece,
  bore, and bell decomposition, and notes that high-level bore nonlinearity is
  part of natural brass behaviour:
  <https://www.dsprelated.com/freebooks/pasp/Brasses.html>.
- D'haes and Rodet show that even a simplified trumpet model couples a
  resonating lip valve to the instrument body's reflection response, under
  physically constrained controls:
  <https://dafx.de/papers/DAFX02_DHaes_Rodet_trumpet_model.pdf>.
- Norman et al. found that players can change brassiness through embouchure at
  similar loudness, while nonlinear propagation creates the resulting
  high-harmonic enrichment:
  <https://doi.org/10.3813/AAA.918316>.
- Myers et al. relate spectral enrichment to bore profile and absolute bore
  size, so player-to-player timbral identity should not be represented by
  pitch scatter alone:
  <https://pubmed.ncbi.nlm.nih.gov/22280689/>.

Apply those principles at the current model's scale:

1. Retain the five modeled players, seeded determinism, onset scatter, and
   modest detuning. Those already create timing and pitch spread; increasing
   them is not the primary fix.
2. Give every player a stable, seed-derived identity across all three physical
   stages: lip/exciter resonance, damping and nonlinear brightness;
   bore/formant centre and gain; and bell/radiation cutoff. Bound the spread so
   the result remains one natural brass section, with a balanced mixture of
   brighter, middle, and warmer players rather than five clones.
3. Drive each player from the shared musical controls, but give it a subtly
   different pressure/attack response and independent breath variation.
   Never use one shared amplitude modulator, which would make the section pump
   coherently.
4. Preserve velocity/expression-driven nonlinear spectral enrichment. Do not
   replace brassiness with static EQ, broadband noise, or chorus.
5. Keep GM56–60 solo brass and GM62/63 synth brass behaviour unchanged. Add no
   sample asset or dependency.
6. Recalibrate output level only after the timbre is correct; the existing
   −1.15 dB M-CAL residual does not justify a gain-first fix.

The regression oracle must prove:

- isolated same-note players have distinct exciter/resonator/radiator
  parameters and are not near-identical waveforms;
- the complete section occupies a broader, stable spectrum than any one
  player without relying on excessive detune;
- higher velocity/expression increases high-harmonic energy while pitch and
  level remain controlled;
- existing section onset-spread and seeded-determinism tests remain green;
- GM61 remains measurably distinct from natural solo brass and synth-brass
  programs, with no NaN, aliasing, or material render-cost regression.

After the focused oracle passes, run the required full catalog render diff and
audition low, middle, and high GM61 notes. Land the fix as **Fixed**, not
Closed, for independent listening verification.

## Fix

### Fix summary (2026-07-27, deltic:auto run=fix-20260727T005703Z-p9812-n849374900-c34 code=08cb7f6ad9c7dfa8407dff5589d36bba647c00d5 gate=cargo)

GM61 remains a five-player, sample-free modeled section. Each player now carries
a seed-rotated identity through the lip/exciter cutoff and nonlinear drive,
bore/formant centres and gains, bell/output radiation, pressure response, and
independent filtered breath before the players are summed. The fixed identity
set contains balanced warm, neutral, and bright players; the seed changes their
seat assignment without changing the section's overall population.

The first candidate leaked GM61's 0.24×sample-rate source-filter clamp into
GM62/63 synth brass. The final constructor and render paths explicitly contain
the identity work to GM61. Fresh release renders of GM56–60 and GM62/63 are
byte-identical to trunk; GM61 alone changes. No sample asset, dependency, level
trim, or version change was added.

The strengthened regression removes detune, onset scatter, vibrato, drift, and
both shared and per-player breath before isolating each player. The five
steady-state spectral profiles span 1.525× in upper/body energy, 3.793× in
bell/body energy, and 1.388× in centroid. Every pair remains distinct. Their
combined identity envelope spans 889.0 Hz while the largest within-player
centroid drift is 0.1 Hz. The identity set is invariant across seeds, while the
existing onset-scatter and same-seed determinism oracle remains green. The
velocity/expression, pitch, finite-output, solo/synth distance, and detune-cap
guards also pass.

The optimized direct render-cost oracle compares the final per-player path with
the same five-player preset on the previous shared-filter path. It measured
6.573 s versus 6.568 s (1.001×), within the 1.25× ceiling. The 12-note M-CAL v3
probe measured raw integrated loudness of −40.58 LUFS versus trunk's −41.13
LUFS, a +0.55 LU change. Applied to the certified −1.15 dB residual, the
candidate is approximately −0.60 dB from target, so the existing `amp` remains
correct. Raw peak is 0.0615, below the 0.30 glue ceiling.

Focused validation:

- `cargo fmt --all -- --check`
- `cargo test -p ferrosintesis brass_o -- --nocapture` — 20 passed, one manual
  performance oracle ignored
- `cargo test -p ferrosintesis brass_section_61_skips_sample_layer -- --nocapture`
- `cargo test -p ferrosintesis brass_living_breath_scope_and_inertness -- --nocapture`
- `cargo test --release -p ferrosintesis brass_o18_render_cost_budget -- --ignored --nocapture`
- `cargo clippy -p ferrosintesis --all-targets -- -D warnings`
- `cargo clippy -p ferrosintesis --all-targets --no-default-features -- -D warnings`
- release no-sample renders of GM56–60 and GM62/63 — SHA-256-identical to
  trunk; GM61 changed

Fresh final release binaries produced complete 11,025 Hz render inventories.
Twenty-five of 124 album MIDIs and four of 17 demos changed, all because they
use GM61. The other 112 tracks stayed byte-identical. Both inventories report
zero contamination and zero not-reached tracks.

Independent low/mid/high and M-CAL listening evidence is under
`C:\Users\marti\AppData\Local\Temp\MM-BUG-KILN-00038-candidate`. It contains
raw and level-matched trunk/candidate WAVs plus the exact MIDI and plan files.

### Verification summary (2026-07-27, deltic:auto run=verify-20260727T182402Z-p9812-n426934100-c111 verified_fix_run=fix-20260727T005703Z-p9812-n849374900-c34 verdict=doubt)

Verifier note: Engineering evidence is fully green and the fix plausibly addresses the root cause, but the original observation is an audible timbre judgement I cannot reproduce on an earless box, and the ledger's own Arthur-approved contract says to land as Fixed 'for independent listening verification' - so closing now would bypass that gate. — Ledger: bugs/MM-BUG-KILN-00038.md; fix commits 829c63f..08cb7f6 touch only crates/ferrosintesis/src/voices.rs (+ledger). (1) Recorded code-confirmed root cause was 'BR_SECTION is a pure model - 5 waveshaped brass_valve players' with no per-player variance; that cond...
