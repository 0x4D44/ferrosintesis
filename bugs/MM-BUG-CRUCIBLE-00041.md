# MM-BUG-CRUCIBLE-00041 — banks_parse sanity sweep is a hand-written chain that omits the bass banks and most other zone families

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** sampler / bank oracles
- **Raised:** 2026-08-18T00:08:33Z
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
- **State history:** Open (2026-08-18T00:08:33Z, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

**Symptom.** `banks_parse` is the sampler's basic sanity sweep over zone banks — it asserts
each zone is long enough, has a plausible root, and is peak-normalised. It is a
hand-written `.chain()` list, and most zone families are not in it, including both electric
bass banks.

**Expected.** Every zone bank is covered, and a newly added bank is covered on its first
commit.

**Actual.** `crates/ferrosintesis/src/sampler.rs:7420-7478`. The test chains **34**
accessors in two groups:

- `:7422-7451` — 28 families (violin, flute, grand ×6, trumpet, mutetpt, trombone, tuba,
  horn, oboe, bassoon, clarinet ×2 each, nylon, strsec ×2), asserting
  `data.len() > 20_000`, `(25.0..2500.0).contains(&root)`, and `peak > 0.5`.
- `:7461-7476` — the 6 conditioned piano banks, with a `(0.12..=0.91)` peak band.

`sampler.rs` defines **107** `fn <name>() -> &'static [Zone]` bank builders and exposes
**38** `pub fn ... -> &'static [Zone]` accessors. Neither `finger_bass()` (`:963-975`) nor
`pick_bass()` (`:985-998`) appears in either chain — nor do `pizzbass`, `dbass`,
`contrabass_*`, `rhodes`, and many others. The companion oracle at `sampler.rs:6621-6623`
describes the same file as carrying "57 families, 700+ zones", so roughly two thirds of the
families are outside this sweep.

**What is and is not covered for bass.** The 13 bass zones *are* decoded — `prewarm()`
(`sampler.rs:3091-3092`) and `exercise_every_public_bank()` (`:6060`, `:6070`) force it, and
`ferrosintesis-flac` re-verifies each payload's STREAMINFO MD5 on load
(`crates/ferrosintesis-flac/src/lib.rs:374-382`). So *corruption* is caught. What is not
caught is a structurally valid but musically wrong take: silent, clipped, mis-trimmed, or
wrongly normalised.

Only 4 of the 13 bass zones are reached by any rendering test —
`la_bass_onset_engages_at_every_supported_rate` (`sampler.rs:7866-7883`) exercises finger
E1 and G#1 and pick E2, and its own doc at `:7849-7855` states pitch is deliberately not
scored. The remaining **9** zones (`fingerbass_F#1/A#1/C2/D2`,
`pickbass_F#1/G#1/A#1/C2/D2`) are decoded and never checked for level, peak or length by
anything.

**Concrete failure.** A re-bake mis-trims `fingerbass_C2.flac` so its onset is cut past the
transient and the file is near-silent. `EXPECTED_BYTES` moves, so the crate test goes red
and gets re-pinned as a matter of course; the FLAC decodes cleanly and its MD5 matches;
`every_note_named_zone_root_matches_its_filename` reads source text, not audio;
`banks_parse` never sees the bank. GM 33 C2 through D#2 loses its attack layer and nothing
is red. The identical assertion that would have caught it — `peak > 0.5` — is already
written 20 lines away and simply is not applied to this family.

**This is the repo's signature defect, in a test.** CLAUDE.md's *Hand-maintained lists are
the recurring defect here* names three instances (KILN-00060/00059/00069) and prescribes
deriving the set from source. `banks_parse` is a fourth: a list that grows one entry per
feature change, where nobody re-read the whole. The adjacent oracles already show the way —
`prewarm_leaves_no_bank_uninitialized` counts `bank!` initialisations, and
`every_public_bank_accessor_is_exercised` source-scans so a new accessor cannot land
outside the sweep.

Static review only. No build or test ran; the counts above are from grep over the committed
`sampler.rs` and from reading the chain.

## Fix

Unfixed. Raised for the fix-open-bugs loop; this review did not change code.

Derive the sweep instead of listing it. `exercise_every_public_bank()` (`sampler.rs:6060`)
already enumerates every public bank accessor for the prewarm oracles; route `banks_parse`'s
assertions through the same enumeration so a family cannot be silently absent.

The obstacle is that the thresholds are not uniform — the conditioned pianos need
`(0.12..=0.91)` rather than `peak > 0.5`, and the tuba's low root drove the 25 Hz floor. So
the derived form needs a small per-family exception table, and that table must itself be
proved exhaustive: assert that every enumerated family is either checked by the default
bar or named in the exception set, and that no exception names a family that no longer
exists. Otherwise the exception table becomes the next hand-maintained list.

Cheapest correct first step, if the full derivation is too large for one change: add
`.chain(finger_bass()).chain(pick_bass())` and the other missing families to the existing
chain, and *in the same change* add the derived guard that fails when a public bank
accessor is absent from the sweep. Adding the entries alone repeats the defect.

**Prove it fails first.** Zero out one bass zone's samples in a scratch tree and confirm
the new coverage reports it; today it does not.

## Notes

- Same shape as Open `MM-BUG-KILN-00284` ("Core drum-kit audio oracle omits 33 routed
  takes") but a different oracle and a different crate; whoever fixes one should read the
  other, since a single derived-enumeration approach may serve both.
- No existing bug or requirement mentions `banks_parse` — checked across `bugs/` and
  `reqs/`.
- Found during the coverage-ledger review of `crates/ferrosintesis-samples-bass/`. The
  finding is repo-wide; bass is where the gap was noticed.
- Estimated effort: Small for the chain plus its guard; Medium for the full derived form
  with a proved-exhaustive exception table.
