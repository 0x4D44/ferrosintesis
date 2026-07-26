# MM-BUG-KILN-00036 — GM21 Accordion is a sparse 12-sine additive stack: reads thin/synthetic AND perceptually quiet

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
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the M-CAL
  instrument-audition review; timbre defect confirmed by Fable 5 + Codex gpt-5.6-sol
  cross-agent reconciliation) → Blocked (2026-07-25, GPT-5.6 Codex on KILN-Windows — current trunk still has the measured sparse additive voice, but Arthur must choose a modeled-reed target or approve a sourced LA accordion layer before an audible fix has a correctness target) → Open (2026-07-26, unblocked by Arthur after focused free-reed synthesis research; approved a modeled French-musette source-filter voice rather than a sampled layer)

## Observation

In the neutral reference audition, GM21 (Accordion, musette) sounds **very quiet AND
"wrong sound"** to the ear, yet the max-momentary level metric reads it as roughly
matched to the SC-55. Both symptoms have one cause.

## Root cause

`organ()` case 21 (`crates/ferrosintesis/src/voices.rs:5644`) builds the accordion as a
**static 12-sine additive stack** — fundamental + detuned (±16 c) reed pairs on h1–h4,
harmonics falling 2.0→0.24 … 4.0→0.05 — plus only a token `.with_reed_noise(0.018, …)`.
There is no broadband reed buzz and no sampled body. The thin pure-sine spectrum excites
few critical bands, so it (a) reads quiet perceptually despite equal K-weighted energy
(few bands summed) and (b) sounds synthetic next to the SC-55's spectrally-rich sampled
accordion. A level trim cannot fix "wrong sound".

## Fix direction

Add spectral richness: a broadband reed buzz (noise-excited reed model) or more partials
with per-partial jitter, or an LA accordion onset/body sample layer. Related: closed bug
MM-BUG-KILN-00006 (no class-identity timbre oracle) — a Passport-style oracle would pin it.

### Blocker — 2026-07-25

Blocking owner: **Arthur**. Current trunk still matches the diagnosis:
`organ(21)` is twelve sine entries plus `with_reed_noise(0.018, ...)`. The later
musette work made H2–H4 beat correctly, but did not add the broadband body this
audition found missing.

Unblock when Arthur chooses one of these audible product targets:

1. **Modeled accordion:** authorize a noise-excited reed/broadband buzz and
   per-partial instability pass, with an A/B target of “spectrally rich French
   musette, clearly fuller than GM23 bandoneon without becoming an organ”.
2. **LA accordion:** provide an owner recording or approve a CC0/CC-BY source
   and its retained provenance, plus the intended onset/body crossfade policy.

After either choice, the Build must add a class-identity oracle for broadband
reed energy, retain the existing per-harmonic musette and drier-bandoneon
oracles, remeasure perceived level after the timbre change, and run the full
catalog render-diff required for `voices.rs` changes. Picking either synthesis
or sampling unattended would invent both the timbre contract and asset scope.

### Prior art and accepted implementation direction — 2026-07-26

Arthur approved the **modeled accordion** route. Focused research narrows that choice:
do not try to repair the voice merely by turning up white noise or adding arbitrary
sines.

- Puranik and Scavone's real-time harmonium work uses a **source-filter** architecture.
  Their perceptually simplified source is a band-limited periodic waveform populated
  from the first 37 spectral peaks of a physical reed model. They found the enclosure
  filter affected perceived timbre more strongly than the exact physical source, and
  approximated its 8–9 prominent response peaks with second-order sections:
  [DAFx 2023 paper and abstract](https://dafx.de/paper-archive/details/YpJGemANSDbyjvvVLMb4rg).
- Their preceding physical-model study shows why a sine stack is insufficient: free-reed
  airflow has a sharp within-period transition as the reed crosses its plate, producing
  a dense harmonic source, while the wooden enclosure supplies the recognisable spectral
  envelope. Bellows pressure primarily changes amplitude and only slightly shifts pitch:
  [Physical modelling synthesis of a harmonium](https://caml.music.mcgill.ca/lib/exe/fetch.php?media=publications%3Apuranik_harmonium_poma_2022.pdf).
- Ricot, Caussé and Misdariis model the accordion reed as a blown-closed free reed whose
  self-oscillation does not require bore coupling; its radiated sound is dominated by
  momentum fluctuations through the reed gap. This supports a nonlinear-looking
  band-limited reed waveform, not an organ-like set of isolated sine partials:
  [JASA 2005 abstract](https://pubmed.ncbi.nlm.nih.gov/15898668/).
- Experimental transient work finds that the steady fundamental bending mode is joined
  by higher transverse and torsional modes during the attack, especially early in the
  oscillation. Those modes should be short attack colour, not permanent broadband hiss:
  [ICA 2019 survey](https://pub.dega-akustik.de/ICA2019/data/articles/001430.pdf).

Implement the smallest real-time source-filter approximation consistent with that
evidence:

1. Preserve GM21's existing three-reed French-musette registration and ±16-cent
   per-harmonic beating. Replace each reed's four-sine steady source with an antialiased,
   band-limited reed waveform carrying a smooth upper-harmonic tail (up to the
   sample-rate-safe limit, with roughly the first 24–37 harmonics available on low
   notes). A generated wavetable or equivalent compact oscillator is preferable to
   dozens of per-voice `Sine` objects.
2. Add a compact body/enclosure filter after the combined reeds. Use a small cascade of
   broad, stable resonant sections that captures several prominent spectral regions
   without cloning the cathedral-organ resonator or adding a dependency. Keep its
   response bounded and smoothly register-aware so high notes cannot become piercing.
3. Retain a modest, velocity-responsive band-limited air/reed residual, but do not use
   noise as the steady timbre's main source. Add short, seeded-deterministic upper-mode
   attack colour that decays out before the steady musette body.
4. Allow only subtle seeded per-reed amplitude/pitch movement around the existing fixed
   tuning. Preserve pitch-bend and controller path independence; do not add uncommanded
   large pitch wander.
5. Leave GM23 bandoneon and GM20 reed organ structurally unchanged. GM21 must remain the
   wider, fuller French musette, while GM23 remains the dry comparison voice.
6. Recalibrate GM21's output level only after its spectrum and body filter are correct.
   Do not use a trim to conceal an under-populated spectrum.

The autonomous fix must provide focused regression evidence:

- A steady-state harmonic-occupancy oracle proves substantial H5–H12 energy on
  representative low/mid keys and proves the antialias limit removes unsafe partials on
  high keys.
- A source-filter oracle proves the body stage materially reshapes several spectral
  regions rather than acting as a scalar.
- An attack-versus-sustain oracle proves the higher-mode colour is stronger during the
  initial transient and decays out of the held tone.
- Existing `accordion_musette_beats_across_harmonics` and
  `bandoneon_is_drier_than_accordion` tests remain green, augmented by a spectral
  fullness comparison showing GM21 is broader than GM23 without collapsing onto an
  organ.
- Re-run the M-CAL GM21 probe and perceived-level comparison after timbre work, plus the
  repository's required catalog render-diff for `voices.rs`.

No sample asset, licence change or new dependency is approved. Leave the bug **Fixed**,
not Closed, after implementation so an independent verifier can inspect the automated
evidence and audition representative low/mid/high GM21 notes.

## Note

The M-CAL derivation report and the audition markers labelled this slot "Percussive Organ"
in places — GM21 is **Accordion**; GM17 is Percussive Organ. Correct the label where it
appears.
