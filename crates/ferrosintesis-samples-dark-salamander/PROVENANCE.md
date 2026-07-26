# Provenance — ferrosintesis-samples-dark-salamander

## Packaged family inventory

| Family | Files |
|--------|------:|
| `darkgrand_*` | 54 |

A **warmer voicing of the Salamander grand** for a **GM 0 Acoustic Grand
alternate** (bank select CC0=5): 54 mono 16-bit 44.1 kHz WAVs, the same 9 pitch zones
(C2–C6) × 3 dynamics × 2 round robins as `ferrosintesis-samples-grand`, with a
high-shelf EQ cut applied to darken the bright top end. The WAVs under `samples/`
are **source, not build output** — committed and embedded via `include_bytes!`.

## Why this bank exists

The Salamander C5 grand (CC0=2) is bright, which the maintainer finds too
bright. This bank isolates the question: *is the dislike fixable by EQ, or does
it need a different instrument?* It is the same recording, warmed — so in the
audition it A/Bs directly as CC0=2 (raw Salamander) versus CC0=5 (this bank).
If it sounds acceptably
warm, the cheapest fix is EQ, not a new sample set. (This is the reproducible,
shippable stand-in for the Noct-Salamander remaster, which is distributed only via
a fragile 1.6 GB Google-Drive file.)

## Source & processing

Derived deterministically from the committed `ferrosintesis-samples-grand` WAVs
(themselves the Salamander Grand Piano V3, CC BY 3.0). Per file, `prepare.py`
(`_bake_darkened_grand`) applies a one-pole **high-shelf cut**
(`y = x - g·(x − lowpass(x))`, shelf ≈ 2 kHz, cut ≈ −6 dB — both EAR-TUNABLE
constants), then peak-normalizes to 0.9. Roots are unchanged from the grand (EQ
does not move pitch) and re-measured for the `darkgrand_*` zone tables in
`crates/ferrosintesis/src/sampler.rs`.

Licence: **CC BY 3.0**, inherited from Salamander — attribution in `NOTICE`
(Alexander Holm + a "modified: EQ" note).

## Regenerating

```
python tools/ferrosintesis-samples/prepare.py --only=darkgrand
```

No network — reads the tracked grand crate samples. Pure stdlib.
