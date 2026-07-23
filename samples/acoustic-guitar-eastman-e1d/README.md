# Eastman E1D steel-string acoustic — first-party source recordings

Two performance masters of Arthur's own **Eastman E1D** dreadnought steel-string
acoustic guitar, recorded 2026-07-23. They are the source for the default (and one
alternate) GM 25 steel-string banks in ferrosintesis — replacing the fetched Martin
HD28 bank as the default, which moves to a bank-select alternate.

- **`picked.opus`** — plectrum articulation (bright attack). Source `DR0000_0192.wav`.
  → baked into the **default** GM 25 bank (`eastman_picked`).
- **`plucked.opus`** — fingerstyle / hand-plucked (warm, ~4–5× darker centroid).
  Source `DR0000_0191.wav`. → baked into the CC0=1 **alternate** bank (`eastman_plucked`).

## Recording

| | |
|---|---|
| Instrument | Eastman E1D dreadnought, steel strings |
| Performer | Arthur |
| Master format | 44.1 kHz · 16-bit · **stereo, coincident pair** (inter-channel delay ~0.08 ms — mono-sums with −0.1…−0.3 dB, no comb filtering) |
| Content | chromatic walk up the neck, **E2 → ~C6**, ~80 discrete notes per take |
| Quality | no clipping; peak −4.6 dBFS (plucked) / −6.6 dBFS (picked); noise floor ~−66 dBFS |
| Tuning | ~+10…+30 cents sharp overall — irrelevant to the render: the sampler repitches from each zone's **measured** f0 |
| Licence | **CC0-1.0** (public-domain dedication by the repo owner) |

Kept as Opus (160 kbps, music mode) to save ~9× on the git tree; the full
performances are preserved uncut (the takes are wall-to-wall, with note tails ringing
5–7 s into the following gaps, so there is no dead air to trim without damaging
decays). The 44.1 kHz/16-bit lossless originals are Arthur's authoritative masters;
these Opus copies are the in-repo archive and the re-slice source.

## Zone slice map (approximate anchor times, seconds into each take)

The bank keeps the Martin/nylon layout — 8 zones at ~6-semitone spacing, E2–B5 — one
onset (~0.9 s) per zone; the Karplus-Strong model carries the decay. `prepare.py`
slices a generous window around each anchor and `trim_to_onset` finds the exact onset,
so these times only need to bracket the right note. Final pinned windows live in
`tools/ferrosintesis-samples/prepare.py`.

| Zone | `picked.opus` (0192) | `plucked.opus` (0191) |
|------|----------------------|-----------------------|
| E2   | ~1.7 s   | ~5.7 s   |
| A#2  | ~39.3 s  | ~64.1 s  |
| E3   | ~85.0 s  | ~102.8 s |
| A#3  | ~132.2 s | ~143.8 s |
| E4   | ~180.4 s | ~189.4 s |
| B4   | ~215.9 s | ~282.0 s |
| F5   | ~244.1 s | ~254.1 s |
| B5   | ~276.2 s | ~277.4 s |

The top zones (F5, B5) ring shorter and quieter — expected acoustic-guitar physics,
and the same situation the Martin bank already lives with (its `steel_B5` is 0.706 s,
the binding case of the `guitar_zone_fade_budget` oracle).
