# MM-BUG-KILN-00069 — Sample-crate NOTICE/PROVENANCE files under-enumerate contents and drop named creators

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** packaging / licensing
- **Raised:** 2026-07-24
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
- **State history:** Open (2026-07-24, raised by Claude Opus 4.8 from the per-crate
  licence audit run while fixing KILN-00060; each item below is file-quoted)
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). The durable fix landed first: a
  licence-agnostic `inventory.rs` oracle derived from the packaged WAVs, which found MORE
  than the nine filed items. All nine addressed, five new PROVENANCE.md files written and
  packaged. Evidence under "Fix landed" below. Awaits independent two-eyes closure.)

## Observation

KILN-00060 fixed the *parent* guide. This bug collects accuracy defects found in the
**individual asset crates'** attribution files during the same audit. None hides a more
restrictive licence; each weakens the attribution paper trail a CC-BY or MIT credit
depends on.

**1. `ferrosintesis-samples-musescore` under-enumerates its own contents.**
Its `NOTICE`, README contents table and `Cargo.toml` description list only the GM 104
sitar and GM 75/76/77 pipes. The crate also embeds **8 GM 8 celesta onsets**
(`celesta_C4/C5/C6/C7/F#3/F#4/F#5/F#6.wav`), which `src/lib.rs:6` documents. A
distributor reading the NOTICE would not know the celesta bytes are in the shipment.

**2. `ferrosintesis-samples-musescore` has no `PROVENANCE.md`** — 16 sibling sample
crates have one. Its source pin exists only in
`tools/ferrosintesis-samples/prepare.py:746-753`
(`MUSESCORE_REV = d307a2bd899f15bf650efc3c2891211af5cb78b5`, SHA-256
`5ea2375e8bd7d8e71def1036978c1621e85b66934169b6a2744b27b9b3c2d99c`), so the packaged
crate carries no pin at all.

**3. `ferrosintesis-samples-gong` gives no per-work identification.** Its `NOTICE`
cites only the uploader page (`https://freesound.org/people/Digitopia_CdM/`), while
`PROVENANCE.md` identifies the two actual sounds (Freesound **261890** soft layer,
**261893** loud layer). CC BY credit normally names the work; the file that *ships*
does not. The same crate spells the credit `Digitópia / Casa da Música` in `NOTICE` and
`Casa da Música / Digitópia` in `PROVENANCE.md`, so there is no single canonical string
to copy.

**4. `ferrosintesis-samples-ydp-grand`'s README drops a named creator.** README:12
summarises the credit as "NOTICE credits Zenph/OLPC/FreePats" and omits
**roberto@zenvoid.org**, whom the `NOTICE` names as the producer of the SoundFont. A
distributor copying the README summary instead of the NOTICE loses a required name.

**5. `ferrosintesis-samples-ccby`'s `PROVENANCE.md` is stale in two ways.** Its
regeneration command reads `prepare.py --only=rhodes,dulcimer,musicbox`, but musicbox
is not in this crate (it ships in `-orchestral2`); and it carries **no checksums**
although `tools/ferrosintesis-samples/prepare.py:980` states "Provenance (exact pack
IDs/SHAs) in crates/ferrosintesis-samples-ccby/PROVENANCE.md". Pack IDs are present,
SHAs are not.

**6. Bank-select "CC0" collides with the licence "CC0" in prose.**
`ferrosintesis-samples-dark-salamander` and `-ydp-grand` write "CC0 bank 5" / "CC0 bank
7", meaning MIDI controller 0 (bank select), directly beside CC BY licence statements.
It reads as a public-domain claim on a CC-BY bank. Cosmetic, but exactly the kind of
misreading that produces a compliance mistake.

