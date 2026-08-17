# MM-BUG-KILN-00254 — MuseScore-grand regeneration command leaves the embedded FLAC bank stale

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** MuseScore grand sample crate / deterministic regeneration
- **Raised:** 2026-08-17T02:30:02Z
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
- **State history:** Open (2026-08-17T02:30:02Z, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

The package documents `python3 tools/ferrosintesis-samples/prepare.py --only=musescoregrand` as its regeneration command at crates/ferrosintesis-samples-musescore-grand/README.md:14-15 and PROVENANCE.md:49-53. `_bake_musescore_grand` validates and writes `musescoregrand_*.wav` names at tools/ferrosintesis-samples/prepare.py:4643-4665, and the validator at :5419-5423 ignores existing FLAC files. The active package instead embeds only `.flac` files at crates/ferrosintesis-samples-musescore-grand/src/lib.rs:14-111, and runtime consumes those names at crates/ferrosintesis/src/sampler.rs:1572-1596. Following the documented command on the current FLAC-only tree therefore leaves all 25 runtime payloads stale and writes 25 unconsumed WAVs beside them; the crate inventory then sees 50 sample files against FILE_COUNT=25. Expected: the scoped command replaces and verifies the exact final-format bank runtime consumes. Actual: it produces a second, unconsumed container set and leaves playback unchanged. Concrete fix: generate, encode, and verify the final FLAC set in empty staging, reject mixed formats before any publication, replace the active bank, and refresh the generated inventory. Add a negative fixture starting from the current FLAC-only tree. Sibling bugs MM-BUG-KILN-00239, 00244, 00248, and 00251 cover other independent sample packages. Static review only; the command was not run. Estimated effort: Medium.

## Fix

<unfixed — raised only>

## Notes
