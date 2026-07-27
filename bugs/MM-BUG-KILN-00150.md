# MM-BUG-KILN-00150 — MuseScore sample notice omits mandatory upstream acknowledgements

- **State:** Open
- **Priority:** Should
- **Severity:** High
- **Area:** sample packaging / licensing
- **Raised:** 2026-07-27
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
- **Held branch:** host-local:KILN:task/bug-MM-BUG-KILN-00150-run-fix-20260727T054903Z-p9812-n086124000-c54-code-1785131994265
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

Static reproduction:

1. Read the crate's pinned source at
   `crates/ferrosintesis-samples-musescore/PROVENANCE.md:18-20`. It identifies
   MuseScore commit `d307a2bd899f15bf650efc3c2891211af5cb78b5` and the exact
   `MS Basic.sf3` SHA-256.
2. At that commit, upstream
   [`share/sound/MS Basic_License.md`](https://github.com/musescore/MuseScore/blob/d307a2bd899f15bf650efc3c2891211af5cb78b5/share/sound/MS%20Basic_License.md)
   lists five acknowledgements, then states that the acknowledgements and copyright
   notices above must be included in any derivative work.
3. `crates/ferrosintesis-samples-musescore/NOTICE:3-10` says those acknowledgements
   "are reproduced here", but reproduces only three. It omits:
   - `Temple Blocks instrument provided by Ethan Winer Copyright (c) 2002`
   - `Drumline Cymbals provided by Michael Schorsch Copyright (c) 2016`

Expected: the independently publishable sample crate carries every acknowledgement
that its pinned upstream licence requires.

Actual: its packaged `NOTICE` omits two of the five mandatory acknowledgement lines.
A distributor following the repository's instruction to concatenate the asset-crate
notices therefore receives incomplete attribution text.

The same static pass found nearby evidence of selective transcription drift:

- `NOTICE:14-16` says the crate contains only GM 104 sitar and GM 75/76/77 pipe
  onsets, while `src/lib.rs:63-94` also embeds eight GM 8 celesta WAVs. This is the
  still-live NOTICE portion of closed `MM-BUG-KILN-00069`; its recorded fix changed
  README/Cargo/PROVENANCE but never changed this NOTICE.
- `README.md:26-28` points readers to `tools/ferrosintesis-samples/README.md` for the
  source pin and regeneration recipe even though that guide's MuseScore inventories
  omit celesta and it calls clavinet the only non-CC0 bank. The packaged
  `PROVENANCE.md:7-20` is the accurate authority.

No build, test, application, render, generator, package command, or exploratory
harness ran. The WAVs and documents were inspected read-only.

## Fix

Reproduce both missing upstream acknowledgement lines in this crate's `NOTICE`.
Sweep the sibling notices and the parent consolidated notice that transcribe the same
pinned source so the same omission does not remain elsewhere. Update or remove the
NOTICE's partial instrument inventory, and make this crate's README point to its
packaged `PROVENANCE.md` as the source-pin and scoped-regeneration authority.

Add a regression in `crates/ferrosintesis/src/licensing.rs` that rejects an
MS-Basic-derived packaged notice when any acknowledgement required by the pinned
upstream licence is absent. Prefer checking against a committed verbatim copy of the
pinned upstream licence over maintaining another selective name list.

Estimated effort: Small.

## Notes

This is not a duplicate of `MM-BUG-KILN-00148`, which concerns the standalone
MuseScore-grand crate omitting the MIT permission grant. The primary defect here is
two missing acknowledgements in the `-musescore` crate, which no existing Open bug
covers.
