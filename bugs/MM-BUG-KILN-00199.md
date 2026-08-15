# MM-BUG-KILN-00199 — Generated ALIASES crate test is vacuously green on a dangling canonical target

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** samples gen_crate_lib / oracles
- **Raised:** 2026-08-14T10:21:09Z
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
- **State history:** Open (2026-08-14T10:21:09Z, raised via `deltic bugs new` model=claude-fable-5) -> Fixed (2026-08-15T16:38:42Z, deltic:auto role=fix run=fix-20260815T163323Z-p32188-n779561800-c1 branch=task/bug-MM-BUG-KILN-00199-run-fix-20260815T163323Z-p32188-n779561800-c1 code=b2fe20f gate=manual)

## Observation

**Symptom.** The alias test `gen_crate_lib.py` emits into every ALIASES-bearing sample
crate proves less than its name claims. In
`crates/ferrosintesis-samples-vcsl-steinway/src/lib.rs:227-229` (template at
`tools/ferrosintesis-samples/gen_crate_lib.py:196-198`), alias resolution is asserted as

```rust
for (alias, canonical) in ALIASES {
    assert_eq!(get(alias), get(canonical), "alias {alias}");
}
```

If an `ALIASES` row's canonical target is missing from `SAMPLES`, both sides are `None`
and the assertion is **vacuously green**. Nothing in the crate asserts
`get(alias).is_some()` or that every canonical name exists in `SAMPLES`. The same
generated shape ships in `crates/ferrosintesis-samples-vcsl-kawai/src/lib.rs:237` — the
only two ALIASES crates today.

**What still guards it (why severity is Low).** Generation-time `read_aliases`
(`gen_crate_lib.py:62-69`) rejects dangling canonicals, and the integration gate runs
`tools/ferrosintesis-samples/test_prepare.py`, whose `SteinwayAliasDeduplicationTest`
(`test_prepare.py:2904-2958`) / kawai twin (`:2847-2901`) re-derive the committed
`ALIASES` files from the bake source maps via `read_aliases`
(`.deltic-integrate.toml:59,71` run `python3 -m unittest discover -s
tools/ferrosintesis-samples`). A consistent hand-edit of both `ALIASES` and `lib.rs` is
therefore caught at the gate — for these two crates.

**Residual holes.**

1. The **published** crates carry only the vacuous Rust test: a downstream
   `cargo test -p ferrosintesis-samples-vcsl-steinway` proves aliases resolve *the same*,
   not that they resolve *at all*. Nothing in-repo exercises alias names either — the
   sampler zone tables (`crates/ferrosintesis/src/sampler.rs:1248-1308`) use only
   physical names, so the crate test is the alias contract's sole executable guard.
2. The Python-side protection is **bespoke per crate** (each test was minted by its own
   bug: MM-BUG-KILN-00165, MM-BUG-KILN-00162). The generator will happily emit the
   vacuous test into any **future** ALIASES crate, which then has no derived guard at
   all until someone hand-writes a third unittest.

Expected: the generated test proves each alias resolves to real bytes — the
one-line-stronger form costs nothing.

Found by the 2026-08-14 review pass over `crates/ferrosintesis-samples-vcsl-steinway/`;
the original broader claim ("a hand-edit ships green") was refuted by an adversarial
verify pass, which located the Python gate tests; this record carries what survived.

## Fix

<unfixed — raised only>

Suggested shape: in the template at `gen_crate_lib.py:196-198`, resolve the canonical
against `SAMPLES` directly and unwrap:

```rust
for (alias, canonical) in ALIASES {
    let bytes = get(canonical).unwrap_or_else(|| panic!("alias {alias} dangles: {canonical}"));
    assert_eq!(get(alias), Some(bytes), "alias {alias}");
}
```

then regenerate both crates' `lib.rs`. Prove it the KILN-00073 way: point one ALIASES
row (in a scratch copy of both files) at a nonexistent canonical and watch the
strengthened test go red where the current one stays green.

## Notes

- Related but separable observation, recorded in the 2026.08.14 CR report rather than
  filed: `steinway_logical_aliases_share_decoded_banks`
  (`crates/ferrosintesis/src/sampler.rs:7461-7477`) is `ptr::eq` on functions that call
  each other, i.e. true by construction — a change-detector, not a cross-artifact
  oracle.
