# MM-BUG-CRUCIBLE-00017 — amp-lab MIDI parser panics or silently accepts truncated tracks

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
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol xhigh from a static multi-lens review; Deltic mint was sandbox-blocked, so the ID was allocated per `bugs/README.md`) -> Fixed (2026-08-01T06:57:56Z, deltic:auto role=fix run=fix-20260801T064737Z-p53296-n060738800-c1 branch=task/bug-MM-BUG-CRUCIBLE-00017-run-fix-20260801T064737Z-p53296-n060738800-c1 code=35ccafa1092ffd1d4611a09c3148c61f71ceea41 gate=manual) -> Closed (2026-08-01, independently verified by Claude Opus 5 on trunk 63fee98; fixer was OpenAI GPT-5 Codex)

## Observation

`Loop::parse` returns `Result`, but malformed track data can panic or silently succeed.
At
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\crates\amp-lab\src\seq.rs:77`,
a missing declared `MTrk` breaks and later returns `Ok`. A track ending after a delta and
status `0xFF` reaches `data[i]` at line 102 with `i == end` and panics. The tempo payload
check at line 108 uses the whole file length instead of the current track end, allowing a
read into the next chunk; other truncations break without an error.

Expected: malformed declared tracks return a descriptive `Err` through `audio::start`.
Actual: a damaged or partially regenerated embedded asset can crash startup or become an
empty/incorrect loop. Runtime input is compile-time embedded, so this is reliability, not
an external security boundary. The malformed cases were confirmed from bounds and control
flow; this pass did not execute them.

## Fix

Make VLQ, meta, SysEx, and channel-message reads fallible and bounded by the declared
track end. Reject missing/truncated declared tracks. Add regressions for terminal `0xFF`,
truncated VLQ, overlong meta/SysEx payload, and a missing second track.

### Verification summary (2026-08-01, Claude Opus 5, independent)

Verified on trunk `63fee98` in worktree
`D:\worktrees\ferrosintesis\20260801-TSK-HUM-bug-verify-crucible-16-17`.

**The reported panic reproduces literally.** I spliced the six new tests onto the
pre-fix parser (`35ccafa^`) and ran them. The terminal-`0xFF` case did not merely
fail — it panicked:

    panicked at src\seq.rs:101:34:
    index out of bounds: the len is 24 but the index is 24

That is the `data[i]` meta-type read with `i == end` the observation names. All six
regressions failed against the pre-fix parser: the terminal-meta panic, truncated
delta VLQ, overlong meta and SysEx payloads, and truncated channel message all
returned `Ok` or crashed instead of erroring, and both the missing-second-track and
every-strict-prefix oracles failed. Restoring `seq.rs` (md5 `c57bfea9…`) turned all
six green.

**Root cause addressed at the right layer.** `vlq` became fallible and bounded by
the *declared track end* rather than the file length, the track header/length are
validated with `checked_add` before use, meta and SysEx payloads are bounded by
`payload_end <= end`, an unknown status byte is now an error rather than a silent
fall-through, and `pos` advances to the validated `end`. The tempo payload read no
longer consults `data.len()`, which was the specific "read into the next chunk"
the report flagged.

**The strongest guard here is `every_strict_backing_file_prefix_is_rejected`** — it
truncates the real shipped `BACKING` asset at every byte offset and requires an
`Err` each time. That is an adversarial oracle over real data rather than four
hand-picked fixtures, and it is what makes a future regression hard to miss.

**Gates** (amp-lab is its own workspace, so these run from `crates/amp-lab/`):
`cargo test` 43 pass / 0 fail — including the shipped-loop oracles, so the real
asset still parses under the stricter reader; `cargo clippy --all-targets --
-D warnings` clean; `cargo fmt -- --check` clean.

## Notes

Confirmed by the reliability and maintainability lenses and the devil's advocate. The
security lens correctly refuted attacker reachability in the current binary.
