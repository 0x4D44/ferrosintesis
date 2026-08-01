# MM-BUG-CRUCIBLE-00016 — amp-lab non-f32 fallback selects the maximum sample rate

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** amp-lab / audio device configuration
- **Raised:** 2026-08-01
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
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol xhigh from a static multi-lens review; Deltic mint was sandbox-blocked, so the ID was allocated per `bugs/README.md`)

## Observation

When the default output format is not f32,
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\crates\amp-lab\src\audio.rs:263`
selects the first f32 range and unconditionally calls `with_max_sample_rate()` at line
276. On a device whose f32 range spans ordinary rates through 96 or 192 kHz, amp-lab
chooses the maximum rather than the device default or a preferred 44.1/48 kHz rate.

Expected: select a normal supported rate nearest the default and report it. Actual: the
fallback can multiply synth work without a stated audio-quality requirement. Actual
xruns are UNVERIFIED because this static pass did not run the app on hardware. This is a
narrow residual of the non-f32 fallback introduced for MM-BUG-KILN-00081.

## Fix

Choose the default rate when it lies in an f32 range; otherwise prefer 48 kHz or 44.1 kHz
when supported, then clamp to the nearest supported rate. Add pure selection tests over
synthetic ranges; keep hardware xrun claims out of the acceptance oracle.

## Notes

Confirmed by the reliability lens and the devil's advocate. Only the rate-selection
policy is confirmed; audible failure is not.
