# MM-BUG-CRU-00079 — gen_crate_lib.py custom-API guard misses attribute-prefixed and non-pub hand-written items

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** tools/ferrosintesis-samples
- **Raised:** 2026-09-14T23:40:11Z
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
- **State history:** Open (2026-09-14T23:40:11Z, raised via `deltic bugs new --land` model=claude-opus-5)

## Observation

Split from MM-BUG-CRU-00067 at independent verification (2026-09-14, trunk 56ba5184). That fix (d5e85732) makes gen_crate_lib.py refuse whole-file generation when the existing src/lib.rs declares public items the generator does not produce, via custom_inventory_reason in tools/ferrosintesis-samples/gen_crate_lib.py. The drum-kit crate is now refused and left byte-identical. The detector only recognises items that begin a line with 'pub'. Observed by calling custom_inventory_reason directly: 'pub fn fast() {}' returns a refusal reason, but '#[inline] pub fn fast() {}', '#[macro_export] macro_rules! sample { () => {} }' and a hand-written '#[cfg(test)] mod tests { #[test] fn t() {} }' each return None. A None reason means whole-file generation proceeds and overwrites the file, erasing that hand-written code, which is the failure MM-BUG-CRU-00067 recorded. Expected: generation refuses (or preserves) any hand-written content it does not generate. Actual: attribute-prefixed public items, exported macros and hand-written test modules are not detected. No committed sample crate contains such items today.

Evidence fingerprint: `manual:v1:gen-crate-lib-py-custom-api-guard-misses-attrib-c4f3706d93255cb3`


## Fix

<unfixed — raised only>

## Notes
