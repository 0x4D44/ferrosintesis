# ferrosintesis-samples-drumkit

Embedded CC0 sampled drum-kit bank for ferrosintesis: kick, snare, sidestick,
rack and floor toms, hi-hat closed/open/pedal, and ride
(bow and bell) — 128 mono 16-bit 44.1 kHz WAVs with velocity layers and round
robins, exposed as raw WAV bytes (`get`) and decoded PCM (`Bank::pcm`).

The accent cymbals — crash, splash and an 18" china — are in the
sibling `ferrosintesis-samples-drumkit2`, split out on 2026-07-25 to keep each
package under the crates.io 10 MiB limit. That was a packaging split, not a
musical one; renders are byte-identical across it.

Source: Virtuosity Drums, CC0 1.0 — the balanced `mid` mic set for every family
except the kick, which uses the `kickmic` close-mic set for its low end. See
`PROVENANCE.md` for the pinned revision, full inventory with SFZ-derived velocity
splits, and processing chain. The license text ships as `LICENSE-CC0`.

The WAVs under `samples/` are source, not build output; regenerate them with
`python3 tools/ferrosintesis-samples/prepare_drumkit.py` from the repo root.
