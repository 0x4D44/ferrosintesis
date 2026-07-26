# MM-BUG-KILN-00122 — Dark-Salamander documentation selects the B1 upright and names the wrong A/B baseline

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample assets / GM0 alternate-bank routing
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
- **State history:** Open (2026-07-26, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-dark-salamander/`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T073254Z-p43624-n750388200-c1 branch=task/bug-MM-BUG-KILN-00122-run-fix-20260726T073254Z-p43624-n750388200-c1 code=9c2baab298ed33ac1cfce2fd7f10144e14bfacfa gate=manual) -> Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: deltic:auto role=fix), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree: `cargo fmt --all --check`, `clippy --workspace --exclude amp-lab --all-targets -D warnings`, `clippy -p ferrosintesis --no-default-features --all-targets -D warnings`, `test -p ferrosintesis --no-default-features --locked` (630 passed) and `test --workspace --exclude amp-lab --locked` (735 passed) - 1468 tests, 0 failures. Original observation re-run at source, on both halves the bug separates. FIRST, the routing is genuinely UNCHANGED, as the fix direction required: `altbank.rs` still maps GM0 CC0=1 to `grand_bank`, CC0=4 to `darkgrand_bank` and CC0=5 to `b1upright_bank`, and the 108 lines this commit added to that file are entirely a new `#[cfg(test)]` oracle - no shipped dispatch moved. SECOND, every documentation surface the bug enumerated now names bank 4: the crate module docs ("GM0 acoustic-grand alternate bank 4"), the manifest description, the README ("CC0 bank 4"), `PROVENANCE.md` ("bank select CC0=4"), `sampler.rs` and `prepare.py`. A repo-wide grep for a dark-Salamander claim tied to bank 5 or CC0=5 returns nothing. The A/B endpoint the bug called wrong is corrected too: the provenance now reads "it A/Bs CC0=4 directly against CC0=1 (raw Salamander)", which is the comparison the bug said was intended. So following the packaged README now selects `darkgrand_bank`, not `b1upright_bank` - the reproduction's step 2 no longer holds. I checked the new guard is derived rather than a second hand-copy by re-implementing its predicate myself: it parses the live GM0 match arms out of `altbank.rs` and recovers dark=4, raw=1, b1=5, then requires each document to carry text built from those derived numbers. And I proved it is non-vacuous by REINTRODUCING the bug - editing the tracked README back to "CC0 bank 5" turned it red with "crate README does not identify the routed selector: expected \"CC0 bank 4\"". Restored; `git status --porcelain` clean.)

## Observation

The published asset crate says the darkened Salamander is the GM0 alternate at
bank-select MSB CC0=5:

- `crates/ferrosintesis-samples-dark-salamander/src/lib.rs:1`;
- `crates/ferrosintesis-samples-dark-salamander/Cargo.toml:6`;
- `crates/ferrosintesis-samples-dark-salamander/README.md:3-9`;
- `crates/ferrosintesis-samples-dark-salamander/PROVENANCE.md:9-12`.

Its provenance also says the default GM0 grand is the raw, bright Salamander and
describes the experiment as an A/B against bank 0
(`crates/ferrosintesis-samples-dark-salamander/PROVENANCE.md:17-21`).

The shipping routing says otherwise. `crates/ferrosintesis/src/altbank.rs:1041-1058`
maps raw Salamander to CC0=1, dark-Salamander to CC0=4, and the unrelated
first-party B1 upright to CC0=5. The GM0 default is the VSCO upright
(`crates/ferrosintesis/src/voices.rs:13122-13142`).

Static reproduction:

1. Follow the packaged README and author GM program 0 with bank-select MSB CC0=5.
2. `altbank::make` selects `b1upright_bank`, not `darkgrand_bank`.
3. Compare bank 5 with the documented bank-0 baseline.

Expected: CC0=5 selects the warmer copy of the raw Salamander, and bank 0 is its
unprocessed counterpart.

Actual: CC0=5 selects the B1 upright; bank 0 selects another upright. The intended
same-recording EQ comparison is raw Salamander at CC0=1 versus dark-Salamander at
CC0=4.

This was not an historical bank-5 mapping. Commit `0281dcd` introduced the
dark-Salamander route at CC0=4 and the incorrect bank-5 prose together; commit
`0a47568` later assigned CC0=5 to the B1. “Fifth GM0 option” counts the default
bank 0 and does not imply a CC0 value of 5.

## Fix

Keep the routing unchanged. Correct the crate module docs, manifest description,
README and provenance to say bank-select MSB CC0=4, and describe the A/B as
CC0=1 versus CC0=4.

Correct the same stale contract in
`crates/ferrosintesis/src/sampler.rs:1469-1472,1575-1577` and
`tools/ferrosintesis-samples/prepare.py:2639-2645,3006-3009`.

Add a focused, source-derived routing/documentation regression so the named GM0
alternate identities cannot drift independently again.

Estimated effort: Small.

## Notes

This is distinct from closed MM-BUG-KILN-00069. That bug removed ambiguous
“CC0 bank N” licence wording; it did not address this wrong numeric selector or
the wrong A/B endpoint.

No build, test, render, or application execution was performed in the read-only
review. The defect was confirmed from the exact dispatch and default-voice
source paths, then independently challenged by a devil's-advocate reviewer.
