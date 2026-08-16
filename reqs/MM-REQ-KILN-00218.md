# MM-REQ-KILN-00218 — Generated legal pointers must name only packaged documents

- **State:** Draft
- **Priority:** Could
- **Area:** sample crate generation / legal document packaging
- **Raised:** 2026-08-16T12:39:12Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-08-16T12:39:12Z, raised via `deltic reqs new`)

## Statement

Generated sample-crate legal pointers must name exactly the legal and provenance
documents included in that crate's published package.

The acceptance oracle must parse the Cargo `[package] include` entries rather
than search the whole manifest as text. It must reject a fixture where `NOTICE`
appears only in a description or comment while the include list packages only
`PROVENANCE.md`.

## Notes

Current sample manifests are correct; this is prevention debt in the shared
generator. `tools/ferrosintesis-samples/gen_crate_lib.py:22-37` decides a document
ships when its filename occurs anywhere in `Cargo.toml`. A decoy mention can
therefore make generated rustdoc point to a file excluded from crates.io. The
existing generator fixture checks an absent name, not a misleading manifest
mention. The invariant matters across every generated sample crate because this
pointer is the package consumer's route to legal obligations.

Proposed effort: Small.
