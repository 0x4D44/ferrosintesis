# MM-BUG-CRUCIBLE-00016 — amp-lab non-f32 fallback selects the maximum sample rate

- **State:** Closed
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
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol xhigh from a static multi-lens review; Deltic mint was sandbox-blocked, so the ID was allocated per `bugs/README.md`) -> Fixed (2026-08-01T06:46:43Z, deltic:auto role=fix run=fix-20260801T063556Z-p69260-n044641400-c1 branch=task/bug-MM-BUG-CRUCIBLE-00016-run-fix-20260801T063556Z-p69260-n044641400-c1 code=4a43c844649dba176c9ac79534a14a498663c55a gate=manual) -> Closed (2026-08-01, independently verified by Claude Opus 5 on trunk 63fee98; fixer was OpenAI GPT-5 Codex)

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

### Verification summary (2026-08-01, Claude Opus 5, independent)

Verified on trunk `63fee98` in worktree
`D:\worktrees\ferrosintesis\20260801-TSK-HUM-bug-verify-crucible-16-17`.

**Original observation reproduced as a number.** The fix extracts the policy into a
pure `choose_f32_sample_rate(default_rate, ranges)`. I replaced its body with the
pre-fix rule — first f32 range, `with_max_sample_rate()` — and ran the new test:
for the reported device shape (f32 range 8 kHz-192 kHz, device default 44.1 kHz) it
returned **`Some(192000)`** where the fix returns `Some(44100)`. That is exactly
"chooses the maximum rather than the device default", measured rather than inferred.
Restoring `audio.rs` (md5 `6dd06894…`) turned it green.

**Policy checked against the bug's stated expectation**, case by case: device default
when supported; else 48 kHz, else 44.1 kHz; else the nearest range boundary, with
ties broken toward the lower rate (50 kHz between `(32k,40k)` and `(60k,96k)` picks
40 kHz — less synth work, and what the test pins). Empty range list returns `None`,
so the "no f32 configuration" error still fires.

**Scope of this verification, stated honestly.** The extracted helper is what I
exercised. The device path in `start()` needs real audio hardware, so I did not run
it, and — as the bug itself asks — no xrun or audibility claim is made either way.

**Gates** (amp-lab is its own workspace, so these run from `crates/amp-lab/`):
`cargo test` 43 pass / 0 fail; `cargo clippy --all-targets -- -D warnings` clean;
`cargo fmt -- --check` clean.

## Notes

Confirmed by the reliability lens and the devil's advocate. Only the rate-selection
policy is confirmed; audible failure is not.
