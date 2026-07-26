# MM-BUG-KILN-00149 — Parent sample inventory mislabels MuseScore grand as GM0 instead of GM1 CC0=2

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sample routing documentation
- **Raised:** 2026-07-26
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
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

Static reproduction:

1. The parent distribution table calls `ferrosintesis-samples-musescore-grand` a `GM 0 grand` at `crates/ferrosintesis/README.md:233`; the parent notice repeats `GM 0 grand piano` at `crates/ferrosintesis/NOTICE:26`.
2. The routing source accepts this bank only inside the program `1` arm and only for CC0=2 at `crates/ferrosintesis/src/altbank.rs:1046-1075`.
3. The crate module docs, manifest, README, provenance, generator, and sampler all correctly identify it as GM 1 Bright Acoustic alternate CC0=2.

Expected: parent documentation identifies the embedded bank as GM 1 Bright Acoustic, CC0=2, matching the shipped selector.

Actual: both parent-facing references classify it as GM0. A maintainer or MIDI author relying on the parent inventory associates the asset and its attribution with the wrong program; GM0 CC0=2 routes to the Salamander bank instead.

The existing derived selector/documentation oracle covers only `voices::GM0_SOURCES` (`crates/ferrosintesis/src/altbank.rs:1317-1363`), so this non-GM0 parent drift is unguarded. No application, build, test, render, generator, or exploratory harness ran.

## Fix

Correct both parent references to identify the bank as GM 1 Bright Acoustic,
CC0=2. Add a derived GM1 alternate-bank documentation regression rather than a
new hand-maintained list: cover the YDP bank at CC0=1 and MuseScore grand at
CC0=2, including the parent README/NOTICE claims, and prove an unknown GM1 bank
falls back to the model.

Estimated effort: Small.

## Notes

Closed `MM-BUG-KILN-00122` fixed stale selector claims inside individual sample
crates and added a GM0-only guard. This is a residual on parent documentation
outside that guard, not a duplicate of the corrected crate-local claims.
