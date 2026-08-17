# MM-BUG-KILN-00263 — Banjo extractor and its required tests cannot consume the migrated FLAC inventory

- **State:** Open
- **Priority:** Must
- **Severity:** Medium
- **Area:** orchestral2 banjo regeneration / required test gate
- **Raised:** 2026-08-17T04:26:00Z
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
- **State history:** Open (2026-08-17T04:26:00Z, raised via `deltic bugs new`)

## Observation

The standalone banjo recipe published at
`crates/ferrosintesis-samples-orchestral2/PROVENANCE.md:10-14` still models a WAV
bank. `tools/ferrosintesis-samples/banjo_extract.py:40` selects `banjo_*.wav`, and
`_sample_crate_banjo_files` at lines 57-66 accepts only a `.wav` name found on the
same source line as `include_bytes!`. The current crate table uses FLAC names and
rustfmt may split the name from the macro (`src/lib.rs:18-71`); the sampler also
declares 24 FLAC keys at `crates/ferrosintesis/src/sampler.rs:2695-2718`.

`expected_banjo_files()` therefore obtains an empty crate set and a 24-name sampler
set, then raises the inventory-mismatch error at `banjo_extract.py:83-95`. The
command does not reach a valid publication, and even its staging/output names at
lines 205-215 and 306-309 remain WAV-only. The committed publication tests call
that failing function during every `setUp` at
`tools/ferrosintesis-samples/test_banjo_extract.py:26-41`, before any test body;
unittest discovery is required at `.deltic-integrate.toml:59,71`.

Expected: the documented extractor regenerates and atomically publishes the exact
24-file FLAC bank, and its tests initialize against the current inventory. Concrete
fix: derive the canonical inventory without depending on rustfmt line layout,
stage/encode/verify FLAC outputs, reject stale opposite-container files, and add
negative coverage for split table formatting plus a stale WAV-only inventory.
Static source review only; no extractor, test, decoder, app, render, or exploratory
harness ran.

## Fix

<unfixed — raised only>

## Notes

This is independent of `MM-BUG-KILN-00262`: banjo has a standalone extractor,
inventory parser, atomic publisher, and test module rather than the generic
non-banjo path.
