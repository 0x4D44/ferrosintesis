# MM-BUG-KILN-00150 — MuseScore sample notice omits mandatory upstream acknowledgements

- **State:** Fixed
- **Priority:** Should
- **Severity:** High
- **Area:** sample packaging / licensing
- **Raised:** 2026-07-27
- **Owner:** -
- **Owner role:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner fingerprint:** -
- **Owner since:** -
- **Owner until:** -
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=gpt-5.6-sol@high) → Fixed (2026-07-27, deltic:auto role=fix run=fix-20260727T054903Z-p9812-n086124000-c54 branch=task/bug-MM-BUG-KILN-00150-run-fix-20260727T054903Z-p9812-n086124000-c54 code=4278b0bdf638a33faa52cfec03304effd540f261 gate=focused-licensing model=codex@xhigh; held branch recovered by Codex)

## Observation

Static reproduction:

1. Read the crate's pinned source at
   `crates/ferrosintesis-samples-musescore/PROVENANCE.md:18-20`. It identifies
   MuseScore commit `d307a2bd899f15bf650efc3c2891211af5cb78b5` and the exact
   `MS Basic.sf3` SHA-256.
2. At that commit, upstream
   [`share/sound/MS Basic_License.md`](https://github.com/musescore/MuseScore/blob/d307a2bd899f15bf650efc3c2891211af5cb78b5/share/sound/MS%20Basic_License.md)
   lists five acknowledgements, then states that the acknowledgements and copyright
   notices above must be included in any derivative work.
3. `crates/ferrosintesis-samples-musescore/NOTICE:3-10` says those acknowledgements
   "are reproduced here", but reproduces only three. It omits:
   - `Temple Blocks instrument provided by Ethan Winer Copyright (c) 2002`
   - `Drumline Cymbals provided by Michael Schorsch Copyright (c) 2016`

Expected: the independently publishable sample crate carries every acknowledgement
that its pinned upstream licence requires.

Actual: its packaged `NOTICE` omits two of the five mandatory acknowledgement lines.
A distributor following the repository's instruction to concatenate the asset-crate
notices therefore receives incomplete attribution text.

The same static pass found nearby evidence of selective transcription drift:

- `NOTICE:14-16` says the crate contains only GM 104 sitar and GM 75/76/77 pipe
  onsets, while `src/lib.rs:63-94` also embeds eight GM 8 celesta WAVs. This is the
  still-live NOTICE portion of closed `MM-BUG-KILN-00069`; its recorded fix changed
  README/Cargo/PROVENANCE but never changed this NOTICE.
- `README.md:26-28` points readers to `tools/ferrosintesis-samples/README.md` for the
  source pin and regeneration recipe even though that guide's MuseScore inventories
  omit celesta and it calls clavinet the only non-CC0 bank. The packaged
  `PROVENANCE.md:7-20` is the accurate authority.

No build, test, application, render, generator, package command, or exploratory
harness ran. The WAVs and documents were inspected read-only.

## Fix

Reproduce both missing upstream acknowledgement lines in this crate's `NOTICE`.
Sweep the sibling notices and the parent consolidated notice that transcribe the same
pinned source so the same omission does not remain elsewhere. Update or remove the
NOTICE's partial instrument inventory, and make this crate's README point to its
packaged `PROVENANCE.md` as the source-pin and scoped-regeneration authority.

Add a regression in `crates/ferrosintesis/src/licensing.rs` that rejects an
MS-Basic-derived packaged notice when any acknowledgement required by the pinned
upstream licence is absent. Prefer checking against a committed verbatim copy of the
pinned upstream licence over maintaining another selective name list.

Estimated effort: Small.

### Fix summary (2026-07-27, deltic:auto run=fix-20260727T054903Z-p9812-n086124000-c54 code=4278b0bdf638a33faa52cfec03304effd540f261 gate=focused-licensing)

Agent-reported summary: Fixed MM-BUG-KILN-00150 by completing the MuseScore MS Basic attribution text in the packaged notices that transcribe the pinned source. Reproduced the original observation first: the MuseScore sample crate NOTICE was missing the Temple Blocks and Drumline Cymbals acknowledgement lines. Added a focused licensing regression that derives the required acknowledgement set from the committed pinned upstream licence fixture and checks the MS-Basic-derived asset notices plus the parent consolidated notice. Updated the MuseScore sample crate inventory/docs so celesta is named and the crate README points to its own PROVENANCE.md for the source pin and regeneration recipe. The focused licensing module passes in both default and no-default-feature builds.

Root cause: The MS Basic acknowledgement block was hand-transcribed into notices, while the existing licensing oracle only proved that some distinctive credit token travelled. That allowed a selective subset of the upstream-required acknowledgement lines to pass as complete attribution.

Changed:
- crates/ferrosintesis/src/licensing.rs adds an MS Basic acknowledgement completeness regression
- crates/ferrosintesis/src/upstream_licenses/ adds the pinned MS Basic licence fixture used by the regression
- crates/ferrosintesis-samples-musescore and crates/ferrosintesis-samples-clavinet NOTICE files now include the missing Temple Blocks and Drumline Cymbals acknowledgements
- crates/ferrosintesis/NOTICE and crates/ferrosintesis/README.md now carry the complete MS Basic acknowledgement summary
- crates/ferrosintesis-samples-musescore README, PROVENANCE, and crate docs now name celesta and point to crate-local provenance

Tests:
- deltic timeout 180 cargo test -p ferrosintesis licensing::tests::ms_basic_notices_reproduce_every_required_upstream_acknowledgement failed before the notice fix
- deltic timeout 180 cargo test -p ferrosintesis licensing::tests passed
- `cargo test -p ferrosintesis licensing::tests` passed after rebase
- `cargo test -p ferrosintesis --no-default-features licensing::tests` passed after rebase
- `cargo test -p ferrosintesis-samples-musescore` passed
- `cargo test -p ferrosintesis-samples-clavinet` passed
- The committed fixture's alphanumeric content matches the pinned upstream file
  exactly; only Markdown wrapping and heading style differ.
- git diff --check passed

## Notes

This is not a duplicate of `MM-BUG-KILN-00148`, which concerns the standalone
MuseScore-grand crate omitting the MIT permission grant. The primary defect here is
two missing acknowledgements in the `-musescore` crate, which no existing Open bug
covers.
