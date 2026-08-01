# MM-BUG-CRUCIBLE-00014 — amp-lab sequencer violates its first-tempo contract

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** amp-lab / sequencer
- **Raised:** 2026-08-01
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260801T062615Z-p40124-n250195500-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00014-run-fix-20260801T062615Z-p40124-n250195500-c1
- **Owner base:** 9b325c9277e22e714a7c11aee2cda6812e737781
- **Owner fingerprint:** -
- **Owner since:** 2026-08-01T06:26:15Z
- **Owner until:** 2026-08-01T08:26:15Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol xhigh from a static multi-lens review; Deltic mint was sandbox-blocked, so the ID was allocated per `bugs/README.md`)

## Observation

`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\crates\amp-lab\src\seq.rs:53`
promises that the first Set-Tempo governs this constant-tempo parser. Instead, every
Set-Tempo overwrites `tempo_us` at line 108, and lines 138-159 apply the final physically
scanned value to every event and the loop length. With two tempo events, earlier events
are retroactively retimed; format-1 track order can also change which value wins.

Expected: honour the documented first tempo or reject later tempo events explicitly.
Actual: the last scanned tempo silently wins globally. The committed loop currently
authors one tempo, so current playback is unaffected. This pass did not execute a probe.

## Fix

Reject a second Set-Tempo with a descriptive error, matching the deliberately
constant-tempo scope, or retain only the first if that is the intended contract. Add a
two-tempo format-0 test and a format-1 track-order test for the chosen rule.

## Notes

Confirmed by the correctness and maintainability lenses and the devil's advocate. The
main synth's historical tempo-map bugs do not cover this independent parser.
