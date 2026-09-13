# MM-BUG-KILN-00248 — Headroom regeneration command leaves the embedded FLAC bank stale

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** headroom sample crate / deterministic regeneration
- **Raised:** 2026-08-17T00:04:33Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260913T073537Z-248083dd
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00248-run-fix-20260913T073537Z-248083dd
- **Owner base:** 05fc76fb677a2ba274a920caa0fd901ff18b19cb
- **Owner fingerprint:** -
- **Owner since:** 2026-09-13T07:35:37Z
- **Owner until:** 2026-09-13T09:35:37Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T00:04:33Z, raised via `deltic bugs new`)

## Observation

The crate documents `python3 tools/ferrosintesis-samples/prepare.py
--only=headroom` as its regeneration command at
`crates/ferrosintesis-samples-headroom/README.md:15-16` and
`PROVENANCE.md:63-69`. The active crate embeds 45 FLAC files, but
`tools/ferrosintesis-samples/prepare.py:780-794` canonicalizes the Headroom
recipe to 45 physical `.wav` output names, and the generic loop at
`prepare.py:5733-5787` writes those WAVs. The stale-output validator at
`prepare.py:5402-5429` inspects only WAV names and cannot reject the existing
FLAC half.

Following the documented command therefore adds 45 WAVs beside the 45 old FLACs
and leaves every payload used by runtime unchanged. The crate inventory test at
`crates/ferrosintesis-samples-headroom/src/lib.rs:234-246` then sees both
extensions and disagrees with `FILE_COUNT = 45`. Expected: the scoped command
replaces and verifies the exact final-format bank that runtime embeds. Actual: it
produces unconsumed assets and leaves the shipped bank stale. Concrete fix: make
the Headroom workflow stage and verify final FLACs, update the alias/table contract,
and reject or remove mixed containers before publication. This remains distinct
from Open `MM-BUG-KILN-00241`, which covers the generator's syntax failure. Static
review only; the command was not run.

## Fix

<unfixed — raised only>

## Notes
