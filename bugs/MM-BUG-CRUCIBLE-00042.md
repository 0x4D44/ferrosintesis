# MM-BUG-CRUCIBLE-00042 — Five packaged sample-crate NOTICEs still call the embedded FLAC banks WAVs

- **State:** Open
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
- **State history:** Open (2026-08-18T06:59:44Z, raised via `deltic bugs new` model=claude-fable-5)

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

## Notes
