# MM-BUG-KILN-00284 — Core drum-kit audio oracle omits 33 routed takes

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** core drum-kit sample crate / audio validation
- **Raised:** 2026-08-17T11:40:04Z
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
- **State history:** Open (2026-08-17T11:40:04Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T19:09:35Z, deltic:auto role=fix run=fix-20260913T185158Z-892715cf branch=task/bug-MM-BUG-KILN-00284-run-fix-20260913T185158Z-892715cf code=4687d7dc15d4b9c674243e3f9135e2bff8c7261b gate=manual) -> Closed (2026-09-14T21:50:03Z, independent verify by Claude Opus 5 on trunk 1d87b00f: all ten core drum-kit banks now go through the duration/peak/RMS oracle; dropping RIDE_BELL from the bounds table fails three tests)

## Observation

`crates/ferrosintesis-samples-drumkit/src/lib.rs:683-686` registers ten routed
banks, but `decoded_banks_are_valid_audio` at `:966-1000` applies duration, peak,
and RMS assertions to only seven. It omits `RIDE_BELL` (9 takes at `:603-610`),
`HH_OPEN` (12 takes at `:619-626`), and `HH_PEDAL` (12 takes at `:627-634`) — 33
routed files in total.

The mapping test at `:904-923` decodes those takes but proves only name/index and
pointer agreement. The inventory test at `:947-960` proves only aggregate bytes,
container magic, and self-lookup. A structurally valid FLAC containing silence,
bad normalization, or an implausible duration in any omitted bank can therefore
pass this crate's local quality oracles and reach ride-bell, open-hat, or
pedal-hat playback.

Expected: every public bank receives the same meaningful-signal and duration
validation. Actual: 33 takes have structural coverage only. No current bad take
was claimed, and no test or decoder ran; the false-green mutation follows directly
from the enumerated test table.

## Fix

<unfixed — raised only. Derive the quality sweep from `BANKS`, keep per-bank
duration bounds as data, and assert that the bounds table covers every registered
bank exactly once. Add a negative silent or badly normalized omitted-bank fixture.
Estimated effort: Small.>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` (fix `4687d7dc`) by an agent other than the fixer.

**Original observation.** `decoded_banks_are_valid_audio` now iterates `BANKS` (all ten routed banks, including `RIDE_BELL`, `HH_OPEN` and `HH_PEDAL`) and applies `validate_decoded_take` to every take. `audio_bounds_cover_every_registered_bank_once` ties the bounds table to `BANKS` by pointer identity, and `decoded_audio_oracle_rejects_silent_omitted_bank_control` shows a same-length silent ride-bell take is rejected. All pass in `cargo test --workspace --all-targets --locked`, so every one of the 128 real takes meets its bounds.

**Fails-before (method B).** Removing the `RIDE_BELL` row (and shrinking the array to 9) fails three tests: `audio_bounds_cover_every_registered_bank_once` and `decoded_banks_are_valid_audio` (left 9, right 10) and the silent control ('ride-bell duration bounds must be registered'). Restored.

**Repo gate on `1d87b00f`.** Green: fmt, all three clippy steps, `cargo test -p ferrosintesis-cli --no-default-features`, and `cargo test --workspace --all-targets`. Red, not caused by this fix: `cargo test -p ferrosintesis --no-default-features` fails `no_default_gate_is_paired_with_embedded_sample_coverage` (MM-BUG-KILN-00301 reopened), and 4 `test_prepare.py` tests error (MM-BUG-CRU-00068 reopened).

## Notes
