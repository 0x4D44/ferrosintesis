# MM-BUG-KILN-00250 — Honky-tonk package still documents WAV keys and bytes after FLAC conversion

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** honky-tonk sample crate / public package contract
- **Raised:** 2026-08-17T01:05:10Z
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
- **State history:** Open (2026-08-17T01:05:10Z, raised via `deltic bugs new`)

## Observation

Static review found that the published package contract still describes the
pre-migration WAV bank. `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\crates\ferrosintesis-samples-honkytonk\README.md:7-9`
says nine mono WAVs are embedded,
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\crates\ferrosintesis-samples-honkytonk\PROVENANCE.md:11-14,42-46`
calls the committed and generated payloads WAVs, and
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\crates\ferrosintesis-samples-honkytonk\NOTICE:4-6`
calls the embedded samples WAVs. The actual public exact-name lookup at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\crates\ferrosintesis-samples-honkytonk\src\lib.rs:12-57`
contains only `.flac` keys and FLAC bytes.

A caller following the shipped format contract can request a former `.wav` key
and receive `None`, or pass the actual bytes to a WAV-only consumer. Expected:
README, provenance, notice, and lookup documentation describe the keys and
container actually shipped, or the crate deliberately preserves and documents a
compatibility contract. Actual: the current in-repo sampler works because it uses
the new `.flac` names, but the published package contract is stale. Concrete fix:
choose the supported compatibility contract, update all package-local documents
together, and add a source-derived guard proving every documented key resolves and
that the documented container matches the packaged inventory. Static review only;
no app, test, build, decoder, generator, package command, or exploratory harness ran.

## Fix

<unfixed — raised only>

## Notes

This is the Honkytonk counterpart of open `MM-BUG-KILN-00238`,
`MM-BUG-KILN-00243`, and `MM-BUG-KILN-00247`, which cover separately published
sample crates. Draft `MM-REQ-KILN-00186` covers independent payload/root
verification, not the public container and lookup contract.
