# Provenance - ferrosintesis-samples-orchestral

Every WAV this crate packages, with the pinned source it was baked from. Machine-checked
by `crates/ferrosintesis/src/inventory.rs`: a family that ships without a row here fails
the build (MM-BUG-KILN-00069).

Regenerate with `python3 tools/ferrosintesis-samples/prepare.py --only=<family>` from the repository
root.

| Family | Files | Instrument | Source | Licence |
|--------|------:|------------|--------|---------|
| `bassoon_*` | 12 | Bassoon (GM 70) sustains | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `celens_*` | 12 | Cello section (GM 42 ensemble) sustains | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `chanter_*` | 15 | Bagpipe chanter (GM 109) loops | FreePats Bagpipe-SFZ-20221204 archive, SHA-256 pinned in `prepare.py` | CC0-1.0 |
| `clarinet_*` | 12 | Clarinet (GM 71) long sustains | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `drone_*` | 2 | Bagpipe drones (GM 109), G2 + G3 | FreePats Bagpipe-SFZ-20221204 archive, SHA-256 pinned in `prepare.py` | CC0-1.0 |
| `harpsi_*` | 10 | Harpsichord (GM 6) onsets | VCSL (Versilian Community Sample Library), pinned `c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e` | CC0-1.0 |
| `horn_*` | 12 | French horn (GM 60) sustains | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `mutetpt_*` | 10 | Muted trumpet (GM 59) sustains | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `nylon_*` | 7 | Nylon guitar (GM 24) onsets | FreePats SpanishClassicalGuitar-SFZ-20190618 archive, SHA-256 pinned in `prepare.py` | CC0-1.0 |
| `oboe_*` | 12 | Oboe (GM 68) sustains | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `steel_*` | 8 | Steel-string guitar (GM 25) onsets, Martin GM2 | sfzinstruments/Discord-SFZ-GM-Bank, REV pinned in `prepare.py` | CC0-1.0 |
| `trombone_*` | 12 | Tenor trombone (GM 57) sustains | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `trumpet_*` | 10 | Trumpet (GM 56) sustains | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `tuba_*` | 12 | Tuba (GM 58) sustains | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `vlnens_*` | 12 | Violin section (GM 48 ensemble) sustains | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |

Every source above is CC0, so no attribution is legally required; this file exists so a
consumer can trace what they received and reproduce it. The exact per-file URLs live in
the corresponding `*_URLS` / `*_SOURCES` tables in
`tools/ferrosintesis-samples/prepare.py`, all pinned by revision or archive SHA-256.

## Removed from this package

`drum_*` — eight percussion hits (crash cymbal, suspended cymbal, kick, snare; two
round robins each), also trimmed from **VSCO 2 Community Edition** (Versilian Studios /
sgossner, <https://github.com/sgossner/VSCO-2-CE>) at pinned commit
`440300901dfe9275fd84e0b7763af1f8443ae62e`, released under **CC0-1.0**.

They shipped here until 2026-07-26. The sampled kit in `ferrosintesis-samples-drumkit`
superseded them and no `ferrosintesis` code ever read them, so ~919 KiB of
`include_bytes!` payload was being compiled into every binary and published in this
package for nothing. The WAVs were **not deleted** — they moved to
`tools/ferrosintesis-samples/retired-drum-overlays/` in the repository, outside any
published crate, because `drum_crash1_ff_rr1.wav` is the real-cymbal measurement
reference the shipped MetalPlate cymbal model was calibrated against. That directory's
`README.md` records the detail.
