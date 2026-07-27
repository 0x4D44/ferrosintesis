# MM-BUG-KILN-00150 — MuseScore sample notice omits mandatory upstream acknowledgements

- **State:** Closed
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
- **Attempts:** fix=3, doubt=1, indeterminate=0
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=gpt-5.6-sol@high) → Fixed (2026-07-27, deltic:auto role=fix run=fix-20260727T054903Z-p9812-n086124000-c54 branch=task/bug-MM-BUG-KILN-00150-run-fix-20260727T054903Z-p9812-n086124000-c54 code=4278b0bdf638a33faa52cfec03304effd540f261 gate=focused-licensing model=codex@xhigh; held branch recovered by Codex) → Open (2026-07-27, deltic:auto role=verify run=verify-20260727T113201Z-p9812-n730268400-c75 verified_fix_run=fix-20260727T054903Z-p9812-n086124000-c54 verdict=doubt reason=static-fix-and-regression-look-correct-and-complete-but-this-sessions-bash-permi model=claude) → Blocked (2026-07-27, deltic:auto role=fix run=fix-20260727T114906Z-p9812-n236554200-c78 verdict=fix_failed reason=no_work model=codex@xhigh) → Fixed (2026-07-28, state restored by GPT-5.6 Codex after executable evidence confirmed the landed fix) → Closed (2026-07-28, independently verified by GPT-5.6 Codex; original omissions reproduced, regression sensitivity proved, focused default and no-default-feature licensing gates green)

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

### Verification summary (2026-07-27, deltic:auto run=verify-20260727T113201Z-p9812-n730268400-c75 verified_fix_run=fix-20260727T054903Z-p9812-n086124000-c54 verdict=doubt)

Verifier note: Static fix and regression look correct and complete, but this session's Bash permission mode denies cargo/rustc outright, so I could not execute the regression test or a single repo gate - criteria 2 (test PASSES) and 3 (gates PASS) are unverified, not failed. — Read bugs/MM-BUG-KILN-00150.md (State: Fixed, fix commit 4278b0b). CRITERION 1 (symptom) CONFIRMED gone: crates/ferrosintesis-samples-musescore/NOTICE now reproduces all five upstream acknowledgements including the two the bug named verbatim - 'Temple Blocks instrument provided by Ethan Winer Copyright (c) 2002' and 'Drumline Cymbals p...

### Independent verification (2026-07-28)

GPT-5.6 Codex reproduced the pre-fix notice at `e84c8e2`: it omitted the
Temple Blocks and Drumline Cymbals acknowledgements. Removing those two lines
from the current MuseScore notice made
`ms_basic_notices_reproduce_every_required_upstream_acknowledgement` fail and
name both omissions; restoring the final notice made all 11 licensing tests
pass with default features and with `--no-default-features`. The current
packaged notice contains all five acknowledgements. This independently
confirms the symptom, regression sensitivity, and landed root-cause fix.

## Notes

This is not a duplicate of `MM-BUG-KILN-00148`, which concerns the standalone
MuseScore-grand crate omitting the MIT permission grant. The primary defect here is
two missing acknowledgements in the `-musescore` crate, which no existing Open bug
covers.

### Fix attempt summary (2026-07-27, deltic:auto run=fix-20260727T113801Z-p9812-n904678400-c76 outcome=no_work)

Agent-reported summary: MM-BUG-KILN-00150 was already code-fixed in this worktree by the prior landed fix commit, which is contained in main; this pass reproduced the original recorded defect against the pre-fix parent and verified the current tree. The pre-fix MuseScore sample NOTICE promised to reproduce the MS Basic acknowledgements but omitted the Temple Blocks and Drumline Cymbals lines. The current tree carries the full required acknowledgement set in the MuseScore, clavinet, and parent notices, plus a licensing regression derived from the pinned upstream licence fixture. The focused licensing tests passed with default features and with --no-default-features. No Cargo, bug ledger, journal, scratchpad, or addi

