# MM-BUG-KILN-00135 — Grand regeneration docs invoke the whole multi-bank bake

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / grand-piano regeneration
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
- **State history:** Open (2026-07-26, raised by Codex review lead from the coverage-ledger review of `crates/ferrosintesis-samples-grand/`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T134236Z-p35852-n696737100-c1 branch=task/bug-MM-BUG-KILN-00135-run-fix-20260726T134236Z-p35852-n696737100-c1 code=85c0bb734b417b3858d1a313184e19ec89a60559 gate=manual) -> Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: deltic:auto role=fix), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree: `cargo fmt --all --check`, both clippy configurations with `-D warnings`, `test -p ferrosintesis --no-default-features --locked` (636 passed) and `test --workspace --exclude amp-lab --locked` (747 passed) - 1486 tests, 0 failures; the sample-tool Python suite passes 67. Original observation re-run at source: both packaged grand documents now carry the scoped `python tools/ferrosintesis-samples/prepare.py --only=grand` as their regeneration recipe (`crates/ferrosintesis-samples-grand/README.md:21`, `PROVENANCE.md:69`), and each explains separately that a bare invocation is the full multi-bank workflow - so a maintainer following the packaged docs no longer rebuilds unrelated banks. `GrandRegenerationRecipeTest` (`test_prepare.py:1044`) adds the doc check plus a selector test proving `--only=grand` bakes neither gong nor bottle; the sample-tool suite passes 67 tests. CLOSED WITH A RESIDUAL SPLIT OUT AS MM-BUG-KILN-00142: the doc half of that guard is `assertIn(COMMAND, f.read())` over the whole file, which cannot tell the recipe a maintainer will copy from a passing mention in prose - and since both documents legitimately discuss the bare invocation as well, a future edit promoting the bare command back into the fenced block would keep the test green while reintroducing exactly this defect. That is the same guard-quality class as MM-BUG-KILN-00115 and 00132, both handled earlier today. I also checked a second claim from the review and am NOT filing it: `tools/ferrosintesis-samples/README.md`'s own `## Regenerating` section does show a bare `prepare.py` in its fence, but that file documents the VSCO multi-bank workflow that rebuilds both packages, where the unscoped command is the correct instruction.)

## Observation

The crate-specific instructions at
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-125503\crates\ferrosintesis-samples-grand\README.md:19`
and
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-125503\crates\ferrosintesis-samples-grand\PROVENANCE.md:66`
tell a maintainer to regenerate this grand bank with:

```powershell
python tools/ferrosintesis-samples/prepare.py
```

The provenance record then describes the path as pure Python standard library.
That accurately describes the Salamander tar.bz2 extraction itself, but not the
bare command.

With no `--only` selector, every `want()` call is true at
`D:\worktrees\midi-music\20260726-REV-CLA@KILN-code-review-125503\tools\ferrosintesis-samples\prepare.py:2920`.
The command traverses and rewrites unrelated sample families at lines
2945–3019. Those paths include 7z-backed archive extraction at line 1265 and
ffmpeg-backed decoding at line 1370.

Static reproduction:

1. Start on a clean machine with Python but without 7z or ffmpeg.
2. Follow either packaged grand-specific regeneration instruction.

Expected: the documented grand recipe regenerates only this crate using the
stated Salamander prerequisites.

Actual: it starts the full multi-bank workflow, can fail on an unrelated
external prerequisite, and can rewrite unrelated tracked sample crates before
or after reaching the grand bank.

## Fix

Change both grand-specific documents to:

```powershell
python tools/ferrosintesis-samples/prepare.py --only=grand
```

State separately that a bare invocation is the full-bank workflow. Add a small
documentation/selection regression that binds the packaged grand recipe to the
`grand` family selector and proves unrelated local banks are not selected.

Estimated effort: Small.

## Notes

No generator or application was run. The side-effect and prerequisite expansion
follow directly from `_family_selection`, `want()`, and the unconditional
no-selector traversal.
