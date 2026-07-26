# MM-BUG-KILN-00135 — Grand regeneration docs invoke the whole multi-bank bake

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / grand-piano regeneration
- **Raised:** 2026-07-26
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260726T134236Z-p35852-n696737100-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00135-run-fix-20260726T134236Z-p35852-n696737100-c1
- **Owner base:** 1b05d5a604c1d87e21b29867f05115b5e40a69a5
- **Owner fingerprint:** -
- **Owner since:** 2026-07-26T13:42:36Z
- **Owner until:** 2026-07-26T15:42:36Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-26, raised by Codex review lead from the coverage-ledger review of `crates/ferrosintesis-samples-grand/`)

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
