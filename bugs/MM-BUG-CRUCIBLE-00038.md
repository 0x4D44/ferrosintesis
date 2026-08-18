# MM-BUG-CRUCIBLE-00038 — Shipped NOTICE instructs distributors to reproduce ten attribution notices; nine exist and nine are listed

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** licensing / attribution documentation
- **Raised:** 2026-08-18T00:07:44Z
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
- **State history:** Open (2026-08-18T00:07:44Z, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

**Symptom.** `crates/ferrosintesis/NOTICE` is the index a downstream binary distributor
reads to discharge its attribution obligations. Its own arithmetic does not close, and the
count it states in a mandatory instruction is wrong.

`crates/ferrosintesis/NOTICE:7-14`:

> "A build with default features (`embedded-samples`) compiles **twenty-four** first-party
> sample-asset crates into the binary. **Fifteen** are CC0 1.0 and require nothing. The
> **ten** below are not... YOU MUST REPRODUCE THE **TEN** NOTICES LISTED HERE... concatenating
> those **ten** satisfies every obligation below."

24 − 15 = **9**, not ten.

**Expected.** The stated count equals the number of attribution-bearing banks a default
build embeds, and equals the number of blocks the document lists.

**Actual.** Measured on this tree:

| Quantity | Derived value | Method |
|---|---:|---|
| sample-asset crates in the `embedded-samples` list | 24 | `crates/ferrosintesis/Cargo.toml:32-57` |
| declaring `license = "CC0-1.0"` | 15 | census of `crates/ferrosintesis-samples-*/Cargo.toml` |
| declaring a non-CC0 licence | 9 | 3 MIT, 3 CC-BY-3.0, 2 CC-BY-4.0, 1 `CC-BY-4.0 AND CC-BY-3.0` |
| crates named in the NOTICE index | 9 | `NOTICE:24, 25, 27, 48, 54, 61, 72, 83, 96` |

So "twenty-four" and "Fifteen" are right and "ten" is wrong in all three places. The nine
named crates are clavinet, musescore, musescore-grand, grand, ydp-grand, gong, headroom,
sax, ccby — exactly the nine non-CC0 manifests, so the *content* of the index is correct
and complete. Only the count word is wrong.

**Why this matters rather than being a typo.** These are the only sentences in the repo
phrased as a legal instruction to a third party, and they ship: `ferrosintesis` 0.21.58 was
published from this tree. A distributor told to reproduce ten notices counts nine and
cannot tell whether a tenth was omitted from the index or the count is simply stale — the
one thing this document exists to make unambiguous.

**Same defect, second site.** `crates/ferrosintesis/src/licensing.rs:7` says the default
feature "pulls in **twenty-five** of them"; the feature list has 24. `licensing.rs` is
packaged (`include = ["src/**"]`), so this renders on docs.rs.

**Why the existing oracles do not catch it.** `crates/ferrosintesis/src/licensing.rs`
derives the attribution-bearing set from the feature list plus each bank's own `license`
field and proves *coverage* — that the README table, the parent `NOTICE` and each packaged
`NOTICE` name every bank that needs one. It never reads the surrounding prose, so a
hand-written count inside the very document the oracle protects is unguarded. That is the
repo's documented recurring failure (CLAUDE.md, *Hand-maintained lists are the recurring
defect here*), one level up: the list is derived, the number describing it is not.

Closed `MM-BUG-KILN-00121` explicitly declined to add a count assertion — "do not add
another hand-maintained count" (`MM-BUG-KILN-00121:49-50`, and its Resolution at `:65-68`).
That reasoning was sound as stated but left the existing prose counts unguarded, and they
have since drifted as crates were added and removed.

Static review only. No build, test, render, or packaging step ran; every number above was
counted from the committed manifests and the committed `NOTICE`.

## Fix

Unfixed. Raised for the fix-open-bugs loop; this review did not change code.

Two directions, and the second is the one MM-BUG-KILN-00121's reasoning points at:

1. Correct "ten" → "nine" at `NOTICE:9, :12, :14` and "twenty-five" → "twenty-four" at
   `licensing.rs:7`. This restores accuracy but recreates the hazard — the next crate
   added or removed re-breaks it silently.
2. Better: remove the bare numerals from the instruction ("reproduce the notices listed
   below"), and add one derived assertion in `licensing.rs` that any numeral the document
   *does* state equals the size of the already-derived set. That is derived, not
   hand-maintained, so it does not reintroduce what MM-BUG-KILN-00121 refused.

Whichever is chosen, the negative control matters: write a NOTICE whose count disagrees
with the derived set and prove the new assertion goes red, per CLAUDE.md's rule that an
oracle must be shown to fail once.

## Notes

- Three CC0 crates ship a courtesy `NOTICE` despite needing none — honkytonk, vcsl-kawai,
  vcsl-steinway — so 12 `NOTICE` files exist against 9 required. `licensing.rs` correctly
  filters these out of the attribution set; noted so a fixer counting files rather than
  obligations does not "correct" nine to twelve.
- Found during the coverage-ledger review of `crates/ferrosintesis-samples-bass/`. Bass is
  CC0 and is on the correct side of this arithmetic; it surfaced only because the pass
  checked whether the parent NOTICE needed to mention it.
- Estimated effort: Small for direction 1, Small–Medium for direction 2.
