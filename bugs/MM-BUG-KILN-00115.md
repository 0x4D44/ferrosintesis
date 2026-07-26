# MM-BUG-KILN-00115 — Licence boilerplate counts as a credit, and real copyright-line credits do not

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** licensing oracles / attribution
- **Raised:** 2026-07-25
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
- **State history:** Open (2026-07-25, found by Claude Opus 4.6 while performing the two-eyes verification of MM-BUG-KILN-00110 — the reported instance was fixed, so the predicate was audited for others) → Fixed (2026-07-25, Claude Opus 4.6, same change; awaiting independent two-eyes verification) → Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: Claude Opus 4.6), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree at b0b93d9: `cargo fmt --all --check`, `clippy --workspace --exclude amp-lab --all-targets -D warnings`, `clippy -p ferrosintesis --no-default-features --all-targets -D warnings`, `test -p ferrosintesis --no-default-features --locked` (628 passed) and `test --workspace --exclude amp-lab --locked` (731 passed) - 1461 tests, 0 failures. Original observation re-run BY REFUTATION ON THE REAL TREE, not by reading the fix - the same method that found this bug's three predecessors. I replaced the tracked `crates/ferrosintesis-samples-clavinet/NOTICE` with the bare MIT grant from the Observation, deleting Frank Wen, Michael Cowgill and S. Christian Collins entirely, and ran `cargo test -p ferrosintesis --lib licensing`. It went RED - three tests, the decisive one naming the crate and the reason: "ferrosintesis-samples-clavinet/NOTICE carries no source URL and no `Copyright (c) ...` line, so nothing in it identifies a licensor." The bug's recorded symptom (that reduction leaves "Software" and "AS IS" as surviving credit tokens while the suite stays green) is therefore false on this tree. NOTICE restored from my backup; `git status --porcelain` for the crate is clean. I also checked the `(c)` subtlety the fix note flags: `carries_licensor_owned_signal` (`licensing.rs:216`) accepts a bare copyright symbol but requires the spelled-out word to be paired with `(c)`, so the "The above copyright notice ... shall be included" sentence present in every licence body cannot re-admit boilerplate. All seven licensing tests green.)

## Observation

The third instance of the MM-BUG-KILN-00071 class, after 00110 and 00111. `credit_tokens`
extracts **any** quoted run of ≥4 characters — and licence boilerplate is full of quoted
phrases.

Auditing all 13 attribution-bearing NOTICEs, two crates yield only boilerplate:

```
ferrosintesis-samples-clavinet:  'MS Basic'  'Software'  'AS IS'
ferrosintesis-samples-musescore: 'MS Basic'  'Software'  'AS IS'
```

`"Software"` and `"AS IS"` come from the MIT text (`…files (the "Software")…`,
`THE SOFTWARE IS PROVIDED "AS IS"`). They identify nobody.

Worse, the credits these two crates *do* carry are invisible to the extractor, because they
are not quoted — they are copyright lines:

```
FluidR3 (original version) by Frank Wen Copyright (c) 2000-02
Mono conversion (FluidR3Mono) by Michael Cowgill Copyright (c) 2014-17
Adaptation for MuseScore_General.sf2 by S. Christian Collins Copyright (c) 2018-19
```

**Expected.** A NOTICE stripped of every real credit fails the attribution oracles.

**Actual.** Cutting `crates/ferrosintesis-samples-clavinet/NOTICE` down to the bare MIT grant —
deleting Frank Wen, Michael Cowgill and S. Christian Collins entirely — leaves `"Software"` and
`"AS IS"` as surviving credit tokens, and the whole licensing suite stays green. **Observed**,
not reasoned: the reduction was applied to the tracked NOTICE and
`cargo test -p ferrosintesis --lib licensing` passed.

That is MM-BUG-KILN-00071's symptom for the third time. Each fix so far has closed the reported
instance while leaving the predicate able to be satisfied by text that credits nobody.

## Fix

Stop asking `credit_tokens` to answer two different questions. It is the right instrument for
*"did a distinctive token travel from the bank's NOTICE into the licensing guide"* — and being
permissive is correct there. It is the wrong instrument for *"is this document an attribution
at all"*.

Added `carries_licensor_owned_signal` in `crates/ferrosintesis/src/licensing.rs`, asserted per
crate inside `every_attribution_bearing_sample_bank_ships_a_notice`: the NOTICE must contain a
**non-`creativecommons.org` source URL** or a **`Copyright (c) …` / `©` line**. Those two are
the licensor's; neither can be produced by licence boilerplate or by our own identifiers.

Derived, not listed: every attribution-bearing crate satisfies it today without edits — the
Freesound / GitHub / archive.org banks via their URLs, the two MuseScore-lineage banks via the
FluidR3 copyright block. A new bank has to carry one or go red.

Two details worth keeping:

- `©` alone counts, but the spelled-out word only counts with `(c)`. Every licence body
  contains "The above copyright notice … shall be included", so a bare `copyright` match would
  have re-admitted the boilerplate this fix exists to reject. The first draft got this wrong
  and its own unit test caught it.
- The licence's own `creativecommons.org` URL is excluded, for the same reason `credit_tokens`
  excludes it: it appears in every CC notice and identifies nobody.

Verified by refutation on the real tree: reducing `crates/ferrosintesis-samples-clavinet/NOTICE`
to the bare MIT grant now turns `every_attribution_bearing_sample_bank_ships_a_notice` RED,
naming the crate and explaining that a quoted phrase is not enough. Restored afterwards, suite
green, `git status` clean.

## Notes

- Fixed alongside a latent fragility in the same file (recorded on MM-BUG-KILN-00111):
  `names_license` matched by bare substring, and `MIT` occurs inside `LIMITED`, `LIMITATION`
  and `PERMIT`. Now word-boundary matched.
- The pattern across 00071 → 00110 → 00111 → this one is worth naming: each was found by
  attacking the predicate rather than reading it, and each previous fix was green when the
  next hole was found. The general lesson — a `contains`-shaped credit check is satisfiable
  by text that credits nobody — is now three-for-three, and the strong-signal assertion is the
  first check in this family that is not `contains`-shaped.
