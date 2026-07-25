# MM-BUG-KILN-00111 — Changing one manifest field removes a sample crate from every attribution oracle

- **State:** Fixed
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
- **State history:** Open (2026-07-25, raised by Claude Opus 4.6 from an adversarial review of the licensing oracles while landing MM-REQ-KILN-00029) → Fixed (2026-07-25, Codex GPT-5.6-Sol; all attribution oracles now derive the obligation from packaged provenance and reject a conflicting manifest declaration; awaiting independent two-eyes verification)

## Observation

`crates/ferrosintesis/src/licensing.rs:109-111` decides which crates the attribution oracles
apply to:

```rust
fn requires_attribution(license: &str) -> bool {
    license != "CC0-1.0"
}
```

The `license` it reads is the crate's **own declared `license` field**, and all three
oracles `continue` past any crate that fails the predicate (`licensing.rs:220-223`,
`:310-313`, `:363-366`).

**Expected.** Removing a CC-BY bank's attribution turns something red.

**Actual.** Editing `license = "CC-BY-4.0"` to `license = "CC0-1.0"` in
`crates/ferrosintesis-samples-ccby/Cargo.toml` silently removes that crate from README
coverage, from parent-NOTICE coverage, **and** from the ships-a-NOTICE check — three
oracles at once, with nothing red anywhere. `inventory.rs` does not backstop it: its checks
(`crates/ferrosintesis/src/inventory.rs:87`, `:119`) only require each packaged WAV to be
*mentioned* by the crate's own documents, never what licence applies.

The subject of the guard therefore selects whether the guard applies to it. Every use of
`declared_license` is inside `licensing.rs` (`:89`, `:220`, `:310`, `:363`) and nothing
cross-checks the declaration against the crate's actual provenance.

This is not hypothetical bookkeeping: the two Freesound CC-BY banks are the ones with a real
third-party obligation, and `licensing.rs:22-27` explicitly disclaims checking whether a
declared licence is *correct* for the PCM it ships. That disclaimer is defensible on its own
— a text oracle cannot settle provenance — but combined with this, a single-token edit can
switch the obligation off with no independent record contradicting it.

**Observed by reading the source and grepping every use of `declared_license`; the mutation
itself was reasoned through, not applied to the tracked tree.**

## Fix

Implemented in `crates/ferrosintesis/src/licensing.rs`. Each attribution oracle now reads
the sample crate's packaged `PROVENANCE.md`, recognizes the repository's supported
attribution-bearing licence vocabulary, and derives the obligation from that independent
record. It then asserts that the crate's manifest declaration agrees before deciding
whether to check the README or notices. The enumeration remains derived; there is no list
of attribution-bearing crates.

The adversarial regression pins the original one-token mutation: a `CC0-1.0` manifest
declaration disagrees with provenance recording CC BY 4.0 and therefore cannot exempt the
crate. Before the fix, the test failed because the manifest compared only with itself. All
25 current default sample crates agree with their provenance records.

Validation on 2026-07-25:

- Five licensing tests, including the manifest self-exemption regression: passed.
- The same five tests under `--no-default-features`: passed.
- The same five tests on Rust 1.87: passed.
- `cargo clippy -p ferrosintesis --lib --tests -- -D warnings`: passed.

## Notes

- Related: MM-BUG-KILN-00110 (a crate's own name counts as a credit token). 00110 weakens
  the check for crates still inside the net; this one lets a crate leave the net entirely.
- No crate in the tree currently misdeclares its licence — this is about the absence of a
  guard, not a present compliance failure.
