# Provenance — ferrosintesis-samples-ccby

Two real recordings from Freesound, each **CC BY 4.0** (per-sound license confirmed in each
pack's bundled `_readme_and_license.txt` — all sounds "Attribution 4.0", no exceptions):

| GM | Instrument | Source | Author | Pack |
|----|-----------|--------|--------|------|
| 4 | Electric piano (Rhodes tine) | "C_S Fender Rhodes Mark II" | tim.kahn | Freesound **3957** |
| 15 | Hammered dulcimer | "Multi-sampled Hammered Dulcimer" | iternetcone | Freesound **19445** |

**Freesound gates downloads behind a login**, so these cannot be auto-fetched. The decoded +
trimmed source notes are committed under `tools/ferrosintesis-samples/freesound-src/` (the
same "committed source" pattern as `gong-src/`), and `prepare.py --only=rhodes,dulcimer,musicbox`
bakes onsets from them (trim to onset, measure root near the note label, mono 16-bit 44.1 kHz).

To fully regenerate from scratch: download packs 3957 (Rhodes) + 19445 (dulcimer) from
Freesound (login required), re-decode/trim the chosen notes into `freesound-src/`, then run
`prepare.py`. The `jRhodes` set was rejected — its sample bytes are CC-BY-**NC** (see the
round-3 voice-quality HLD); tim.kahn's pack is plain CC-BY and safe for a published crate.
