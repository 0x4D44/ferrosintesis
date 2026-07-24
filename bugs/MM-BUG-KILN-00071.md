# MM-BUG-KILN-00071 — licensing.rs validates crate-name substrings, not actual attribution content

- **State:** Open
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

## Notes

- The shipped attribution is correct; this is a test-quality defect. Severity Medium
  rather than High for that reason.
- Same class as MM-BUG-KILN-00023 ("BAR_FULL anti-clone threshold has no failing negative
  anchor"): a guard nobody has tried to defeat tends not to hold. The lesson generalises —
  when adding an oracle, write the adversarial document that *should* fail it.
