# MM-BUG-KILN-00160 — Strings sample package still omits GM32 from public metadata and regeneration

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** sample packaging / strings metadata
- **Raised:** 2026-07-28
- **Owner:** deltic:gpt-5.5
- **Owner role:** fix
- **Owner run:** fix-20260728T111505Z-p57192-n305240400-c180
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00160-run-fix-20260728T111505Z-p57192-n305240400-c180
- **Owner base:** 9042ffd8bc5ad21fdd478a09f08c9338d81217c3
- **Owner fingerprint:** -
- **Owner since:** 2026-07-28T11:15:05Z
- **Owner until:** 2026-07-28T12:00:05Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

The published strings sample package has three intentional families:
`cellosolo_*` (16 WAVs), `dbass_*` (16 WAVs), and `pizzbass_*` (8 WAVs).
`crates/ferrosintesis-samples-strings/README.md:17`,
`crates/ferrosintesis-samples-strings/PROVENANCE.md:12-14`, and
`crates/ferrosintesis-samples-strings/src/lib.rs:19-180` agree on that 40-file
inventory.

The public regeneration command at
`crates/ferrosintesis-samples-strings/README.md:24-25` selects only
`cellosolo,dbass`. `tools/ferrosintesis-samples/prepare.py:3339-3347` defines
`--only` as an exact family selection, `:3394-3402` fetches the three families
independently, and `:3535-3547` skips every source whose prefix was not selected.
Following the README therefore exits after rebuilding 32 of the 40 packaged WAVs
while leaving all eight GM32 pizzicato outputs untouched. A maintainer can believe
the package was reproduced even though 20% of its assets remain stale.

The same omitted family leaves the published summaries materially inaccurate:

- `crates/ferrosintesis-samples-strings/Cargo.toml:6` describes only bowed GM42/43;
- `crates/ferrosintesis-samples-strings/src/lib.rs:1-12` says the crate contains
  bowed attacks that crossfade into the bowed-string waveguide;
- `crates/ferrosintesis-samples-strings/README.md:3-7` repeats that bowed-only
  description, despite its own GM32 row at `:17`.

This is unfinished remediation from closed `MM-BUG-KILN-00069`, not a later
regression. Fix commit `96e2a47` added the `pizzbass_*` README row and the complete
three-family command to `PROVENANCE.md`, but did not update the pre-existing
two-family README command or the package summaries. Nevertheless,
`bugs/MM-BUG-KILN-00069.md:189-190` and
`crates/ferrosintesis-samples-strings/PROVENANCE.md:16-19` record those surfaces as
corrected. Commit `23f648b` later changed only `python` to `python3`; it preserved
the incomplete selector.

Expected: every public inventory and the advertised regeneration recipe cover all
three packaged families.

Actual: the detailed tables cover all three, but the executable README recipe and
the package-level summaries omit GM32 `pizzbass_*`.

## Fix

<unfixed — raised only>

Update the README command to
`--only=cellosolo,dbass,pizzbass`. Make the Cargo description, crate rustdoc, and
README introduction either name all three families or delegate to the packaged
`PROVENANCE.md`; correct the false historical claim there.

Add a source-derived regression oracle that compares every advertised `--only`
selector with the packaged family prefixes. Its negative control should keep a
complete family table while omitting one family from the command, because the
current inventory oracle accepts exactly that shape. Harden the public-summary
oracle so a two-of-three family description cannot evade its current threshold.

## Notes

- Static code-review finding. No build, test, sample regeneration, application run,
  or exploratory audio harness was executed.
- Confidence: high. Effort: Small for the metadata corrections; Small–Medium with
  the two adversarial oracle cases.