Root cause: The MS Basic acknowledgement block was hand-transcribed into packaged notices, while the old licensing oracle only proved that some distinctive credit token travelled. That allowed a selective subset of the upstream-required acknowledgement lines to look complete.

Changed:
- No additional shipped code or test files changed in this pass; the current tree already contains the relevant NOTICE updates and licensing regression for MM-BUG

Tests:
- deltic timeout 180 cargo test -p ferrosintesis licensing::tests
- deltic timeout 180 cargo test -p ferrosintesis --no-default-features licensing::tests

Left alone:
- bugs/
- Cargo.toml
- Cargo.lock
- wrk_journals/
- scratchpad.md

### Fix attempt summary (2026-07-27, deltic:auto run=fix-20260727T114402Z-p9812-n071981400-c77 outcome=no_work)

Agent-reported summary: Reproduced the original MM-BUG-KILN-00150 observation against the recorded pre-fix parent: the old MuseScore sample NOTICE promised to reproduce the MS Basic acknowledgements but omitted the Temple Blocks and Drumline Cymbals lines. The current tree already contains the root-cause fix from the earlier landed code change, so this pass made no additional shipped code or test edits. Current notices include the complete acknowledgement set for the MuseScore-derived sample crates and the parent ferrosintesis NOTICE. The regression in ferrosintesis licensing derives the required acknowledgement lines from the pinned upstream MS Basic licence fixture instead of a hand-maintained subset. The focused

Root cause: The MS Basic acknowledgement block was hand-transcribed into packaged notices while the old licensing oracle only checked for partial attribution tokens, so missing required upstream acknowledgement lines were not detected.

Changed:
- No additional shipped code or test files changed in this pass; the current tree already contains the NOTICE updates and fixture-backed licensing regression for
- .deltic-run-summary.json written for Deltic scheduler reporting.

Tests:
- $null | deltic timeout 180 cargo test -p ferrosintesis licensing::tests
- $null | deltic timeout 180 cargo test -p ferrosintesis --no-default-features licensing::tests

Left alone:
- bugs/
- Cargo.toml
- Cargo.lock
- wrk_journals/

### Fix attempt summary (2026-07-27, deltic:auto run=fix-20260727T114906Z-p9812-n236554200-c78 outcome=no_work)

Agent-reported summary: MM-BUG-KILN-00150 was reopened because the prior verifier could not execute cargo, not because the static fix failed. I reproduced the original recorded observation against the pre-fix blob: the old MuseScore sample NOTICE omitted the Temple Blocks and Drumline Cymbals acknowledgement lines. I also proved the regression fails by temporarily removing those lines from the current NOTICE, then restored the final tree. The current tree contains those acknowledgements in the MuseScore-derived notices and the parent notice, plus the fixture-backed licensing regression. The focused licensing module passes in this worktree with default features and with --no-default-features.

Root cause: The MS Basic acknowledgement block was hand-transcribed into packaged notices while the previous licensing oracle only checked partial attribution tokens, so a selective subset of the upstream-required acknowledgement lines could pass as complete.

Changed:
- No additional shipped code or test edits in this pass; the current tree already contains the NOTICE updates and licensing regression for this bug.
- Temporarily removed and restored the two recorded acknowledgement lines from the MuseScore sample NOTICE to prove the regression fails before the fix.
- Wrote .deltic-run-summary.json for Deltic scheduler reporting.

Tests:
- $null | deltic timeout 180 cargo test -p ferrosintesis licensing::tests::ms_basic_notices_reproduce_every_required_upstream_acknowledgement failed with the two
- $null | deltic timeout 180 cargo test -p ferrosintesis licensing::tests::ms_basic_notices_reproduce_every_required_upstream_acknowledgement passed after restori
- $null | deltic timeout 180 cargo test -p ferrosintesis licensing::tests
- $null | deltic timeout 180 cargo test -p ferrosintesis --no-default-features licensing::tests

Left alone:
- bugs/
