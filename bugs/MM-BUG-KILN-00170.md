# MM-BUG-KILN-00170 — The committed-source registry is hand-maintained: 3 of 4 repo-root recording roots are unpinned and invisible to the provenance oracle

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample provenance / oracle enumeration
- **Raised:** 2026-07-29
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
- **State history:** Open (2026-07-29, split from MM-BUG-KILN-00168 during its independent two-eyes closure by Claude Opus 5 on trunk `be161eb`) -> Fixed (2026-07-29, deltic:auto role=fix run=fix-20260729T113244Z-p34508-n560217800-c1 branch=task/bug-MM-BUG-KILN-00170-run-fix-20260729T113244Z-p34508-n560217800-c1 code=ef81ac23702a266ffb2b3b5d8e59d89188b34ae3 gate=manual)

## Observation

Split from MM-BUG-KILN-00168. That bug is correctly fixed and closed: both B1
Opus archives are now digest-pinned and scanned. This is the residual its own
fix note asked for and did not get — a control "so another committed-source root
cannot evade the scan".

`source_dirs()` in
`D:\language\midi-music\crates\ferrosintesis\src\provenance.rs:167` discovers
tool-owned sources by the glob `tools/ferrosintesis-samples/*-src`, but reaches
repo-root first-party archives through a hand-written list:

```rust
const REPO_SOURCE_DIRS: &[&[&str]] = &[&["samples", "b1-upright"]];
```

That list has exactly one entry. The repo-root `samples/` store has **four**
recording roots (`git ls-files samples/`):

| root | tracked files | pinned by a packaged document? |
|---|---:|---|
| `samples/b1-upright` | 2 | yes (both) |
| `samples/acoustic-guitar-eastman-e1d` | 18 | **no — none** |
| `samples/fret-noise-eastman-e1d` | 14 | **no — none** |
| `samples/banjo` | 1 | **no** |

Measured on trunk `be161eb` by hashing every tracked file under `samples/` and
searching the whole repository's `.md` / `.rs` / `.py` / `.toml` text for each
digest. Two of 34 are pinned; 32 are not, including five performance masters we
cannot re-derive: `acoustic-guitar-eastman-e1d/picked.opus`,
`acoustic-guitar-eastman-e1d/plucked.opus`, `banjo/banjo-5string-openG-2026-07-23.opus`,
`fret-noise-eastman-e1d/DR0000_0203.opus` and `fret-noise-eastman-e1d/DR0000_0204.opus`.

**Expected.** `every_committed_source_is_pinned_by_a_packaged_document` covers
every committed bake input, and a newly added committed-source root is covered
on the day it appears rather than when somebody remembers to register it.

**Actual.** Three of the four roots are outside the oracle's enumeration
entirely, so the test passes while 32 committed source files — five of them
irreplaceable masters — have no recorded identity. Adding
`samples/<new-instrument>/` tomorrow repeats this silently.

This is precisely the class `CLAUDE.md` names under "Hand-maintained lists are
the recurring defect here — derive them": the reported item (B1) was evidence the
list was unmaintained, not the specification of the work.

No tampering or output corruption was observed. This is a Low-severity integrity
and reproducibility defect in the enumeration predicate, not in any shipped audio.

## Fix

The `REPO_SOURCE_DIRS` registry was a deliberate judgment call, and the reason is
sound: `samples/` mixes performance masters with derived per-zone cuts
(`*/zones/`, `*/cuts/`), so a blanket `samples/*` glob would sweep in build
output. So the fix is not simply "widen the glob" — it needs a predicate that
distinguishes committed input from derived cut without a second hand-written
list. Options worth weighing:

- derive the roots from `samples/README.md`'s documented per-instrument
  convention, or from a small per-root manifest committed beside the recordings;
- treat every `samples/*/` directory as a source root and pin its masters,
  classifying `zones/` and `cuts/` subdirectories as derived by their own
  documented naming rule;
- keep the registry but add a guard that fails when a `samples/*` root exists
  outside it, so registration is forced rather than remembered.

Whichever is chosen, add the adversarial control MM-BUG-KILN-00168 asked for:
a new committed-source root shaped like `samples/b1-upright/` must not be able to
evade the scan. Per `CLAUDE.md`, write the document that *should* fail the oracle
and check that it does — a derived predicate is still an assumption until it has
been attacked.

Decide alongside draft requirement `MM-REQ-KILN-00144` (publishing known exact
source pins), which covers the publishing half of the same ground.

Estimated effort: Medium.

## Notes
