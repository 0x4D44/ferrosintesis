# MM-BUG-NMI-00004 — b1 sustain-pilot output-dir validator false-positives when the user home directory is itself a Git working tree

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** sample tooling / test environment
- **Raised:** 2026-08-15T21:41:47Z
- **Discovery source:** Agent
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
- **State history:** Open (2026-08-15T21:41:47Z, raised via `deltic bugs new`)

## Observation

`tools/ferrosintesis-samples/prepare.py:validate_b1_pilot_output_dir` (line ~3128) walks
every filesystem ancestor of a proposed pilot-output path looking for a `.git` entry, to
stop the offline B1 sustain pilot from writing inside any Git working tree:

```python
cursor = resolved
while True:
    if os.path.exists(os.path.join(cursor, ".git")):
        raise ValueError("B1 pilot output must be outside every Git working tree")
    parent = os.path.dirname(cursor)
    if parent == cursor:
        break
    cursor = parent
```

On this machine the walk reaches `C:\Users\ano`, which is itself a Git working tree root
(`C:\Users\ano\.git` exists). Because the walk climbs to the filesystem root rather than
stopping at some declared boundary, ANY output directory under the user's home — including
every `tempfile.TemporaryDirectory()` default, since Windows resolves `%TEMP%` to
`C:\Users\<user>\AppData\Local\Temp` — is rejected, regardless of whether it is nested
inside the repo or any other working tree ferrosintesis cares about.

Reproduction (from a repo checkout on this box):

```
python -m unittest test_prepare.PrepareSampleBankTests.test_b1_sustain_pilot_output_is_outside_every_git_tree_and_empty
python -m unittest test_prepare.PrepareSampleBankTests.test_b1_sustain_pilot_preserves_assets_and_cleans_decode_temp
```

Both raise `ValueError: B1 pilot output must be outside every Git working tree` from
inside `run_b1_sustain_pilot`, because the tests use `tempfile.TemporaryDirectory()` (or
an equivalent default-temp-rooted path) as their "known good, outside every worktree"
fixture, and that fixture is not actually outside every worktree on this machine.

Expected: the validator's intent is "not inside *this repository* or *a ferrosintesis
worktree*" (per its own docstring: "It may never point at this repo, another worktree, or
a directory that already carries artifacts"), not "not inside any Git-tracked directory
anywhere on the filesystem up to the drive root." Actual: it conflates the two, so a
perfectly safe pilot-output directory is rejected purely because some unrelated ancestor
(the user's home directory, here used for dotfiles/config tracking) happens to be a `.git`
root.

Discovered 2026-08-15 as a byproduct of an unrelated bug-ledger verification pass
(`cargo test` / `python -m unittest discover` gate run) — confirmed unrelated to any of the
Fixed bugs being verified in that pass; this test/behaviour predates all of them and fails
identically regardless of which commit is checked out, since the trigger is this
machine's home-directory layout, not repo content.

## Fix

<unfixed — raised only>

## Notes

- Impact is test-environment-specific: the pilot itself may work fine when actually run
  with a genuinely repo-external output directory that has no `.git` ancestor; the defect
  is in how tightly `validate_b1_pilot_output_dir` scopes "every Git working tree," and in
  the two tests trusting a machine-dependent default temp root as their negative fixture.
- A plausible fix: bound the ancestor walk to a declared root (e.g. stop once `cursor` is
  no longer under any *registered* ferrosintesis worktree, via `git worktree list`, rather
  than walking to the drive root), or have the tests construct their fixture under a
  directory they control and know is `.git`-free rather than trusting `tempfile`'s default.
- Not observed to affect any packaged sample bank or committed asset — the sustain pilot
  writes to scratch, so a false rejection blocks the tool loudly rather than corrupting
  output.
