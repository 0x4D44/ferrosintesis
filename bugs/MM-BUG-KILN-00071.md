# MM-BUG-KILN-00071 — licensing.rs validates crate-name substrings, not actual attribution content

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
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
- **State history:** Open (2026-07-24 — split from MM-BUG-KILN-00060 on its independent
  two-eyes closure. Found by Codex gpt-5.6-sol, which refuted the strength of that bug's
  regression coverage; recorded by Claude Opus 4.8 (1M), who wrote the oracle.)
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). The oracles now check that each bank is
  CREDITED, not merely mentioned: its licence is stated, it sits under its own licence
  heading, and a distinctive token from its own NOTICE travelled into both documents.
  The bug’s verbatim repro now fails. Evidence under "Fix landed" below. Awaits
  independent two-eyes closure.)
  → Closed (2026-07-24, independently verified by Codex GPT-5.6-Sol; fails-before,
  passes-after, root-cause review, and green gate evidence are recorded in
  `wrk_journals/2026.07.24 - JRN - Fixed queue two-eyes closure pass.md`.)

## Observation

**Symptom.** The licensing oracles can be fully satisfied by a document that credits
nobody.

**Repro** (performed by the verifier). Replace `crates/ferrosintesis/README.md` and
`crates/ferrosintesis/NOTICE` with nothing but the ten attribution-bearing crate names,
one per line — 10 words in each file, no authors, no licence text, no URLs — then:

```
cargo test -p ferrosintesis licensing::tests
```

All three oracles **pass**.

**Root cause.** Every assertion is a substring test:

- `readme_names_every_attribution_bearing_sample_bank` → `readme.contains(&krate)`
- `parent_notice_is_packaged_and_names_every_attribution_bearing_bank` →
  `notice.contains(&krate)`
- `every_attribution_bearing_sample_bank_ships_a_notice` → `text.trim().len() > 40`

These prove a bank is **mentioned**. The licence requires it to be **credited** — the
author named, the licence identified, the notice reproduced. Nothing checks that.

**Impact is on the guard, not on today's shipped files.** The README table and the
parent `NOTICE` landed by KILN-00060 are correct and complete. The defect is that they
could be gutted — by a careless edit, a bad merge, or a well-meaning "tidy the README"
pass — and the build would stay green. That is precisely the drift KILN-00060 existed to
stop, so the fix does not fully deliver its own stated purpose.

## Fix

Check per-bank **blocks**, not bare occurrence. For each attribution-bearing crate,
take the span of the parent `NOTICE` from that crate's mention to the next crate's
mention, and require it to:

- contain the crate's declared licence in a normalised form (accept both the SPDX
  `CC-BY-4.0` and prose `CC BY 4.0` spellings — the repo uses both, see KILN-00069), and
- carry a real body of credit text rather than a bare name (a minimum token count
  defeats the word-list case; pick the threshold from the *shortest* legitimate block
  currently shipped, then subtract a margin).

Apply the same per-row check to the README table: each row must carry the crate **and**
its licence.

Stronger still, if it proves practical: require some distinctive token from each asset
crate's own `NOTICE` — a source URL, or a credited proper noun — to appear in the parent
`NOTICE`, which is a direct test that the credit actually travelled. Note that not every
crate's `NOTICE` carries a URL (`-clavinet` and `-musescore` do not), so a URL-only rule
would false-negative on those two.

Calibrate the thresholds against the current files first, and confirm the strengthened
oracle actually fails on the verifier's bare-name-list document.

## Fix landed (2026-07-24)

**Approach — and a deliberate departure from the suggested fix.** The bug proposed a
minimum token count per block. I did not implement that: a token floor is a proxy for
"real credit" that any 40 words of prose satisfies, and calibrating it against the
shortest shipped block would leave it one careless edit from meaninglessness. The route
taken subsumes it — **require the licensor's own words to travel**.

`crates/ferrosintesis/src/licensing.rs` now derives, per attribution-bearing bank:

- **its distinctive credit tokens** — quoted work titles and source URLs taken from the
  bank's OWN `NOTICE` (the licence's own `creativecommons.org` URL is excluded: it appears
  in every notice, so it would let an uncredited bank pass). A crate name is our
  identifier and proves nothing; a work title is the licensor's and cannot be reproduced
  by accident.
- **the licence section it sits under** in the parent `NOTICE`, so a bank filed under
  another bank's licence heading is caught. Sections rather than name-to-name spans
  because several banks legitimately share one credit body (the three MuseScore-lineage
  crates do), and a span check would read an empty block for all but the last of a group.

The three oracles then require, for every attribution-bearing bank: the README row names
it AND states its licence AND repeats one of its credit tokens; the parent `NOTICE` names
it under a heading carrying its own licence AND repeats one of its tokens; and the bank's
own `NOTICE` names a work or cites a source AND states its licence. Both SPDX
(`CC-BY-4.0`) and prose (`CC BY 4.0`) spellings count — the repo uses both (KILN-00069).

**Fails before / passes after.** The verifier's repro — README and `NOTICE` replaced by
the ten crate names, one per line — previously passed all three oracles. It now fails two
of them ("10 README row(s) name a bank without stating which licence applies", "10 bank(s)
… under a licence heading that is not their own"). A second, subtler probe isolates the
core guard: keeping correct licences and section headings but stripping all licensor
credit fails with "none of the credit from their own NOTICE travelled with them", naming
each bank and the tokens it looked for (`"Salamander Grand Piano V3"`, `"CdM Gamelan
Sample Library"`, …). Both documents were restored byte-for-byte afterwards.

The third oracle correctly stays green under both probes — it checks the per-crate NOTICE
files, which neither probe touched. That is the intended split, not a gap.

**Shipped files were already correct**, as the bug said: all three oracles pass on the
real documents, so this changes no user-visible text. The module is entirely `#[cfg(test)]`,
so there is no shipped-code change and no render impact.

**Gates.** `cargo test -p ferrosintesis licensing` 3 passed — and also 3 passed under
`--no-default-features`, which is the KILN-00020 trap this module exists to avoid (an
oracle that evaporates with a feature flag). Full crate: 659 passed / 0 failed / 26
ignored (+4 doc-tests); clippy `-D warnings` clean; `cargo fmt --check` clean.

## Notes

- The shipped attribution is correct; this is a test-quality defect. Severity Medium
  rather than High for that reason.
- Same class as MM-BUG-KILN-00023 ("BAR_FULL anti-clone threshold has no failing negative
  anchor"): a guard nobody has tried to defeat tends not to hold. The lesson generalises —
  when adding an oracle, write the adversarial document that *should* fail it.
