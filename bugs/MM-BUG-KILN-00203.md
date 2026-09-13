# MM-BUG-KILN-00203 — Accent-cymbal audio oracle admits silent and click-only assets

- **State:** Closed
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
- **State history:** Open (2026-08-16T07:17:00Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:00:05Z, deltic:auto role=fix run=fix-20260913T145322Z-8da22b38 branch=task/bug-MM-BUG-KILN-00203-run-fix-20260913T145322Z-8da22b38 code=ba9b3ff224b19c6c786f705d52678b9d4eff2a7a gate=manual) -> Closed (2026-09-13T19:35:03Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: restoring the peak-only rule fails the silent/impulse controls; the hand-maintained per-bank duration table is split to MM-BUG-CRU-00073)

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

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `ba9b3ff2`) by an agent other than the fixer.

`decoded_banks_are_valid_audio` checks CRASH, SPLASH and CHINA with duration, a 0.85-0.92 peak band and RMS > 0.01; silent-splash and single-impulse controls are rejected.

**Fails-before (method B).** Restoring the `peak > 16_000` predicate and disabling the RMS floor fails `decoded_audio_oracle_rejects_silent_and_impulse_controls` ("single-impulse crash PCM must be rejected"). Restored; both pass on HEAD.

**Residual split to MM-BUG-CRU-00073.** Dropping SPLASH from the per-bank duration table leaves `decoded_banks_are_valid_audio` green: the table is hand-maintained beside `BANKS`, the same omission class.

## Notes

Raised by the 2026-08-16 static review of
`crates/ferrosintesis-samples-drumkit2/`. Estimated effort: Small.
