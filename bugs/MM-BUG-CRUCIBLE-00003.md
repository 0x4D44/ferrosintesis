# MM-BUG-CRUCIBLE-00003 — Malformed SMF Program Change can panic rendering

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / SMF parser and renderer
- **Raised:** 2026-07-31
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260731T062701Z-p86820-n912298900-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00003-run-fix-20260731T062701Z-p86820-n912298900-c1
- **Owner base:** 98a7d1fea6838576d10ff046140d1549828eab16
- **Owner fingerprint:** -
- **Owner since:** 2026-07-31T06:27:01Z
- **Owner until:** 2026-07-31T08:27:01Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-31, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh)

## Observation

The SMF parser reads Program Change data verbatim:
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\midi.rs:332-334`
uses `let prog = c.u8()?` without enforcing MIDI's seven-bit data range. An
otherwise well-formed track containing `00 C0 FF 00 FF 2F 00` therefore produces
`EvKind::Prog { ch: 0, prog: 255 }`.

The engine stores that value unchanged at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\engine.rs:3117-3119`.
The first rendered block then calls `program_trim_lin(strip.program)` at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\engine.rs:3814-3823`,
which indexes the 128-entry `PROGRAM_TRIM_DB` at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\engine.rs:1200-1223`.
A NoteOn also indexes the 128-entry `VEL_LEVEL_EXP` at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\voices.rs:14244-14261`.

**Expected:** malformed channel data is rejected with a typed parse error or
normalized consistently to seven bits; rendering arbitrary input never aborts.

**Actual:** parsing succeeds, and default offline rendering panics on index 255.
No note is required because the default six-second tail enters the render loop.
This is an availability defect in safe Rust, not memory unsafety.

## Fix

Enforce a parser-wide seven-bit channel-data policy. For the immediate crash,
mask Program Change with `& 0x7F`, matching the existing malformed-note-key
policy, or reject high-bit data consistently at the trust boundary. Do not clamp
only at the array index, because that leaves the invalid program in channel
state.

Add two regressions:

1. Parser coverage for `C0 FF`, requiring either a typed error or program 127.
2. Public `offline::render` coverage proving the malformed input cannot panic
   and, if masking is chosen, matches the canonical program-127 render.

## Notes

Static review only; the pass did not execute the application or tests.

This is not a duplicate of `MM-BUG-KILN-00025`. That closed bug fixed malformed
note keys and stated that program bytes were not array indices. The later
`PROGRAM_TRIM_DB` and `VEL_LEVEL_EXP` indexing makes that premise stale.

Reported in
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\wrk_docs\2026.07.31 - CR - 20260731-REV-CLA@CRUCIBLE-code-review-014814.md`.
