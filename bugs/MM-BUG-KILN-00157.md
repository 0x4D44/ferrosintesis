# MM-BUG-KILN-00157 — Sax regeneration trusts unauthenticated warm-cache inputs

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample generation / sax cache
- **Raised:** 2026-07-28
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
- **Attempts:** fix=0, doubt=1, indeterminate=0
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high) → Fixed (2026-07-28, deltic:auto role=fix run=fix-20260728T030703Z-p57192-n099327800-c79 branch=task/bug-MM-BUG-KILN-00157-run-fix-20260728T030703Z-p57192-n099327800-c79 code=336355b461c7f32a82cca417a1ac8ef1e02eb33e gate=deltic model=codex@xhigh) → Open (2026-07-28, deltic:auto role=verify run=verify-20260728T162705Z-p57192-n426209200-c251 verified_fix_run=fix-20260728T030703Z-p57192-n099327800-c79 verdict=doubt reason=fix-is-statically-sound-and-5-6-gate-steps-are-green-but-python3-is-denied-in-th model=claude)

## Observation

**Symptom.** The documented sax regeneration path reuses cached SFZ metadata, source FLACs, and decoded WAVs solely because those paths exist. `_mtg_region_keys` at `tools/ferrosintesis-samples/prepare.py:3040-3045` trusts an existing region file. `_bake_mtg_sax` at `:3129-3137` trusts existing FLAC and WAV files, then measures and publishes their derivative at `:3143-3160`.

**Expected.** Every warm input used by `prepare.py --sax-only` is bound to the pinned MTG revision and exact fetched bytes; every decoded WAV is bound to its source digest and decode recipe.

**Actual.** The sax path calls raw `fetch` and ffmpeg rather than the authenticated `ensure_source` / decoded-source-manifest helpers. A valid substituted cache file is therefore baked into tracked published assets while `crates/ferrosintesis-samples-sax/PROVENANCE.md:27-30` still claims the pinned revision. The revision-keyed cache directory prevents cross-revision reuse, but it does not authenticate files already present under the current revision. A changed decode recipe also reuses the old WAV. This is a residual sibling of closed MM-BUG-KILN-00151, whose fix protects callers routed through `ensure_source`; no existing sax/MTG bug covers the bypass.

**Concrete fix.** Route SFZ and FLAC downloads through authenticated URL+digest cache handling. Bind each decoded WAV to the exact FLAC digest, decode-recipe revision, and its own digest; stage and atomically replace it. Add negative controls for altered SFZ, FLAC, decoded WAV, changed recipe, and interrupted decode, plus a healthy-cache no-refetch control. Broaden the derived cache-authentication oracle so bespoke bake helpers cannot call raw `fetch` behind existence guards.

**Effort:** Medium.

## Fix

The MTG sax path now authenticates warm SFZ and FLAC inputs through the
direct-source manifest cache. Decoded WAVs are accepted only when a manifest
binds their bytes to the authenticated FLAC digest and decode-recipe revision;
replacement decodes are staged, validated, and atomically installed.

Regression coverage proves that altered SFZ, FLAC, and decoded WAV entries are
rejected, recipe changes trigger a new decode, interrupted decodes leave no
partial cache, and a healthy warm cache is reused without fetching or decoding.
The same tests produced six failures against the pre-fix parent
`a6d202d4b594e0494771d0207a64462c63b06b9a` and passed on the fix.

Focused validation:

- `python3 -m unittest test_prepare.DirectSourceCacheTest test_prepare.PinnedFlacCacheTest test_prepare.PinnedWarmCacheAuthenticationTest test_prepare.MtgSaxCacheTest` — 28 passed.
- `deltic integrate --push` — affected-area gate passed and landed code commit `336355b461c7f32a82cca417a1ac8ef1e02eb33e`.

### Verification summary (2026-07-28, deltic:auto run=verify-20260728T162705Z-p57192-n426209200-c251 verified_fix_run=fix-20260728T030703Z-p57192-n099327800-c79 verdict=doubt)

Verifier note: Fix is statically sound and 5/6 gate steps are green, but python3 is denied in this session so the Python regression suite - the only gate step covering this bug - was never executed. — HEAD=9569393, fix commit 336355b confirmed an ancestor (touches only tools/ferrosintesis-samples/prepare.py + test_prepare.py). (1) Symptom, STATIC only: pre-fix _mtg_region_keys and _bake_mtg_sax used 'if not os.path.exists(p): fetch(...)' and 'if not os.path.exists(wav): subprocess.run(ffmpeg)'; on trunk they route through ensure_source (prepare.py:1242, digest+URL via direct_source_matches:1279) and _ensure_...

## Notes
