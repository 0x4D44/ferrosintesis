# MM-BUG-KILN-00068 — ferrosintesis and -sax license fields do not disclose the embedded non-MIT/Apache audio

- **State:** Open
- **Priority:** Should
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
- **State history:** Open (2026-07-24, raised by Claude Opus 4.8 from the licence audit
  run while fixing KILN-00060; two independent review agents flagged the parent field)

## Observation

**Symptom.** A tool or distributor reading only crate *metadata* — not the README or
NOTICE — is told `ferrosintesis` is `MIT OR Apache-2.0`, and learns nothing about the
attribution-bearing audio a default build embeds.

**Two instances.**

1. `crates/ferrosintesis/Cargo.toml:7` declares `license = "MIT OR Apache-2.0"`, while
   its default `embedded-samples` feature (lines 15-40) pulls in ten banks licensed MIT,
   CC-BY-3.0 or CC-BY-4.0. The declared expression covers the *code* accurately, but a
   default binary embeds audio the field does not disclose. Licence-scanning tooling
   (`cargo-deny`, `cargo-about`, SBOM generators) reads this field.

2. `crates/ferrosintesis-samples-sax/Cargo.toml` declares only `CC-BY-4.0`, but its own
   `NOTICE` and `PROVENANCE.md` both record a second layer: the underlying MTG
   good-sounds recordings published on Freesound are **CC BY 3.0**. An expression such
   as `CC-BY-4.0 AND CC-BY-3.0` would carry both obligations.

**Expected.** Crate metadata alone should not understate the licence obligations of the
bytes the crate ships.

**Not in dispute.** KILN-00060 landed the human-readable disclosure (the README table
and a consolidated `crates/ferrosintesis/NOTICE`). This bug is only about the
machine-readable `license` field.

## Fix

Needs a judgement call from Arthur before implementation, because changing the declared
licence expression of a **published crates.io crate** is a distribution-semantics
decision with downstream effects — dependents' licence gates can start failing on a
version bump.

Options, in rough order of preference:

- Leave `ferrosintesis`'s field as the code licence and rely on the new `NOTICE` +
  README (defensible: the field conventionally describes the crate's own source, and
  the samples live in separately-licensed dependency crates that each declare
  correctly). If chosen, close this as "working as intended" and record the reasoning.
- Or move to an explicit compound expression and accept the downstream churn.
- The `-sax` case is narrower and lower-risk: that crate is not the one downstreams
  gate on, and `CC-BY-4.0 AND CC-BY-3.0` is simply more accurate.

## Notes

- Source-confirmed from the manifests and the two attribution files; no external legal
  conclusion was drawn.
- Deliberately raised rather than fixed inside KILN-00060: that bug's scope was the
  attribution *guide*, and silently changing a published crate's licence expression is
  not a call to make unattended.
