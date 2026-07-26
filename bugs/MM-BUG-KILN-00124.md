# MM-BUG-KILN-00124 — Drum-kit regeneration ignores the two-crate package split

- **State:** Closed
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
- **State history:** Open (2026-07-26, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-drumkit/`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T065055Z-p11864-n480023400-c1 branch=task/bug-MM-BUG-KILN-00124-run-fix-20260726T065055Z-p11864-n480023400-c1 code=2a3c656e0199ac2303d6ba7cd4653c3e8b5c9cc4 gate=manual) -> Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: deltic:auto role=fix), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree: `cargo fmt --all --check`, `clippy --workspace --exclude amp-lab --all-targets -D warnings`, `clippy -p ferrosintesis --no-default-features --all-targets -D warnings`, `test -p ferrosintesis --no-default-features --locked` (629 passed) and `test --workspace --exclude amp-lab --locked` (734 passed) - 1465 tests, 0 failures. Original observation re-run by executing the generator's own plan, not by reading it. I imported `prepare_drumkit` and diffed `output_plan()` against both committed sample directories: the core package plans exactly the 140 committed WAVs and the companion exactly the 48, with zero missing and zero extra in BOTH directions, name for name. No accent stem (crash/sizzle/splash/china) appears in the core plan any more, and the companion owns precisely those four stems - so the bug's "all 188 output names target the core crate" is false on this tree. Every bank now carries an explicit owning package as its first tuple field, and the docstring matches the contract at `crates/ferrosintesis-samples-drumkit2/PROVENANCE.md:111-120` that the bug cited. I attacked the fail-closed validation rather than trusting it: seven mutations - an unknown owning package, a duplicated stem, a name claimed by both packages, a velocity plan not ending at 127, a velocity count disagreeing with the layer count, a ragged pseudo-round-robin plan, and a package left with no banks - are ALL rejected with a named `ValueError`. The added regressions compare the derived plan against the live filesystem (not against a second hand-written list) and cover both failure-atomicity paths; the full sample-tool suite passes 41 tests. One bounded limitation I checked and accept: `publish_staged` copies every WAV to a `.part` sibling before any `os.replace`, so a FAILED GENERATION can no longer leave either directory partial - which is the bug's actual concern - but the final replace loop is per-file, so a process kill mid-loop could still interleave. That is inherent without a cross-directory transaction on Windows, and the code comment states the guarantee it actually provides.)

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
