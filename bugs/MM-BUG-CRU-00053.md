# MM-BUG-CRU-00053 — YDP regeneration falsely claims to require no ffmpeg

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** YDP sample package / regeneration documentation
- **Raised:** 2026-08-20T15:50:56Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260913T152133Z-9adb0a87
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00053-run-fix-20260913T152133Z-9adb0a87
- **Owner base:** ef5a9a2fc7300990a6ab73c122d0a09710e3bea6
- **Owner fingerprint:** -
- **Owner since:** 2026-09-13T15:21:33Z
- **Owner until:** 2026-09-13T17:21:33Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-20T15:50:56Z, raised via `deltic bugs new`)

## Observation

Static code review of crates/ferrosintesis-samples-ydp-grand/.

Observation: PROVENANCE.md:52-58 documents `python3 tools/ferrosintesis-samples/prepare.py --only=ydpgrand` and then states "Pure stdlib (raw-PCM SF2 — no ffmpeg)." The extraction itself is stdlib, but the documented command is not: tools/ferrosintesis-samples/prepare.py:5669-5671 calls `_require_ffmpeg()` before family work, and publish_pending_banks at prepare.py:4412-4450 uses ffmpeg to encode and verify the final FLAC files. On a host with Python but no ffmpeg, the documented regeneration command exits instead of rebuilding the bank.

Expected: packaged regeneration instructions name every required executable and distinguish stdlib SF2 extraction from mandatory FLAC publication.

Actual: the package explicitly promises no ffmpeg although the command refuses to run without it.

Concrete fix: change README.md and PROVENANCE.md to require ffmpeg on PATH, describe FLAC output, and retain the narrower fact that parsing/extraction of the raw-PCM SF2 uses stdlib rather than ffmpeg. Add a documentation/source oracle that rejects a "no ffmpeg" claim for any recipe reaching `_require_ffmpeg()`.

Static review only. No generator, test, build, app, render, network, or exploratory harness ran. Estimated effort: Small. Existing MM-BUG-CRU-00047 covers the separate grand package, not this YDP package; no YDP-specific duplicate was found.

## Fix

<unfixed — raised only>

## Notes
