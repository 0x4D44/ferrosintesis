# MM-BUG-KILN-00205 — YDP regeneration can publish a mixed bank after a late failure

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** YDP sample generation / failure atomicity
- **Raised:** 2026-08-16T08:40:59Z
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
- **State history:** Open (2026-08-16T08:40:59Z, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

**Symptom.** `_bake_ydp_grand()` publishes each of the nine tracked WAVs as
soon as that zone has been decoded. It does not prove that every required source
root can be decoded, or that every replacement can be written, before changing
the bank.

At
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-092455\tools\ferrosintesis-samples\prepare.py:4715`,
the preflight checks only whether the current output directory contains an
unexpected owned filename. The function builds `by_root`, then enters the
publication loop at line 4773. It looks up one root at line 4774 and writes that
zone to its final tracked path at line 4782 before it checks the next root.
`write_wav_mono()` atomically protects each individual destination, but not the
nine-file bank as a set.

A pinned source revision that omits a later `YDP_ZONE_MIDI` root, a late frame
range error, or an injected write failure on a later destination therefore
leaves the already-written prefix from the new bake and the untouched suffix
from the old bake. The failure is recoverable from Git, but the mixed bank still
has all nine names and can remain structurally valid, so the crate inventory and
RIFF-magic checks need not reject it.

**Expected.** A failed or incomplete YDP regeneration leaves the previous bank
byte-identical. Only a complete, validated nine-file replacement becomes
visible at the tracked paths.

**Actual.** Generation, validation, and publication are interleaved per zone.
A late failure can publish a mixed old/new bank.

**Concrete fix.** Preflight the complete SF2 structure, required roots, sample
IDs, and frame ranges before writing. Generate all nine WAVs in a temporary
staging directory, validate the exact inventory and WAV contracts, then publish
the complete set through a helper that rolls back every replacement if a
publication step fails. Add negative regressions for a missing late root and an
injected failure after several staged outputs; both must preserve the old bank
byte-for-byte.

Static review only. No generator, test, build, app, render, package command, or
exploratory harness ran. Estimated effort: Small–Medium.

## Fix

<unfixed — raised only>

## Notes

Closed `MM-BUG-KILN-00063` made each individual WAV replacement atomic.
Closed `MM-BUG-KILN-00153` fixed the analogous whole-bank publication defect in
the standalone banjo generator. Neither changes this YDP code path.
