# MM-REQ-KILN-00138 — The audition momentary-loudness peer census must be a committed tool

- **State:** Draft
- **Priority:** Should
- **Area:** tools / instrument-balance
- **Raised:** 2026-07-26
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-26, raised via `deltic reqs new`)

## Statement

The M-CAL instrument-balance rig cannot measure any program its percussive guard
excludes — which is the whole plucked/struck backlog, on **both** reference
modules. For those programs there is a second instrument that works and needs no
external reference at all: the **Reference Audition** gives every voice in a family
an identical root, velocity, figure and dry sends, so per-slot loudness differences
are differences between the *voices*. That turns a program's own family into its
comparison set.

**The system must ship that census as a repeatable tool, not a throwaway.**
Concretely: read `loudness.rs:momentary_lufs` out of a rendered audition WAV, window
it onto the audition's 5-second slot grid using the committed `lyrics/*.txt`
timestamps, and report each slot's peak momentary loudness against its family
median.

Acceptance should be able to reproduce the numbers this was first used for — GM6
harpsichord at the shipped +6 dB reading -14.58 LUFS, 2.62 below the GM0-7 median,
with each rung of a 0 / +3 / +6 trim ladder moving GM6 by ~3 dB while no peer moves
more than 0.03 dB.

Flagged `light`: the whole thing was a ~25-line example plus a short script. The
only judgement calls are where it lives (a committed
`ferrosintesis-cli` example, a `tools/` script, or a `calmeter` mode) and that
`ferrosintesis-cli` is a published crate, so an example there is shipped code.

## Notes

Raised 2026-07-26 out of MM-BUG-KILN-00107 condition (c). The census is what
finally settled GM6 after the M-CAL re-derive could not: see that bug's
"GM6 (2026-07-26)" section for the method and the full table.

The throwaway helper used at the time is preserved outside the repo at
`D:\worktrees\midi-music\KILN-00107-listening\momentary_dump.rs (uncommitted - see
README).txt` — it is 25 lines and trivial to re-derive, so treat it as a reference
rather than something to rescue.

Worth doing because it is not GM6-specific: every program the percussive guard
excludes is currently unmeasurable, and this is the only route to them that does
not need mdmidiemu plus the SC-55 ROMs.
