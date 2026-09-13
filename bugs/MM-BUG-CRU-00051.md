# MM-BUG-CRU-00051 — Kawai package documents WAV output and a pure-stdlib rebake although it ships FLAC and requires ffmpeg

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** Kawai sample crate / packaged regeneration documentation
- **Raised:** 2026-08-20T15:01:05Z
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
- **State history:** Open (2026-08-20T15:01:05Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:17:15Z, deltic:auto role=fix run=fix-20260913T151224Z-aacaf3e2 branch=task/bug-MM-BUG-CRU-00051-run-fix-20260913T151224Z-aacaf3e2 code=782d661527539a1d1958fb6d2d47b9984461757c gate=manual) -> Closed (2026-09-13T19:59:17Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: Kawai docs now describe FLAC output and pinned ffmpeg; the test's negation blindness split to MM-BUG-CRU-00061)

## Observation

Static review found that the independently published Kawai package still describes its
pre-migration WAV contract. `D:\worktrees\ferrosintesis\20260820-REV-MM-CDX@CRUCIBLE-code-review-153056\crates\ferrosintesis-samples-vcsl-kawai\README.md:7-15`
says 32 WAVs back the logical names and tells maintainers to “Regenerate the WAVs.”
`D:\worktrees\ferrosintesis\20260820-REV-MM-CDX@CRUCIBLE-code-review-153056\crates\ferrosintesis-samples-vcsl-kawai\PROVENANCE.md:9-16`
says the packaged `samples/` files are WAV source, while lines 55-69 say the recipe
outputs a mono WAV and is “Pure stdlib (plain WAV, no ffmpeg).”

The package actually contains 32 `.flac` files and no WAVs; its generated table embeds
only FLAC names at
`D:\worktrees\ferrosintesis\20260820-REV-MM-CDX@CRUCIBLE-code-review-153056\crates\ferrosintesis-samples-vcsl-kawai\src\lib.rs:15-144`.
The documented command reaches `_require_ffmpeg()` before selector processing at
`D:\worktrees\ferrosintesis\20260820-REV-MM-CDX@CRUCIBLE-code-review-153056\tools\ferrosintesis-samples\prepare.py:5669-5671`,
and the shared publisher encodes the finished bank as FLAC at `prepare.py:4412-4452`.
A clean host that follows every packaged prerequisite therefore fails immediately when
ffmpeg is absent. A package auditor is also told the wrong physical container.

Expected: the packaged README and provenance distinguish upstream/logical WAV names from
the physical FLAC bank and name every executable the documented recipe requires. Actual:
they promise a WAV, Python-only workflow that no longer exists. Open
`MM-BUG-CRUCIBLE-00042` already covers the Kawai NOTICE's stale “embedded WAV” sentence;
`MM-BUG-CRUCIBLE-00039` covers encoder-version-dependent FLAC bytes; and
`MM-BUG-CRU-00047` covers the analogous grand-package prerequisite. None covers these
Kawai README/PROVENANCE claims. Static review only; no generator, app, build, test,
decoder, package command, render, network request, or exploratory harness ran. Estimated
effort: Small.

## Fix

<unfixed — raised only>

Update the README and provenance together. Call the package payloads FLAC, retain `.wav`
only where it really names an upstream or logical recording, describe the final output as
mono 16-bit 44.1 kHz PCM stored losslessly in FLAC, and require ffmpeg on `PATH`. Extend a
filesystem-derived packaged-document oracle so every generated bank's documented
container and recipe prerequisites follow the live publisher instead of a hand-maintained
crate list. Coordinate the separate NOTICE sentence through `MM-BUG-CRUCIBLE-00042`.

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `782d6615`, earlier FLAC prose in `db16a45b`) by an agent other than the fixer.

**Original observation re-derived.** The Kawai README and PROVENANCE no longer say "Pure stdlib (plain WAV, no ffmpeg)" or "Output: 16-bit mono WAV"; they state FLAC output and ffmpeg 8.1.1 on PATH. `samples/` holds 32 `.flac`; `want("kawai")` exists and the ffmpeg pin gate applies; "Python's stdlib handles WAV decoding and DSP" matches `read_wav`.

**Fails-before (method B).** Reversing the hunk fails `KawaiPackagedDocumentContractTest` in 3 subtests. Restored; passes on HEAD.

**Residual split to MM-BUG-CRU-00061.** The same ffmpeg-near-PATH regex accepts "does not need ffmpeg on `PATH`".

## Notes
