# ferrosintesis-samples-gong

Embedded pitched gong-ageng bank for ferrosintesis: two full-ring one-shot
layers (soft + loud), mono 16-bit 44.1 kHz WAVs, exposed as raw WAV bytes
(`get`). This is the sample source for the GM14 CC0=2 alt-bank pitched gong.

Unlike the other sample crates, this bank is **CC BY 3.0**, not CC0: the audio
is the Casa da Música / Digitópia "CdM Gamelan Sample Library" (Freesound user
`Digitopia_CdM`). The required attribution ships as `NOTICE` — it is
irrevocable and permits commercial use and redistribution, so it flows to every
downstream user while the ferrosintesis code stays MIT/Apache. See
`PROVENANCE.md` for the Freesound IDs, license verification, and the processing
chain.

The WAVs under `samples/` are source, not build output; regenerate them with
`python tools/ferrosintesis-samples/prepare.py --local-only` from the repo root
(reads the committed source WAVs under `tools/ferrosintesis-samples/gong-src/`;
no network needed).
