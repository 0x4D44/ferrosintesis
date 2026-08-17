# MM-BUG-KILN-00258 — MuseScore sample package still documents WAV keys after FLAC conversion

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** MuseScore sample crate / public package contract
- **Raised:** 2026-08-17T03:28:50Z
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
- **State history:** Open (2026-08-17T03:28:50Z, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

Static review found that the independently published package still describes WAV payloads after its bank moved to FLAC. `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-040926\crates\ferrosintesis-samples-musescore\src\lib.rs:7`, line 16, line 141, and line 144 call the assets WAVs and tell callers that lookup names carry a `.wav` suffix; `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-040926\crates\ferrosintesis-samples-musescore\README.md:7` and `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-040926\crates\ferrosintesis-samples-musescore\PROVENANCE.md:3` repeat the WAV claim. The actual `SAMPLES` table at `src\lib.rs:18` embeds only `.flac` keys, so a standalone consumer following the documented contract, for example `get("sitar_E3.wav")`, receives `None`; valid returned bytes are FLAC. Expected: rustdoc, README, provenance, and lookup semantics agree on the shipped container and exact keys. Actual: runtime's in-repo FLAC lookups work, but the public package contract names nonexistent keys and the wrong byte format. Concrete fix: update all package surfaces to FLAC/container-neutral wording or deliberately support compatibility aliases with an explicit returned-byte contract; add a source-derived guard tying documented format and one real lookup key to `SAMPLES`. Sibling bugs for gong, grand, Headroom, Honky-tonk, and MuseScore-grand cover separate published crates. Static review only; no test, build, app, decoder, generator, render, or exploratory harness ran. Estimated effort: Small.

## Fix

<unfixed — raised only>

## Notes
