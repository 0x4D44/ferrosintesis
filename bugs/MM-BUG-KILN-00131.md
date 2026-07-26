# MM-BUG-KILN-00131 — Core drum-kit crate rustdoc names the wrong kick mic source (mid_kick_snon)

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample packaging / provenance
- **Raised:** 2026-07-26
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
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=claude-opus-5@high) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T100451Z-p32652-n863317900-c1 branch=task/bug-MM-BUG-KILN-00131-run-fix-20260726T100451Z-p32652-n863317900-c1 code=4e2ee12b84f3cb0c4891d90745cd09dc602fc1cf gate=manual)

## Observation

**Symptom.** The core drum-kit crate's own rustdoc names the wrong recording source for the kick, in a documentation surface that is PACKAGED and published.

`crates/ferrosintesis-samples-drumkit/src/lib.rs:682` reads:

    /// Kick drum, snares on (`mid_kick_snon`) -- the source's full 4x4 grid of
    /// velocity layers x TRUE round robins.

**Ground truth.** The generator sources all sixteen kick takes from the `kickmic` close-mic set, not `mid`: `tools/ferrosintesis-samples/prepare_drumkit.py:105-109` builds the URL from `Samples/kickmic/kick/kickmic_kick_snon_vl{vl}_rr{rr}.flac`, under a comment that says "kick, snares on, CLOSE MIC (kickmic_kick_snon)".

**Expected.** Every packaged documentation surface names `kickmic_kick_snon`.

**Actual.** `PROVENANCE.md:69` says `kickmic_kick_snon` (correct); the sibling rustdoc in the same crate still says `mid_kick_snon`. `Cargo.toml:13` includes `src/**` in the package, so this line ships to crates.io and renders on docs.rs.

**Provenance.** Split out of MM-BUG-KILN-00126 during its independent two-eyes verification. That bug reported the same factual error and cited it at `PROVENANCE.md:36-52,60-72`; those lines were corrected and the README inventory error was corrected, so 00126 is genuinely fixed and was closed. This instance was not cited and was not swept.

This is the pattern CLAUDE.md records under "Hand-maintained lists are the recurring defect here": the reported item is evidence the surface is unmaintained, not a spec of the work. A repo-wide enumeration during verification found exactly one surviving instance (the two other hits are a code-review doc and a journal, both correctly dated history that should not be edited).

**Why the new guard does not catch it.** MM-BUG-KILN-00126's fix added `test_core_provenance_source_stems_match_the_generator_manifest` (`tools/ferrosintesis-samples/test_prepare_drumkit.py:12`), which is properly DERIVED - it reconstructs each core family's expected source stem from the generator's own `BANKS` / `PSEUDO_RR_BANKS` manifest rather than from a second hand-written list. But it reads exactly one document: the core package's `PROVENANCE.md`. It never inspects `src/lib.rs`. So the rustdoc stem is unguarded, which is both why this instance survived the fix and why it can drift again.

**Fix direction.** Correct the rustdoc line to `kickmic_kick_snon`. Consider whether the existing derived provenance/inventory oracles can be extended to cover source-stem claims in crate rustdoc, so this pair cannot drift again - but do not add another hand-maintained list.

## Fix

<unfixed — raised only>

## Notes
