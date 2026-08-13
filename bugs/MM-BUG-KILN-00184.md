# MM-BUG-KILN-00184 — Headroom logical alias duplicates packaged and decoded PCM

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** Headroom sample package / memory and package size
- **Raised:** 2026-08-13T19:30:29Z
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
- **State history:** Open (2026-08-13T19:30:29Z, raised via `deltic bugs new`)

## Observation

Read-only SHA-256 grouping of
`crates/ferrosintesis-samples-headroom/samples/*.wav` found nine byte-identical
pairs: every `headroom_*_f_rr2.wav` equals its corresponding
`headroom_*_mf_rr2.wav`. This follows from
`tools/ferrosintesis-samples/prepare.py:778-785`, where both logical cells use
the same LEVEL4 source. The musical mapping is intentional, but
`crates/ferrosintesis-samples-headroom/src/lib.rs:12-229` embeds every logical
name as a separate physical WAV.

Expected: logical aliases preserve the documented velocity/round-robin behavior
without storing or decoding the same PCM twice.

Actual: the nine redundant 133,048-byte files add exactly 1,197,432 packaged
bytes (16.67% of this crate's 7,184,592-byte WAV payload). The sampler also
builds independent `headroom_mf_rr2` and `headroom_f_rr2` `Vec<Zone>` caches at
`crates/ferrosintesis/src/sampler.rs:1469-1517`, although their roots and bytes
are identical. `prewarm()` reaches both at `sampler.rs:3103-3118`, retaining
about 2,394,072 avoidable decoded `f32` bytes and repeating the conversions.

This is the Headroom instance of the measured package/memory waste already
fixed for Kawai (`MM-BUG-KILN-00162`) and Steinway
(`MM-BUG-KILN-00165`). No audible corruption is claimed. Final release-binary
linker deduplication was not measured; decoded-memory and raw-package waste are
source-confirmed.

## Fix

Preserve all 54 logical lookup names through an explicit alias manifest while
packaging only the 45 unique WAV payloads. Make `headroom_f_rr2()` reuse
`headroom_mf_rr2()`, after retaining an oracle that their root tables agree.
Extend the generated duplicate-payload guard used by the Kawai and Steinway
crates so undeclared Headroom duplicates cannot return.

Suggested regression: assert 45 physical files and 54 logical names; resolve
every alias; require pointer identity for the shared decoded banks; reject an
undeclared duplicate payload. Estimated effort: Medium.

## Notes
