# MM-BUG-KILN-00283 — Drum-kit regeneration command leaves the embedded FLAC banks stale

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** split drum-kit sample crates / deterministic regeneration
- **Raised:** 2026-08-17T11:39:57Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T202909Z-de9d68d7
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00283-run-verify-20260913T202909Z-de9d68d7
- **Owner base:** 3ca1f7cb0d8a988212fb0adbbf16ccf1fb929422
- **Owner fingerprint:** sha256:dc0283ad305d43b8352b93e00a168bb4a434e2dd07963a13c3bb053c11903250
- **Owner since:** 2026-09-13T20:29:09Z
- **Owner until:** 2026-09-13T22:29:09Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T11:39:57Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T18:50:57Z, deltic:auto role=fix run=fix-20260913T183742Z-34923c74 branch=task/bug-MM-BUG-KILN-00283-run-fix-20260913T183742Z-34923c74 code=82e6b571cf357b86b8dc480a39e026053146a1f0 gate=manual)

## Observation

The package documents
`python3 tools/ferrosintesis-samples/prepare_drumkit.py` as its complete
regeneration command at
`crates/ferrosintesis-samples-drumkit/README.md:18-19` and
`PROVENANCE.md:109-116`. The active core package embeds 128 `.flac` files at
`src/lib.rs:34-547`, and the companion package likewise embeds FLAC.

The shared generator still plans and stages `.wav` names at
`tools/ferrosintesis-samples/prepare_drumkit.py:167-196,320-333`.
`publish_staged` examines only existing WAVs and copies the generated WAVs at
`:351-376`; it neither rejects nor replaces the committed FLACs. Following the
documented command therefore adds 128 unconsumed WAVs beside the core package's
128 unchanged FLACs and does the same for the companion's 36 takes. Runtime keeps
using stale FLAC bytes. The core inventory test at `src/lib.rs:850-880` then sees
both extensions and fails its 128-file contract.

The generator's own parity oracle is stale too:
`tools/ferrosintesis-samples/test_prepare_drumkit.py:76-94` filters committed
inventories to `.wav`, so its planned 128/36 WAV sets cannot equal the current
FLAC-only directories. The separate `to_flac.py` describes itself as a one-time
bake and is not part of either package's regeneration command.

Expected: one documented workflow replaces and verifies the exact final-format
assets compiled by both drum packages. Actual: it creates a second container set,
leaves shipped audio stale, and makes inventory/parity checks red. This is a
deterministic source/file-set result; the command and tests were not run.

## Fix

<unfixed — raised only. Generate the canonical FLAC outputs in empty staging,
verify decoded PCM and the complete two-package inventory, reject mixed same-stem
containers, then publish both packages failure-atomically and refresh their Rust
tables and provenance. Add a negative fixture starting from the current FLAC-only
tree. Estimated effort: Medium.>

## Notes
