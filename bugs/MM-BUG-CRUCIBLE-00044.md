# MM-BUG-CRUCIBLE-00044 — Sample-bank crates' public get() rustdoc still names a .wav suffix the FLAC banks no longer use

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** crates/ferrosintesis-samples-clavinet
- **Raised:** 2026-08-18T19:41:02Z
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
- **State history:** Open (2026-08-18T19:41:02Z, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

The published asset crates document a file-name contract that their own payload no
longer satisfies. `ferrosintesis-samples-clavinet`'s only public function carries this
rustdoc:

`crates/ferrosintesis-samples-clavinet/src/lib.rs:61-63`

```
/// Returns the embedded WAV bytes for an exact file name.
///
/// Names include the `.wav` suffix and are case-sensitive.
```

Every embedded name ends `.flac` (`crates/ferrosintesis-samples-clavinet/src/lib.rs:14-59`;
the eleven files on disk are `clavinet_{C2..C6,G1..G6}.flac`). The lookup is an exact,
case-sensitive string compare (`src/lib.rs:64-69`), so a caller who follows the published
doc and asks for `clavinet_C2.wav` gets `None` — silently, with no diagnostic. This is the
crate's entire public API surface, it is live on docs.rs for the released `0.2.0`, and the
banks became FLAC on 2026-08-16 (`9046cd14` / `59509f7b`; see
`crates/ferrosintesis/CHANGELOG.md:18`).

The packaged provenance file repeats the error in prose:
`crates/ferrosintesis-samples-clavinet/PROVENANCE.md:9` — "The 11 WAVs in `samples/`".

**This is a list defect, not a single-crate defect.** Per CLAUDE.md ("Hand-maintained
lists are the recurring defect here — enumerate all of L before fixing"), the whole set
was enumerated rather than just the crate under review. Twelve asset crates carry the same
two stale doc lines while embedding only FLAC:

| Crate | Stale lines (`src/lib.rs`) |
|---|---|
| `ferrosintesis-samples-core` | 278, 280 |
| `ferrosintesis-samples-drumkit` | 562, 726, 740, 742, 754 |
| `ferrosintesis-samples-drumkit2` | 215, 217 |
| `ferrosintesis-samples-gong` | 23, 25 |
| `ferrosintesis-samples-grand` | 235, 237 |
| `ferrosintesis-samples-fretnoise` | 78, 80 |
| `ferrosintesis-samples-clavinet` | 61, 63 |
| `ferrosintesis-samples-orchestral2` | 14, 410, 412 |
| `ferrosintesis-samples-bottle` | 20, 22 |
| `ferrosintesis-samples-musescore` | 16, 144, 146 |
| `ferrosintesis-samples-sax` | 314, 316 |
| `ferrosintesis-samples-strings` | 19, 188, 190 |

`ferrosintesis-samples-b1-upright` is the deliberate WAV exception, and its wording
(`src/lib.rs:228`) is correct — leave it alone. Wider blast radius in prose, same root
cause: `crates/ferrosintesis/src/lib.rs:52` ("1156 WAVs across twenty-five"), and the
`README.md` / `PROVENANCE.md` "N WAVs" / "The WAVs under `samples/`" statements in the
`gong`, `grand`, `honkytonk`, `ydp-grand`, `headroom`, `vcsl-steinway`, `drumkit`,
`bottle`, `fretnoise` and `ccby` crates.

Classification: shipped documentation defect on a published crate's public contract. Not a
render or behaviour regression — the synth itself is correct
(`crates/ferrosintesis/src/sampler.rs:5501-5511` names the `.flac` files, and
`embedded_wav`, `sampler.rs:232-254`, resolves them).

Verified by reading each cited line; a devil's-advocate reviewer briefed to refute the
finding confirmed it stands.

## Fix

Two parts. Do the second one — the doc edits alone will drift again the same way.

1. Retarget the prose. For each of the twelve crates above, change the `get()` rustdoc to
   the container-neutral wording the newer crates already use — `ferrosintesis-samples-rain`
   (`src/lib.rs:17`), `-honkytonk` (`src/lib.rs:51`), `-mandolin` (`src/lib.rs:175`) and
   friends say "Returns the embedded sample bytes for an exact (case-sensitive) name." Fix
   the `Embedded (file-name, bytes) pairs. Names include the `.wav` suffix…` header comments
   in `-musescore`, `-orchestral2` and `-strings` the same way, and correct
   `crates/ferrosintesis-samples-clavinet/PROVENANCE.md:9` plus the README/PROVENANCE prose
   listed above.

2. Add a derived oracle so it cannot recur, in the style of
   `crates/ferrosintesis/src/licensing.rs` and `src/manifest.rs`. Walk each sample crate's
   `samples/` directory, derive the container(s) it actually ships, then source-scan that
   crate's `src/lib.rs`, `README.md` and `PROVENANCE.md` and fail when the text names a
   container the bank does not use. `crates/ferrosintesis/src/payload.rs:42-67` already
   walks exactly this directory set via `licensing::default_sample_crates()`, so the
   enumeration is a few lines on top of an existing, non-vacuous scan. Guard it against the
   vacuous-pass failure mode the sibling oracles guard against (assert the crate count and
   file count are non-trivial), and — per CLAUDE.md — write the adversarial document that
   *should* fail it and check that it does.

Effort: ~1-2 h (mechanical edits across 12 crates plus one oracle and its negative test).

## Notes
