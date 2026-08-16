# MM-BUG-KILN-00243 — Grand sample API still documents WAV keys and bytes after FLAC conversion

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** grand sample crate / public lookup contract
- **Raised:** 2026-08-16T22:56:37Z
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
- **State history:** Open (2026-08-16T22:56:37Z, raised via `deltic bugs new`)

## Observation

The published `get` contract says it returns WAV bytes and that callers must use
case-sensitive `.wav` names at
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-234326\crates\ferrosintesis-samples-grand\src\lib.rs:235-237`.
Every key in the embedded table is now `.flac`, so a caller following that contract,
for example `get("grand_C4_mf.wav")`, receives `None`; the in-repo consumer succeeds
only because it uses the undocumented `.flac` spelling.

The packaged README repeats the WAV claim at
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-234326\crates\ferrosintesis-samples-grand\README.md:3-5`,
and `PROVENANCE.md:9-15,51-64` still describes WAV output and the pre-conversion
7,184,592-byte aggregate. The committed bank is 54 FLAC files totaling 2,361,631
bytes. Expected: published API and provenance describe the keys and bytes actually
shipped. Actual: the documented lookup key fails and the format/size audit trail is
stale. Static review only; no app, build, test, decoder, or exploratory harness ran.

## Fix

<unfixed — raised only. Update rustdoc, README, and provenance to the FLAC contract
and current aggregate; add a source-derived assertion that a documented real key
resolves and that format claims cannot drift from the packaged inventory.>

## Notes

This is the grand-crate counterpart of open `MM-BUG-KILN-00238`, which covers the
separate gong crate. It is not a duplicate because each published crate owns an
independent API and documentation surface.