**7. `ferrosintesis-samples-strings` ships 8 WAVs it does not document.** README:13-16 and
`Cargo.toml:6` describe only `cellosolo_*` and `dbass_*` (32 files); `samples/` holds 40.
The extra 8 are `pizzbass_*` (`src/lib.rs:148-179`). Its stated regeneration command,
`prepare.py --only=cellosolo,dbass`, therefore rebuilds only 32 of its 40 files —
`prepare.py:909` confirms `pizzbass` is a separate family. `include` is
`["src/**", "samples/**", "README.md"]` with no `PROVENANCE.md`, and the pizzbass source
is documented only in `prepare.py:435-442`, outside the package. A crates.io consumer
receives 8 samples with no traceable origin. Drift is evidenced: the 8 WAVs arrived in
`1a033e3` while README was last touched by the earlier `32f9e91`.

**8. `ferrosintesis-samples-orchestral2` has no `PROVENANCE.md` and documents 5 of its
12 sample families.** Its README covers 50 of 116 WAVs and defers the rest to
`tools/ferrosintesis-samples/README.md`, which omits marimba, xylo, glock, vibes,
tubular and musicbox — 52 WAVs whose only provenance is `prepare.py` comments. The
licences are sound (SHA-pinned CC0 VSCO-2-CE / VCSL sources); the crate under-documents
57% of what it ships.

**9. The GM 10 music box had no licence record at all — now verified, so write it down.**
Its 11 `musicbox_*.wav` files are declared CC0 solely by a code comment at
`crates/ferrosintesis/src/sampler.rs:728`. `orchestral2` has no `PROVENANCE.md`, its
README never mentions musicbox (0 occurrences), and `prepare.py:979` merely routes the
family "→ the CC0 `-orchestral2`". That fell short of the repo's own standard, which
`ferrosintesis-samples-ccby/PROVENANCE.md` states as "per-sound license confirmed in
each pack's bundled `_readme_and_license.txt`" — a standard applied to the rhodes and
dulcimer packs but never to this one. The author's Freesound catalogue mixes CC0,
Attribution and Attribution-NonCommercial, so CC0 was **not** inferable at account level.

**Verified 2026-07-24 (Claude Opus 4.8), externally, all eleven sounds.** Freesound pack
44539 "Hand Crank Music Box B (Notes) Pack" by *moodyfingers*; each sound page states
**"Creative Commons 0"**:

| Sound | Note | Licence |
|---|---|---|
| 832332 | A5 | Creative Commons 0 |
| 832333 | A6 | Creative Commons 0 |
| 832334 | B5 | Creative Commons 0 |
| 832335 | B6 | Creative Commons 0 |
| 832336 | C6 | Creative Commons 0 |
| 832337 | C7 | Creative Commons 0 |
| 832338 | D6 | Creative Commons 0 |
| 832339 | E5 | Creative Commons 0 |
| 832341 | F6 | Creative Commons 0 |
| 832342 | G#6 | Creative Commons 0 |
| 832392 | E6 | Creative Commons 0 |

The 11 sounds match the 11 shipped zones exactly (`sampler.rs:713-723`). **The CC0
declaration is correct — there is no mislabelling.** What is missing is the committed
record, so the next reviewer must repeat this check. Note the near-miss: a *different*
moodyfingers pack (40874, sound 732943) is also a "Hand Crank Music Box" and is easy to
confuse with the pinned 44539.

## Fix

Per-crate documentation corrections; each is independent and cheap.

