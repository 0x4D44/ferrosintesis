# MM-BUG-KILN-00264 — Orchestral2 package still documents WAV keys and payloads after FLAC migration

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** orchestral2 sample crate / public package contract
- **Raised:** 2026-08-17T04:26:06Z
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
- **State history:** Open (2026-08-17T04:26:06Z, raised via `deltic bugs new`)

## Observation

Static inspection found that the published crate contract still describes the
pre-migration container and lookup keys. Module rustdoc calls every payload a mono
16-bit 44.1 kHz WAV at
`crates/ferrosintesis-samples-orchestral2/src/lib.rs:1-10`; the `SAMPLES`,
`FILE_COUNT`, and `get()` documentation at lines 14-16 and 407-412 says names use
the `.wav` suffix. `README.md:8-22` and `PROVENANCE.md:3` likewise describe the
packaged bank as WAV. The committed table at `src/lib.rs:17-405` instead contains
132 `.flac` keys and no WAV key.

A standalone consumer following the exact-name public documentation receives
`None` for a documented `.wav` name, and package users and auditors receive the
wrong byte-container contract. Current in-repo runtime lookups already use FLAC;
this is not evidence of current audio corruption. Expected: rustdoc, README, and
provenance accurately name the physical FLAC payloads and accepted lookup keys.
Concrete fix: update those surfaces together, or deliberately provide documented
WAV-name compatibility aliases with an explicit returned-byte format, and add a
source-derived documentation guard tied to the embedded inventory. Static review
only; no app, test, decoder, generator, package command, or exploratory harness ran.

## Fix

<unfixed — raised only>

## Notes

The source-input checksum tables in `PROVENANCE.md` legitimately name WAV source
files and should not be mechanically rewritten.
