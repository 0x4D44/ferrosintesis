# MM-BUG-CRUCIBLE-00014 — amp-lab sequencer violates its first-tempo contract

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** amp-lab / sequencer
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
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol xhigh from a static multi-lens review; Deltic mint was sandbox-blocked, so the ID was allocated per `bugs/README.md`) -> Fixed (2026-08-01T06:35:18Z, deltic:auto role=fix run=fix-20260801T062615Z-p40124-n250195500-c1 branch=task/bug-MM-BUG-CRUCIBLE-00014-run-fix-20260801T062615Z-p40124-n250195500-c1 code=d4a7176771cda032103643d3f28d092f75bcd348 gate=manual) -> Closed (2026-08-01, independently verified by Claude Opus 5 on trunk d332b93; fixer was OpenAI GPT-5 Codex)

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

### Verification summary (2026-08-01, Claude Opus 5, independent)

Verified on trunk `d332b93` in worktree
`D:\worktrees\ferrosintesis\20260801-TSK-HUM-bug-verify-crucible-14`.

**Original observation reproduced as a measurement.** The report inferred from
source that "the last scanned tempo silently wins globally". I reverted only the
new rejection (back to `tempo_us = Some(value)`) and parsed a format-0 file with
Set-Tempo 500000 then 600000 and a note at tick 480. The pre-fix parser placed
that note at **frame 26460** — 0.600 s at 44.1 kHz, the *second* tempo. The first
tempo the docstring promised would have put it at 22050. Earlier events are indeed
retimed by a later tempo, and the loop length moved with it (52920 frames).

**Root cause addressed by narrowing the contract, not by guessing a tempo map.**
`tempo_us` became `Option<f64>` and a second Set-Tempo returns a descriptive error;
`unwrap_or(500_000.0)` keeps the documented 120 bpm default for a file that
authors none. That is one of the two resolutions the bug's own Fix section
allowed, and it matches the parser's deliberately constant-tempo scope.

**Fails-before proved for both regressions.** With the rejection reverted,
`two_tempo_format_zero_file_is_rejected` and
`tempo_in_multiple_format_one_tracks_is_rejected_in_either_order` both failed with
"two tempos must be rejected". Restoring `seq.rs` (md5 `2d1a9bd0…`) turned them
green. The format-1 test covers both track orders, which is what closes the
"track order can change which value wins" half of the report.

**Gates** (amp-lab is its own workspace, so these run from `crates/amp-lab/`):
`cargo test` 36 pass / 0 fail — including the shipped-loop oracles, so the real
`assets/backing.mid` still parses under the stricter rule; `cargo clippy
--all-targets -- -D warnings` clean; `cargo fmt -- --check` clean.

## Notes

Confirmed by the correctness and maintainability lenses and the devil's advocate. The
main synth's historical tempo-map bugs do not cover this independent parser.
