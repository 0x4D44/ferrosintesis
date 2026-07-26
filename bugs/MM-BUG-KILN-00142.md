# MM-BUG-KILN-00142 — Grand recipe guard is a substring check, so a wrong fenced command still passes

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** testing / provenance
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
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=claude-opus-5@high) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T151417Z-p52260-n404105000-c1 branch=task/bug-MM-BUG-KILN-00142-run-fix-20260726T151417Z-p52260-n404105000-c1 code=a80da2b81591fcd7f4d1e0ea7ef3534044ad9695 gate=manual)

## Observation

**Symptom.** The oracle added to keep the packaged grand regeneration recipe correct only checks that the scoped command appears SOMEWHERE in each document, so a doc whose primary fenced recipe is the wrong (unscoped) command still passes.

`tools/ferrosintesis-samples/test_prepare.py:1044-1056`:

    class GrandRegenerationRecipeTest(unittest.TestCase):
        COMMAND = "python tools/ferrosintesis-samples/prepare.py --only=grand"

        def test_packaged_grand_docs_use_the_scoped_command(self):
            crate = os.path.join(prepare.REPO_ROOT, "crates", "ferrosintesis-samples-grand")
            for name in ("README.md", "PROVENANCE.md"):
                with self.subTest(name=name):
                    with open(os.path.join(crate, name), encoding="utf-8") as f:
                        self.assertIn(self.COMMAND, f.read())

`assertIn` over the whole file cannot distinguish "the recipe a maintainer will copy" from "the string is mentioned in passing". Both documents currently discuss the bare invocation too, legitimately, to explain that it is the full multi-bank workflow (`crates/ferrosintesis-samples-grand/README.md:23`, `PROVENANCE.md:76`). So a future edit that promotes the bare command back into the fenced code block, while leaving the scoped command anywhere in prose, keeps this test green and reintroduces exactly the defect MM-BUG-KILN-00135 reported.

**Expected.** The guard pins the command a maintainer would actually run - the fenced recipe block - not the presence of a substring.

**Actual.** Any occurrence anywhere satisfies it.

**Provenance.** Split out of MM-BUG-KILN-00135 during its independent two-eyes verification. The reported defect IS fixed - both packaged grand documents now carry `--only=grand` (`README.md:21`, `PROVENANCE.md:69`) - and 00135 was closed. This is the guard-quality residual.

**Same class as three already handled this session.** MM-BUG-KILN-00071/00110/00111/00115 were all `contains`-shaped credit checks satisfiable by text that credits nobody, and MM-BUG-KILN-00132 was a documentation guard that hardcoded a boundary instead of deriving it. The repo's CLAUDE.md states the rule directly: "assert against something derived from the source, never against a second hand-written list", and "write the adversarial document that SHOULD fail your oracle, and check that it does".

**Fix direction.** Extract the fenced code block(s) from each document and require the scoped command to be the one inside the primary regeneration fence, rather than searching the whole file - then add the adversarial fixture that this bug describes (a document whose fence holds the bare command and whose prose mentions the scoped one) and prove it goes red. MM-BUG-KILN-00132's fix is the model to copy: it pairs a derived assertion with a `#[should_panic]` negative control feeding a deliberately wrong value.

Two smaller notes, deliberately not filed separately:
- The guard is hardcoded to the grand crate rather than derived from the set of sample crates that document a `prepare.py` recipe, so a second crate with a wrong recipe is unguarded.
- `crates/ferrosintesis-samples-clavinet` documents no regeneration command at all despite being a `prepare.py` bank; whether that is a gap or deliberate is a judgement call for the owner, not a defect this pass can assert.

## Fix

<unfixed — raised only>

## Notes
