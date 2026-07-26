# MM-BUG-KILN-00141 — ensure_ydp_sf2 trusts a warm cache without checking its pinned hash

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample generation / provenance
- **Raised:** 2026-07-26
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
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

**Symptom.** `ensure_ydp_sf2` skips its own SHA-256 pin check whenever the extracted SF2 is already cached, so a warm cache is trusted without proving it came from the pinned archive.

`tools/ferrosintesis-samples/prepare.py:2615-2631`:

    def ensure_ydp_sf2(src):
        """Fetch + sha256-verify the YDP Grand .tar.bz2 and extract its SF2."""
        sf2 = os.path.join(src, "YDP-GrandPiano.sf2")
        if not os.path.exists(sf2):
            ...
            digest = hashlib.sha256(open(arc, "rb").read()).hexdigest()
            if digest != YDP_SHA256:
                raise ValueError(...)
            ...extract...
        return sf2

The pin comparison sits INSIDE the `if not os.path.exists(sf2)` block, so once `YDP-GrandPiano.sf2` exists it is unreachable. Replacing the cached SF2 with different bytes, or bumping `YDP_SHA256` without clearing the cache, leaves the stale/substituted file in use.

**Consequence.** `_bake_ydp_grand` (`prepare.py:2633`) rewrites the nine tracked `crates/ferrosintesis-samples-ydp-grand/samples/ydpgrand_*.wav` from those bytes, and that crate's `PROVENANCE.md:25` claims the source is "SHA-256 pinned in prepare.py". On a warm cache that claim is not enforced.

**Expected.** A warm cache is either proven to come from the pinned archive, or rejected and rebuilt - the contract `ensure_salamander_sources` and `ensure_archive_sources` now satisfy.

**Actual.** Existence alone is accepted.

**Provenance and scope.** Split out of MM-BUG-KILN-00134 during its independent two-eyes verification. That bug reported and fixed exactly this defect for `ensure_salamander_sources`; the fix is good and 00134 was closed. Applying this repo's own "enumerate all of L before fixing" rule, I censused every pinned-archive helper in `prepare.py` and `ensure_ydp_sf2` is the ONLY remaining one that is unauthenticated when warm:

| helper | warm-cache treatment |
|---|---|
| `ensure_archive_sources` | manifest (`cached_members_match`) - authenticated |
| `ensure_salamander_sources` | manifest (`cached_members_match`) - authenticated, MM-BUG-KILN-00134 |
| `ensure_flac_sources` | manifest bound to pin + decode recipe - authenticated, MM-BUG-KILN-00139 |
| `ensure_guitar_sources`, `ensure_ebass_sources`, `ensure_bagpipe_sources` | re-hash the cached file on every call - authenticated |
| `ensure_musescore_sf3`, `ensure_musescore_general_sf3` | only the FETCH is skipped when warm; the sha256 comparison runs unconditionally - authenticated |
| **`ensure_ydp_sf2`** | **existence only - the pin is unreachable when warm** |

I verified the MuseScore pair by reading them rather than trusting a pattern match: my first heuristic classified them as unauthenticated and was wrong, because their `if not os.path.exists(...)` guards only the download while the hash check sits outside it.

NOT in scope: the VCSL-sourced `steinwayb` and `kawai` banks go through `ensure_direct_sources` (`prepare.py:3191-3193`) and carry no per-file SHA pin at all - a different shape (no pin to bypass; they are pinned by `VCSL_REV` in the URL), deliberately not folded in here.

**Fix direction.** Give `ensure_ydp_sf2` the same treatment the sibling helpers already have - either re-hash the cached SF2 against a pinned SF2 digest on every call (the cheap MuseScore shape, one hash of ~36 MB) or bind it to the archive pin with a manifest (the `cached_members_match` shape). Then add the derived oracle that does not exist yet: an assertion that EVERY pinned-archive helper authenticates its warm cache, so the next helper cannot land unguarded. That missing oracle is why this recurred - MM-BUG-KILN-00062 fixed the class once for `ensure_archive_sources`, 00134 fixed it again for the Salamander, and nothing forced the third instance to be found.

## Fix

<unfixed — raised only>

## Notes
