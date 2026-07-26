# Provenance - ferrosintesis-samples-core

Every WAV this crate packages, with the pinned source it was baked from. Machine-checked
by `crates/ferrosintesis/src/inventory.rs`: a family that ships without a row here fails
the build (MM-BUG-KILN-00069).

Regenerate with `python tools/ferrosintesis-samples/prepare.py --only=piano,violin,flute` from the repository
root.

| Family | Files | Instrument | Source | Licence |
|--------|------:|------------|--------|---------|
| `piano_*` | 52 | Upright piano (GM 0 Acoustic Grand alternate, CC0=1) onsets, 3 velocity tiers; 25 cells have 2 round robins, quiet C2/G2 are single-take | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `violin_*` | 12 | Solo violin (GM 40) arco onsets, p/f layers | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `flute_*` | 5 | Flute (GM 73) sustain onsets | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |

All three families come from the same CC0 source and revision pin; the split into
`-core` exists only to keep this crate under the crates.io 10 MiB limit, not because the
provenance differs.
