# MM-BUG-CRUCIBLE-00042 — Five packaged sample-crate NOTICEs still call the embedded FLAC banks WAVs

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample asset crates / packaged attribution notices
- **Raised:** 2026-08-18T06:59:44Z
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
- **State history:** Open (2026-08-18T06:59:44Z, raised via `deltic bugs new` model=claude-fable-5) -> Fixed (2026-09-13T08:08:58Z, deltic:auto role=fix run=fix-20260913T080234Z-3d8fc1e0 branch=task/bug-MM-BUG-CRUCIBLE-00042-run-fix-20260913T080234Z-3d8fc1e0 code=7c214447cda4d061de26949a503abccfd43e37e7 gate=manual) -> Closed (2026-09-13T19:59:17Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: no sample-crate NOTICE names WAV and every named crate ships only FLAC; pre-fix NOTICEs said embedded WAV)

## Observation

Static inspection (code-review pass over `crates/ferrosintesis-samples-ccby/`). Five
packaged `NOTICE` files still describe the embedded banks as WAV, but those banks have
shipped as FLAC since commit `9046cd14` (2026-08-16) and were published that way in the
0.2.0 release (`417c0b22`):

- `crates/ferrosintesis-samples-ccby/NOTICE:14` — "The embedded WAVs are attack
  transients trimmed from the original recordings" (all 20 payloads are `.flac`).
- `crates/ferrosintesis-samples-honkytonk/NOTICE:4` — "The embedded WAV samples".
- `crates/ferrosintesis-samples-vcsl-kawai/NOTICE:4` — "The embedded WAV samples".
- `crates/ferrosintesis-samples-vcsl-steinway/NOTICE:4` — "The embedded WAV samples".
- `crates/ferrosintesis-samples-ydp-grand/NOTICE:7` — "The embedded WAV samples".

Each crate's `samples/` directory holds only `.flac` files (verified by listing), and
each `NOTICE` is packaged (named in the crate's `Cargo.toml` `include` list), so the
published legal/attribution document misstates what it attributes.

The pre-release sweep `904cbe94` ("Correct packaged container claims before publishing",
2026-08-17) fixed 25 stale WAV claims across packaged rustdoc, READMEs and PROVENANCE
files — its file list contains no `NOTICE` at all, so the whole document class was
missed. This is the repo's standing enumerate-all-of-L pattern: the sweep enumerated
three of the four packaged document kinds. MM-BUG-KILN-00247 (Open) already covers the
sixth stale file, `crates/ferrosintesis-samples-headroom/NOTICE:4`, as part of that
crate's wider documentation drift; this record covers the remaining five so a fix of
00247 does not stop at headroom.

Expected: every packaged NOTICE describes the container the crate actually ships.
Actual: five NOTICEs say WAV over all-FLAC payloads. Concrete fix: correct the five
sentences (container-neutral wording such as "embedded samples" survives future
container moves); optionally fold NOTICE into the source-derived documentation guard
KILN-00247 proposes. No runtime behaviour is affected; the licences and credits
themselves are correct.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `7c214447` for ccby, kawai, steinway and ydp; honkytonk by `3f692a8e`; headroom by KILN-00247) by an agent other than the fixer.

**Original observation re-derived.** A case-insensitive search for `wav` across every `crates/ferrosintesis-samples-*/NOTICE` finds nothing, and all six named crates ship only `.flac`. "The embedded samples..." is container-neutral and true; the ccby "attack transients trimmed from the original recordings" matches its provenance.

**Fails-before (method A).** At `7c214447^` each of the four NOTICEs says "embedded WAV".

No regression guard was added; the record marked one optional, and the container oracle does not scan NOTICE files.

## Notes
