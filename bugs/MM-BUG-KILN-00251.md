# MM-BUG-KILN-00251 — Honky-tonk regeneration command leaves the embedded FLAC bank stale

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** honky-tonk sample crate / deterministic regeneration
- **Raised:** 2026-08-17T01:05:18Z
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
- **State history:** Open (2026-08-17T01:05:18Z, raised via `deltic bugs new`)

## Observation

The crate publishes `python3 tools/ferrosintesis-samples/prepare.py
--only=honkytonk` as its regeneration command at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\crates\ferrosintesis-samples-honkytonk\README.md:14-15`
and
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\crates\ferrosintesis-samples-honkytonk\PROVENANCE.md:48-54`.
The active crate embeds nine `.flac` files at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\crates\ferrosintesis-samples-honkytonk\src\lib.rs:12-49`,
and the runtime requests those FLAC names at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\crates\ferrosintesis\src\sampler.rs:1760-1773`.
The documented recipe instead validates and writes `honkytonk_*.wav` at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\tools\ferrosintesis-samples\prepare.py:4787-4818`,
while its stale-output validator inspects only WAV names at `prepare.py:5402-5429`.

Following the documented command therefore adds nine WAVs beside the nine old
FLACs without changing the payloads runtime consumes. The crate inventory test at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-014426\crates\ferrosintesis-samples-honkytonk\src\lib.rs:70-84`
then sees 18 sample files against `FILE_COUNT = 9`. Expected: the scoped command
atomically replaces and verifies the exact final-format bank runtime embeds.
Actual: it creates unconsumed outputs, leaves playback stale, and makes inventory
fail. Concrete fix: make the recipe stage, encode, verify, and publish the nine
final FLACs as one unit; reject mixed containers before the first write; refresh
the generated table; and add a negative regression starting from the current
FLAC-only tree. Static review only; the command was not run.

## Fix

<unfixed — raised only>

## Notes

Open `MM-BUG-KILN-00239`, `MM-BUG-KILN-00244`, and
`MM-BUG-KILN-00248` cover analogous but independently owned sample workflows.
Open `MM-BUG-KILN-00241` covers the separate syntax failure in
`gen_crate_lib.py`. Closed WAV-era stale-output bugs do not cover this later FLAC
migration mismatch.
