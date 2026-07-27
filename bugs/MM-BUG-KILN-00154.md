# MM-BUG-KILN-00154 — Orchestral2 public inventory omits most shipped families

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** orchestral2 / published metadata
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
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

**Symptom.** The published crate front door presents five families as its
“Contents & provenance” inventory, but the package ships 14.

`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\crates\ferrosintesis-samples-orchestral2\README.md:13`
lists harp, timpani, recorder, ocarina, and banjo: 50 WAVs. The complete packaged
inventory at
`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\crates\ferrosintesis-samples-orchestral2\PROVENANCE.md:12`
contains 14 families and 132 WAVs. The omitted nine families are `eastpick`,
`eastpluck`, `glock`, `marimba`, `musicbox`, `tubular`, `vibes`, `viola`, and
`xylo`: 82 shipped assets.

`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\crates\ferrosintesis-samples-orchestral2\Cargo.toml:6`
repeats the same stale five-family description. Crate rustdoc at
`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\crates\ferrosintesis-samples-orchestral2\src\lib.rs:8`
directs provenance readers to the incomplete README and repository tooling
instead of the complete packaged `PROVENANCE.md`.

**Expected.** Exhaustive-looking published inventory surfaces match the package,
or state that they are examples and link the packaged authority.

**Actual.** crates.io consumers and auditors receive a false primary inventory
that omits 62% of the audio.

**Concrete fix.** Make `PROVENANCE.md` the named canonical public inventory,
update or remove the hand-maintained family list in the Cargo description, and
either derive the README table or label a short list as non-exhaustive. Extend
the inventory oracle to guard every surface that claims exhaustiveness.

## Fix

<unfixed — raised only>

## Notes

Current packaging, family counts, and licences are correct. This is the public
metadata residual left after MM-BUG-KILN-00069 added the complete packaged
provenance table.
