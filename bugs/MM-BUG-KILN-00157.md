# MM-BUG-KILN-00157 — Sax regeneration trusts unauthenticated warm-cache inputs

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample generation / sax cache
- **Raised:** 2026-07-28
- **Owner:** deltic:gpt-5.5
- **Owner role:** fix
- **Owner run:** fix-20260728T030703Z-p57192-n099327800-c79
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00157-run-fix-20260728T030703Z-p57192-n099327800-c79
- **Owner base:** 1f8fde4624a0312692e79565979d2faf763fa99e
- **Owner fingerprint:** -
- **Owner since:** 2026-07-28T03:07:03Z
- **Owner until:** 2026-07-28T03:52:03Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

**Symptom.** The documented sax regeneration path reuses cached SFZ metadata, source FLACs, and decoded WAVs solely because those paths exist. `_mtg_region_keys` at `tools/ferrosintesis-samples/prepare.py:3040-3045` trusts an existing region file. `_bake_mtg_sax` at `:3129-3137` trusts existing FLAC and WAV files, then measures and publishes their derivative at `:3143-3160`.

**Expected.** Every warm input used by `prepare.py --sax-only` is bound to the pinned MTG revision and exact fetched bytes; every decoded WAV is bound to its source digest and decode recipe.

**Actual.** The sax path calls raw `fetch` and ffmpeg rather than the authenticated `ensure_source` / decoded-source-manifest helpers. A valid substituted cache file is therefore baked into tracked published assets while `crates/ferrosintesis-samples-sax/PROVENANCE.md:27-30` still claims the pinned revision. The revision-keyed cache directory prevents cross-revision reuse, but it does not authenticate files already present under the current revision. A changed decode recipe also reuses the old WAV. This is a residual sibling of closed MM-BUG-KILN-00151, whose fix protects callers routed through `ensure_source`; no existing sax/MTG bug covers the bypass.

**Concrete fix.** Route SFZ and FLAC downloads through authenticated URL+digest cache handling. Bind each decoded WAV to the exact FLAC digest, decode-recipe revision, and its own digest; stage and atomically replace it. Add negative controls for altered SFZ, FLAC, decoded WAV, changed recipe, and interrupted decode, plus a healthy-cache no-refetch control. Broaden the derived cache-authentication oracle so bespoke bake helpers cannot call raw `fetch` behind existence guards.

**Effort:** Medium.

## Fix

<unfixed — raised only>

## Notes