Item 9 is now just transcription: commit the verified table above into an
`orchestral2/PROVENANCE.md` so the check is never repeated. Item 6 is a rename ("bank
select 5"); items 3, 4 are text edits; item 7 needs a README row, a corrected
`--only=cellosolo,dbass,pizzbass` line and a `PROVENANCE.md`.

The durable fix is a **licence-agnostic** oracle alongside
`crates/ferrosintesis/src/licensing.rs`: assert that every packaged `samples/*.wav`
prefix is named in its own crate's documentation, and that every sample crate ships a
`PROVENANCE.md` in its `include` list. That converts items 1, 2, 7, 8 and 9 from prose
review into a build failure.

Note precisely why the KILN-00060 oracle cannot catch this class, and do not "fix" it by
widening that one: it keys off each bank's declared `license` field and deliberately
skips CC0 crates, because its question is "is the attribution guide complete?". The
question here is different — "has a crate's sample inventory outgrown its provenance
table?" — and it applies to CC0 crates too. Two oracles, two questions.

## Fix landed (2026-07-24)

**The oracle went first, and it found more than the report.** `crates/ferrosintesis/src/
inventory.rs` derives its expectations from what is actually PACKAGED
(`crates/ferrosintesis-samples-*/samples/*.wav`) and asserts two things: every family
prefix is named somewhere in its own crate's README / PROVENANCE / NOTICE, and every
sample crate ships a `PROVENANCE.md` that its `include` list actually packages.

Run before any fixing, it named:

- **5** crates with no `PROVENANCE.md` — `-core`, `-musescore`, `-orchestral`,
  `-orchestral2`, `-strings`. The bug listed two.
- **15** undocumented families across 4 crates. The bug listed three (`celesta`,
  `pizzbass`, and orchestral2's set); it did not mention `-orchestral`'s `celens`,
  `harpsi`, `mutetpt` and `vlnens`.

That is the bug's own thesis — a hand-maintained list drifts, and the reported item is
evidence of the gap rather than its extent — confirmed on itself.

**Why a separate module and not a wider `licensing.rs`.** The bug says not to widen it and
is right: licensing asks "is the attribution guide complete?" and deliberately skips CC0
crates, because CC0 waives credit. This asks "has a crate's inventory outgrown its own
documentation?", which applies to CC0 crates equally — four of the five crates missing a
provenance file are CC0. One predicate answering both questions would answer neither.

**The nine filed items.**

1. `-musescore` celesta — added to the README table, the crate description and the new
   `PROVENANCE.md`.
2. `-musescore` `PROVENANCE.md` — written, with the `MS Basic.sf3` revision and SHA-256
   transcribed from `prepare.py`.
3. `-gong` — `NOTICE` now names the two works used (Freesound 261890 soft, 261893 loud)
   and carries a single canonical credit string to copy.
4. `-ydp-grand` README — now names **roberto@zenvoid.org** and says to copy the `NOTICE`,
   not the summary.
5. `-ccby` `PROVENANCE.md` — regeneration command corrected (`musicbox` ships in
   `-orchestral2`, not here), and the missing checksums added: SHA-256 of all 20 committed
   source WAVs, so `prepare.py`'s "exact pack IDs/SHAs" claim is now true.
6. "CC0 bank N" — rewritten as "bank select CC0=N" in **six** files. The bug named two
   crates; the phrasing had also spread to `-headroom`, `-honkytonk` and `-vcsl-kawai`.
7. `-strings` pizzbass — README row added, `PROVENANCE.md` written, and the regeneration
   command corrected to `--only=cellosolo,dbass,pizzbass` (it rebuilt 32 of 40 files).
8. `-orchestral2` — `PROVENANCE.md` written covering all 14 families.
9. GM 10 music box — the verified eleven-sound table transcribed into
   `-orchestral2/PROVENANCE.md`, including the near-miss warning about pack 40874, so the
   external check is never repeated.

Every pin in the five new files is transcribed from `prepare.py`'s own pinned tables
(`VSCO_REV`, `VCSL_REV`, `MUSESCORE_REV` + SHA-256, the FreePats archive hashes) or from
this bug's verified music-box table — nothing was inferred.

**Fails before / passes after.** The oracle is red on the pre-fix tree, naming all five
crates and all fifteen families; green after. It stays honest going forward because it
reads the filesystem, not a list: a new bank cannot ship without a row.

**Gates.** `cargo test --release -p ferrosintesis` 661 passed / 0 failed / 26 ignored (+4
doc-tests); clippy `-D warnings` clean; `cargo fmt --check` clean. No audio changed —
documentation, one new test-only module, and five `include` lists.

## Notes

- All items were confirmed against file contents during the KILN-00060 audit and are
  quoted above; none was inferred.
- Upstream archives were not re-fetched, so no claim is made about whether the pinned
  bytes still match upstream.
