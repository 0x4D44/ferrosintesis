# MM-BUG-KILN-00060 — The ferrosintesis licence guide omits its default CC-BY Rhodes and dulcimer dependency

- **State:** Fixed
- **Priority:** Must
- **Severity:** Medium
- **Area:** packaging / licensing
- **Raised:** 2026-07-24
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol during the coverage-ledger review of `crates/ferrosintesis-samples-ccby/`)
  → Fixed (2026-07-24, Claude Opus 4.8; the omission was 5 banks, not 1 — see
  "Scope on investigation" below; fixed with a derived oracle so it cannot recur)

## Observation

**Symptom.** The shipped `ferrosintesis` README presents the non-CC0 sample-bank
licensing inventory at `crates/ferrosintesis/README.md:191-221`, but it does not mention
`ferrosintesis-samples-ccby`, the Rhodes and dulcimer recordings, their two authors, or
their required CC-BY 4.0 notice.

**Expected.** A distributor following the parent crate's licensing guide can discover
and reproduce every required attribution for the default embedded sample set.

**Actual.** The default `embedded-samples` feature includes
`ferrosintesis-samples-ccby` at `crates/ferrosintesis/Cargo.toml:32-37`, with the
dependency declared at line 72. The parent package include list carries only its own
README and MIT/Apache licences. The dependency's correct `NOTICE` is packaged by the
asset crate, but it is not surfaced by the parent guide that downstream binary
distributors are most likely to follow. A distributor can therefore miss the required
credits.

This is a compliance risk, not a claim that
`crates/ferrosintesis-samples-ccby/NOTICE` itself is invalid.

## Fix

Add the CC-BY sample crate, both credited authors, and a link to its notice to the
parent README's licensing inventory. State explicitly which third-party notices binary
distributors must reproduce. Prefer generating or validating a consolidated
third-party notice from the default non-CC0 dependency set so a future sample crate
cannot be omitted silently.

## Notes

- The asset crate's own `Cargo.toml:10` correctly packages `NOTICE`,
  `PROVENANCE.md`, README, source, and samples.
- No existing bug or open requirement matched this specific attribution omission.
- No external legal conclusion was made; the review checked only repository contents.

## Scope on investigation: five banks were omitted, not one (2026-07-24)

The report named `ferrosintesis-samples-ccby`. Enumerating the `embedded-samples`
feature list and reading each bank's declared `license` field showed the guide omitted
**five** of the **ten** attribution-bearing banks a default build embeds:

| Crate | Licence |
|---|---|
| `ferrosintesis-samples-headroom` | CC-BY-4.0 |
| `ferrosintesis-samples-musescore-grand` | MIT |
| `ferrosintesis-samples-dark-salamander` | CC-BY-3.0 |
| `ferrosintesis-samples-ydp-grand` | CC-BY-3.0 |
| `ferrosintesis-samples-ccby` | CC-BY-4.0 |

The five named in the guide (`clavinet`, `musescore`, `grand`, `gong`, `sax`) were
correct. The other eleven default banks are CC0-1.0 and require nothing. So the
compliance gap was 50% of the attribution-bearing set — the reporter found the newest
instance of a systemic drift, not a one-off.

Two further stale claims in the same section were corrected: it said "366 embedded
recordings" where the real total across the 21 default banks is **1036**, and
`lib.rs::embedded_samples_available`'s doc comment still described "the two sample
packages".

## Fix as landed

- `crates/ferrosintesis/README.md` — the licensing section is now a table of all ten
  attribution-bearing banks with licence, what each supplies, and the exact credit,
  plus an explicit "If you distribute a binary" instruction. The brittle recording
  count is gone; the per-crate inventory under `tools/ferrosintesis-samples/` is named
  as the authority.
- `crates/ferrosintesis/NOTICE` (new) — a consolidated third-party notice, grouped by
  licence, naming all ten banks and their required credits. **The published crate
  previously shipped no notice at all**: the asset crates' own `NOTICE` files are not
  part of the parent's package, and its `include` list carried only the README and the
  two code licences. A binary distributor following the crate therefore had nothing to
  reproduce. Three sibling `PROVENANCE.md` files already pointed at
  "`../ferrosintesis` for how the credit flows to downstream users" — a dangling
  reference until now.
- `crates/ferrosintesis/Cargo.toml` — `NOTICE` added to `include`, so it actually
  ships. Confirmed with `cargo package -p ferrosintesis --list`.
- `crates/ferrosintesis/src/licensing.rs` (new, `#[cfg(test)]`) — the regression
  coverage, and the reason this cannot recur. It derives the attribution-bearing set
  from the `embedded-samples` feature list plus each bank's own `license` field, then
  asserts (a) the README names every one of them, (b) the parent `NOTICE` names every
  one of them and is packaged, and (c) each bank ships a `NOTICE` its own `include`
  list packages.

**Fails-before / passes-after, observed:** on the pre-fix tree
`readme_names_every_attribution_bearing_sample_bank` fails, listing exactly the five
banks above. With `crates/ferrosintesis/NOTICE` moved aside,
`parent_notice_is_packaged_and_names_every_attribution_bearing_bank` fails. After the
fix all three pass. `cargo clippy -p ferrosintesis --all-targets -- -D warnings` and
`cargo fmt --check` are clean.

The oracle reads the feature list as *text* rather than using `cfg!(feature = ...)`, so
it asserts the same thing under `--no-default-features` — deliberately avoiding the
silently-vanishing-oracle failure mode of MM-BUG-KILN-00020.

**Not asserted:** whether each bank's declared licence is *correct* for the PCM it
ships. That is a provenance question for `PROVENANCE.md` and its pinned hashes, not
something a text oracle can settle.

