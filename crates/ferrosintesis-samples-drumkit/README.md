# ferrosintesis-samples-drumkit

Embedded CC0 sampled-cymbal drum-kit bank for ferrosintesis: ride (bow and
bell), crash, sizzle crash, hi-hat closed/open/pedal/splash, and an 18" china
— 109 mono 16-bit 44.1 kHz WAVs with velocity layers and round robins, exposed
as raw WAV bytes (`get`) and decoded PCM (`Bank::pcm`).

Sources: Virtuosity Drums (`mid` mic set) and Karoryfer Big Rusty Drums (the
china), both CC0 1.0 — see `PROVENANCE.md` for the pinned revisions, the full
inventory with SFZ-derived velocity splits, and the processing chain. The
license text ships as `LICENSE-CC0`.

The WAVs under `samples/` are source, not build output; regenerate them with
`python tools/ferrosintesis-samples/prepare_drumkit.py` from the repo root.
