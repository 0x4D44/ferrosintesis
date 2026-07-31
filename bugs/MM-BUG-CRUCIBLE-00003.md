# MM-BUG-CRUCIBLE-00003 — Malformed SMF Program Change can panic rendering

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / SMF parser and renderer
- **Raised:** 2026-07-31
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
- **State history:** Open (2026-07-31, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh) -> Fixed (2026-07-31, deltic:auto role=fix run=fix-20260731T062701Z-p86820-n912298900-c1 branch=task/bug-MM-BUG-CRUCIBLE-00003-run-fix-20260731T062701Z-p86820-n912298900-c1 code=1f894e1e3d31dc3075231c6816843d14a8b5666a gate=manual) -> Closed (2026-07-31, claude-opus-5; independent two-eyes verification on trunk `ddd71e6`. The fixer was `deltic:auto role=fix` with GPT-5.6 as the authoring model on `1f894e1`; I did not fix it. ORIGINAL OBSERVATION re-run VERBATIM through the public CLI, not through a unit test: a format-0 file whose only track payload is the report's exact bytes `00 C0 FF 00 FF 2F 00`. Against a binary built at the pre-fix commit (`c86f850`, = `1f894e1~1`) it panics with `index out of bounds: the len is 128 but the index is 255` at `crates/ferrosintesis/src/engine.rs:1223` — the `PROGRAM_TRIM_DB` site the report named, reached with no NoteOn, exactly as reported. Against a binary from the fix-bearing tree the same file renders to completion (6.0 s tail, 0 voices, peak 0.00). TWO-SIDED at unit level as well: splicing the fix-bearing test modules onto the pre-fix source, all four new tests FAIL — `program_change_data_bytes_are_limited_to_seven_bits` reports `Prog { ch: 0, prog: 255 }`, and `offline::tests::malformed_program_change_renders_as_its_seven_bit_value` panics at `voices.rs:14261`, i.e. the SECOND index site (`VEL_LEVEL_EXP`) the report named, so both recorded crash sites are covered. ROOT CAUSE addressed at the right layer: the fix adds `Cursor::channel_data` and routes EVERY channel-voice data byte through it, so no out-of-range value reaches channel state — the report explicitly warned against clamping only at the array index, and the fix does not. `all_retained_channel_data_fields_are_limited_to_seven_bits` pins that wider policy across NoteOn/CC/pressure/bend/poly-pressure. Repo gate green on the exact tree: fmt, both clippy configurations with `-D warnings`, `cargo test -p ferrosintesis --no-default-features` (714 passed), `cargo test --workspace` (849 passed in the lib, 0 failures), and the Python sample-tool suite. No residual.)

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
