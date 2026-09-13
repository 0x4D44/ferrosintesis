# MM-BUG-KILN-00269 — Sax regeneration command leaves the embedded FLAC bank stale

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** sax sample crate / deterministic regeneration
- **Raised:** 2026-08-17T06:31:31Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T202621Z-e3282bc0
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00269-run-verify-20260913T202621Z-e3282bc0
- **Owner base:** d676a08827b7486c047f3be22de16d22c5e9dcfe
- **Owner fingerprint:** sha256:866975e58cdae23d469f1b08721d8c6d0917e7b61050579b1efad3245c79e46e
- **Owner since:** 2026-09-13T20:26:21Z
- **Owner until:** 2026-09-13T22:26:21Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T06:31:31Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T17:10:36Z, deltic:auto role=fix run=fix-20260913T170255Z-304e895d branch=task/bug-MM-BUG-KILN-00269-run-fix-20260913T170255Z-304e895d code=c5282f988d2120272e0767369b8109e145470f3c gate=manual)

## Observation

The package documents python3 tools/ferrosintesis-samples/prepare.py --sax-only as its regeneration command at crates/ferrosintesis-samples-sax/README.md:21-22 and PROVENANCE.md:82-90. That path always names and writes sax_*.wav at tools/ferrosintesis-samples/prepare.py:5220-5268, then returns at :5536-5547. The active package instead embeds only 74 .flac files at crates/ferrosintesis-samples-sax/src/lib.rs:15-312, and runtime consumes .flac keys at crates/ferrosintesis/src/sampler.rs:2318-2446. The stale-output validator at prepare.py:5419-5423 scans only .wav names, so following the documented command on the current FLAC-only tree leaves all runtime payloads unchanged and adds 74 unconsumed WAVs; the crate inventory at src/lib.rs:336-365 then sees 148 sample files against FILE_COUNT=74. Expected: the documented scoped workflow replaces and verifies the exact final-format bank runtime consumes, with no duplicate container set. Concrete fix: generate into empty staging, encode and independently verify the canonical FLAC outputs before publication, reject mixed same-stem containers, atomically replace the active bank, and refresh the generated inventory. Add a negative regression starting from the committed FLAC-only package. Static review only; the command was not run. Estimated effort: Medium.

## Fix

<unfixed — raised only>

## Notes
