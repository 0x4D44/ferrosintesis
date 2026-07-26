# Retired drum overlays

Eight baked WAVs — crash cymbal, suspended cymbal, kick and snare, two round robins
each — trimmed from [VSCO 2 Community Edition](https://github.com/sgossner/VSCO-2-CE)
(Versilian Studios / sgossner) at pinned commit
`440300901dfe9275fd84e0b7763af1f8443ae62e`, released under **CC0 1.0**. Their bake
recipe is still recorded in `../prepare.py` (`DRUM_SOURCES` for the upstream URLs,
`KEEP_FILE` for the per-file trim and fade).

**Nothing loads them.** They were the pre-drumkit overlay layer for the default kit;
`crates/ferrosintesis-samples-drumkit` (see `../prepare_drumkit.py`) superseded that
path, and no `ferrosintesis` code has referenced these files since.

**They are deliberately outside the published crate.** They lived in
`crates/ferrosintesis-samples-orchestral/samples/` until 2026-07-26, where ~919 KiB of
`include_bytes!` payload was compiled into every binary and shipped in the crates.io
package for nothing. Moving them here removes both costs without removing the bytes.

**They are kept, not deleted, because they are calibration evidence.**
`drum_crash1_ff_rr1.wav` is the real-cymbal measurement reference the shipped
MetalPlate cymbal model was fitted and tested against. Two design documents cite it
directly:

- `wrk_docs/2026.07.13 - HLD - cymbal plate synthesis and its oracle.md`
- `wrk_docs/2026.07.14 - HLD - MetalPlate V4 dense fixed-plate cymbal model.md`

Deleting the file would delete the evidence behind a model we still ship.

**Do not re-bake these in place.** The onset trim changed after they were made (see
`old_trim` in `../test_prepare.py`), so re-running `prepare.py` over the upstream
sources would produce different bytes and silently overwrite the reference. `DRUM_SOURCES`
is therefore kept inert rather than retargeted at this directory. Git history is the
integrity record for what is committed here.
