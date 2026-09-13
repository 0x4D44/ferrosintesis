# Provenance - ferrosintesis-samples-core

Every recording this crate packages, with the pinned source it was baked from. Machine-checked
by `crates/ferrosintesis/src/inventory.rs`: a family that ships without a row here fails
the build (MM-BUG-KILN-00069).

From the repository root, regenerate the complete packaged inventory with:

```sh
python3 tools/ferrosintesis-samples/prepare.py --only=piano,violin,flute
python3 tools/ferrosintesis-samples/regen_samples_table.py crates/ferrosintesis-samples-core
cargo test -p ferrosintesis-samples-core
```

The first command publishes the 69 FLAC files. The second refreshes `FILE_COUNT`,
`SAMPLES`, and `EXPECTED_BYTES` while preserving the custom aliases and
`PIANO_SINGLE_TAKE_CELLS` API. Do not use `gen_crate_lib.py` for this crate: it
generates a whole `lib.rs` and would remove those handwritten extensions.

| Family | Files | Instrument | Source | Licence |
|--------|------:|------------|--------|---------|
| `piano_*` | 52 | Upright piano (GM 0 Acoustic Grand alternate, CC0=1) onsets, 3 velocity tiers; 25 cells have 2 round robins, quiet C2/G2 are single-take | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `violin_*` | 12 | Solo violin (GM 40) arco onsets, p/f layers | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `flute_*` | 5 | Flute (GM 73) sustain onsets | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |

All three families come from the same CC0 source and revision pin; the split into
`-core` exists only to keep this crate under the crates.io 10 MiB limit, not because the
provenance differs.
