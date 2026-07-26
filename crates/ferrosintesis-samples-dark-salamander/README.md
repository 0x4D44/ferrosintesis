# ferrosintesis-samples-dark-salamander

A **warmer voicing of the Salamander grand** (a high-shelf EQ cut on the CC-BY 3.0
Salamander Grand Piano V3) that voices a **GM 0 Acoustic Grand alternate**
(CC0=5) in [ferrosintesis](https://github.com/0x4D44/ferrosintesis).

Same 9 zones × 3 dynamics × 2 round robins = 54 mono 16-bit 44.1 kHz WAVs as the
Salamander grand (CC0=2), darkened. It exists to A/B against the bright
Salamander grand and answer whether the fix is EQ rather than a new instrument
(see `PROVENANCE.md`).

**Licence: CC BY 3.0**, inherited from Salamander; `NOTICE` credits Alexander Holm
and marks the EQ modification.

Regenerate with `python tools/ferrosintesis-samples/prepare.py --only=darkgrand`
(no network — derives from the tracked grand crate).
