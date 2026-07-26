# MM-BUG-KILN-00124 — Drum-kit regeneration ignores the two-crate package split

- **State:** Fixed
- **Priority:** Should
- **Severity:** High
- **Area:** sample generation / drum-kit packaging
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
- **State history:** Open (2026-07-26, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-drumkit/`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T065055Z-p11864-n480023400-c1 branch=task/bug-MM-BUG-KILN-00124-run-fix-20260726T065055Z-p11864-n480023400-c1 code=2a3c656e0199ac2303d6ba7cd4653c3e8b5c9cc4 gate=manual)

## Observation

The documented drum-kit regeneration command cannot reproduce the current two-crate
package layout.

`tools/ferrosintesis-samples/prepare_drumkit.py:76-101` retains all banks in one
`BANKS` list, including the 48 crash, sizzle, splash, and china WAVs that now belong
to `ferrosintesis-samples-drumkit2`. The script defines only one output directory at
`tools/ferrosintesis-samples/prepare_drumkit.py:136-138`, pointing to
`crates/ferrosintesis-samples-drumkit/samples/`. Every normal and pseudo-round-robin
take is written through that path at
`tools/ferrosintesis-samples/prepare_drumkit.py:165-207,232-247`.

The intended contract is explicit at
`crates/ferrosintesis-samples-drumkit2/PROVENANCE.md:111-120`: the generator writes
the whole kit, with four banks landing in the companion crate and the remainder in
the core crate. The committed layout is 140 core WAVs and 48 companion WAVs.

Static reproduction:

1. Run the documented `python tools/ferrosintesis-samples/prepare_drumkit.py`.
2. Inspect the two package sample directories.

Expected: the generator writes each bank to its owning crate and leaves exact 140/48
inventories.

Actual from the enumerated control flow: all 188 output names target the core crate;
the companion crate is never written. The core inventory then disagrees with its
140-entry embedded table. Regenerating that table would reunite the package payload
that was split because crates.io rejected it over the 10 MiB package cap.

The generator was not run during this read-only review.

## Fix

Give every bank an explicit owning output directory, or split the generator into two
explicit output plans. Derive the expected filename set for each crate before writing
and fail closed if the plans overlap or omit a bank.

Add a no-network regression over the generator definitions that proves the two
destination sets exactly match the committed 140/48 package inventories. Keep writes
atomic so a failed regeneration cannot leave either tracked asset directory partial.

Estimated effort: Medium.

## Notes

No existing bug or open requirement matched this post-split generator regression.
The current committed package directories are internally consistent; the defect is
that their documented producer no longer reproduces them.
