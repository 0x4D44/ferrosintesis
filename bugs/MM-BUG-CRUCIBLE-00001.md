# MM-BUG-CRUCIBLE-00001 — Published YDP notices omit named performer Dr. Mikhail Krishtal

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** packaging / licensing
- **Raised:** 2026-07-31
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
- **State history:** Open (2026-07-31, raised via `deltic bugs new`) -> Fixed (2026-07-31, deltic:auto role=fix run=fix-20260731T061755Z-p76200-n609412900-c1 branch=task/bug-MM-BUG-CRUCIBLE-00001-run-fix-20260731T061755Z-p76200-n609412900-c1 code=d305249e287da01fc300c8a3ff2f44ab6ca3ff57 gate=manual) -> Closed (2026-07-31, claude-opus-5; independent two-eyes verification on trunk `ddd71e6`. I did not fix this — the fixer was `deltic:auto role=fix` with GPT-5.6 as the authoring model on `d305249` — so I am eligible as the second pair of eyes. ORIGINAL OBSERVATION re-checked on the fix-bearing tree: all four distributed documents the report named now carry the supplied performer credit — `crates/ferrosintesis-samples-ydp-grand/NOTICE`, that crate's `PROVENANCE.md`, the consolidated `crates/ferrosintesis/NOTICE`, and the licensing table in `crates/ferrosintesis/README.md`. I did NOT take the retained evidence file on trust: I fetched the authoritative FreePats page cited in the report and it reads "The original sound samples were performed by computer and specifically recorded for OLPC by Dr. Mikhail Krishtal, Director of Music Research and Production, and his team at Zenph Studios", under CC BY 3.0 — so `src/upstream_licenses/ydp_grand_freepats_credits_20260731.md` is a faithful transcription of the upstream record and not a restatement of our own already-incomplete notice, which is exactly the inversion the report asked for. TWO-SIDED: reverse-applying only the four credit documents (leaving the oracle and the evidence file intact) makes `licensing::tests::ydp_documents_reproduce_retained_upstream_credits` FAIL, naming all four documents and all three missing fragments; restoring them makes it pass. The requested negative control `ydp_credit_oracle_rejects_notice_missing_krishtal` exists and holds a notice that keeps Roberto, the work title, the source URL and the recording context but drops Krishtal. Repo gate green on the exact tree: `cargo fmt --all --check`, both clippy configurations with `-D warnings`, `cargo test -p ferrosintesis --no-default-features` (714 passed), `cargo test --workspace` (849 passed in the lib, 0 failures), and `python3 -m unittest discover -s tools/ferrosintesis-samples`. Note on the oracle's bar, not a residual: it asserts substring presence of the required fragments, so it certifies that the names ship, not that they read as a sentence — a strictly stronger bar than the crate-name check MM-BUG-KILN-00071 holed. No residual.)

## Observation

**Symptom.** The authoritative FreePats YDP page identifies Dr. Mikhail
Krishtal, Director of Music Research and Production, and his Zenph Studios team
as the performers and recordists of the original Yamaha Disklavier Pro samples:
<https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html>.

The independently publishable package instead credits only the SoundFont
producer, `roberto@zenvoid.org`, plus Zenph Studios and OLPC generically:

- `D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-005314\crates\ferrosintesis-samples-ydp-grand\NOTICE:4`
- `D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-005314\crates\ferrosintesis-samples-ydp-grand\PROVENANCE.md:20`

The consolidated parent credits repeat the omission at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-005314\crates\ferrosintesis\NOTICE:60`.

**Expected.** A distributed copy preserves the supplied name of the original
performer/recordist. CC BY 3.0 section 4(b) requires the Original Author's name
when supplied:
<https://creativecommons.org/licenses/by/3.0/legalcode.en>.

**Actual.** A distributor can ship both the standalone sample crate and the
default parent crate without Dr. Krishtal's supplied credit.

**Concrete fix.** Add Dr. Mikhail Krishtal and his Zenph Studios team's
performance/recording role to the packaged `NOTICE` and `PROVENANCE.md`, then
carry that credit into the parent `NOTICE` and licensing guide. Strengthen the
licensing oracle so required identities come from retained upstream evidence,
not from the already-incomplete local `NOTICE`. Add a negative control that
removes Krishtal while retaining Roberto, the work title, and the source URL.

**Effort:** Small.

## Fix

Landed in `d305249`: the performer/recordist credit was added to the packaged
`NOTICE` and `PROVENANCE.md`, carried into the parent `NOTICE` and the README
licensing table, and the licensing oracle rewritten to derive its required
identity fragments from a retained upstream credit record
(`crates/ferrosintesis/src/upstream_licenses/ydp_grand_freepats_credits_20260731.md`)
rather than from the local notice. A negative control rejects a notice that keeps
Roberto, the work title and the source URL but drops Dr. Krishtal.

## Notes

This is not covered by Draft `MM-REQ-KILN-00144`, which concerns exact source
SHA-256 pins. Closed `MM-BUG-KILN-00069` added the omitted SoundFont producer,
Roberto; it did not census the authoritative YDP page or cover Dr. Krishtal.

Static code review only. No application or test harness was run.
