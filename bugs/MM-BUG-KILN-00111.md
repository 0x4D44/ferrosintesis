# MM-BUG-KILN-00111 — Changing one manifest field removes a sample crate from every attribution oracle

- **State:** Open
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
- **State history:** Open (2026-07-25, raised by Claude Opus 4.6 from an adversarial review of the licensing oracles while landing MM-REQ-KILN-00029.)

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

The declaration should be cross-checked against something the crate cannot restate. Since
MM-REQ-KILN-00029 landed, there is now such a thing: `PROVENANCE.md` carries the retained
upstream licence manifests and per-sound licence records, and
`crates/ferrosintesis/src/provenance.rs` already pins every committed source by hash.

Suggested shape: derive the attribution obligation from the crate's **provenance document**
(does it record a non-CC0 upstream licence?) and assert it agrees with the manifest's
`license` field. A disagreement is then a red test rather than a silent exemption. That
keeps the enumeration derived — both sides come from files already required to exist — and
introduces no hand-maintained list of "crates that really do need attribution", which would
inherit the defect it exists to catch.

## Notes

- Related: MM-BUG-KILN-00110 (a crate's own name counts as a credit token). 00110 weakens
  the check for crates still inside the net; this one lets a crate leave the net entirely.
- No crate in the tree currently misdeclares its licence — this is about the absence of a
  guard, not a present compliance failure.
