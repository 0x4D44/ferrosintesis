# Provenance - ferrosintesis-samples-strings

Every WAV this crate packages, with the pinned source it was baked from. Machine-checked
by `crates/ferrosintesis/src/inventory.rs`: a family that ships without a row here fails
the build (MM-BUG-KILN-00069).

Regenerate with `python3 tools/ferrosintesis-samples/prepare.py --only=cellosolo,dbass,pizzbass` from the repository
root.

| Family | Files | Instrument | Source | Licence |
|--------|------:|------------|--------|---------|
| `cellosolo_*` | 16 | Solo cello (GM 42) arco onsets | sfzinstruments/karoryfer-bigcat.cello, REV pinned in `prepare.py` | CC0-1.0 |
| `dbass_*` | 16 | Solo double bass (GM 43) arco onsets | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `pizzbass_*` | 8 | Solo double bass **pizzicato** (GM 32 acoustic bass) | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |

The `pizzbass_*` family once shipped undocumented: earlier public summaries named only
`cellosolo_*` and `dbass_*` (32 of the 40 packaged WAVs), and one README regeneration
command omitted it, so it rebuilt 32 of 40 files. The packaged inventory and regeneration
command here are the canonical public record for all three families.
