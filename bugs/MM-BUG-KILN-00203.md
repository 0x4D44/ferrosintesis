# MM-BUG-KILN-00203 — Accent-cymbal audio oracle admits silent and click-only assets

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / drumkit2 audio validation
- **Raised:** 2026-08-16T07:17:00Z
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
- **State history:** Open (2026-08-16T07:17:00Z, raised via `deltic bugs new`)

## Observation

The test named `decoded_banks_are_valid_audio` does not prove that every routed
accent-cymbal asset contains valid audio.

At
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-075555\crates\ferrosintesis-samples-drumkit2\src\lib.rs:455`,
the validation table contains only `CRASH` and `CHINA`; routed `SPLASH` is absent.
For the two covered banks, lines 467-468 require only one sample above 16,000.
The other crate tests check names, RIFF/WAVE magic, aggregate byte count, index
resolution, and nonempty PCM, but no signal-energy floor.

Two static negative controls therefore stay green:

1. Replace each splash data chunk with same-length zero PCM. File names, headers,
   duration, aggregate size, and nonempty decoded slices remain valid, while GM
   key 55 renders silence.
2. Replace a crash or china data chunk with zeros except for one sample at 16,001.
   The duration and peak checks pass although the asset is only a click.

Expected: every bank in `BANKS` must satisfy its documented duration, normalized
peak, and non-silence bounds.

Actual: one routed bank is omitted and the covered-bank predicate admits
click-only PCM. All 36 current WAVs were statically inspected and are healthy;
this is a false-green oracle defect, not a claim of current asset corruption.

## Fix

Validate every bank, including `SPLASH`, from one per-bank duration table. Match
the core drum-kit oracle's meaningful signal checks: require the generator's
normalized peak range (about 0.85-0.92) and an RMS floor (currently `> 0.01`) for
every take, in addition to duration.

Add adversarial negative controls for a same-length silent splash and a
single-impulse crash or china so both holes are proven red before the fix and
green afterward.

## Notes

Raised by the 2026-08-16 static review of
`crates/ferrosintesis-samples-drumkit2/`. Estimated effort: Small.
