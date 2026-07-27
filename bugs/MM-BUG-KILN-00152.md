# MM-BUG-KILN-00152 — Orchestral2 publishes a no-op banjo regeneration recipe

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** orchestral2 / regeneration provenance
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
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=1, doubt=1, indeterminate=0
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=gpt-5.6-sol@high) → Fixed (2026-07-27, deltic:auto role=fix run=fix-20260727T090201Z-p9812-n987723200-c60 branch=task/bug-MM-BUG-KILN-00152-run-fix-20260727T090201Z-p9812-n987723200-c60 code=de95960f899298440bbe24f06bbd548b3139c766 gate=python model=codex@xhigh) → Open (2026-07-27, deltic:auto role=verify run=verify-20260727T165501Z-p9812-n885138800-c96 verified_fix_run=fix-20260727T090201Z-p9812-n987723200-c60 verdict=doubt reason=static-trace-and-rust-gates-all-support-the-fix-but-python-execution-is-blocked model=claude)

## Observation

**Symptom.** The packaged provenance document says every family regenerates with
`python tools/ferrosintesis-samples/prepare.py --only=<family>`, including the
24-file `banjo_*` row at
`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\crates\ferrosintesis-samples-orchestral2\PROVENANCE.md:7`.
That command cannot regenerate banjo.

`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\tools\ferrosintesis-samples\prepare.py:3138`
describes `--only=banjo` as a supported selector. Lines 3216–3220 then explicitly
exclude banjo from the bake, and no later selected-family path dispatches it.
Static control flow reaches `_print_sample_rows([])` and returns success without
touching the 24 outputs. The real producer is the standalone command documented
at
`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\tools\ferrosintesis-samples\banjo_extract.py:26`.

The public README compounds the mismatch at
`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\crates\ferrosintesis-samples-orchestral2\README.md:8`
by saying every WAV was trimmed by `prepare.py`.

**Expected.** Every published regeneration command either produces the named
family or fails clearly before reporting success.

**Actual.** The documented banjo command is a successful no-op, so a maintainer
can mistake stale or missing assets for a completed rebuild.

**Concrete fix.** Give banjo its real family-specific command in packaged
provenance, narrow the generic command to the families it reaches, and make
`prepare.py` reject an unsupported or non-producing `--only` selection. Add a
contract regression for `--only=banjo` and for an unknown family.

## Fix

`prepare.py` now validates `--only` before fetching or baking. It accepts only
families with a producing path, rejects unknown families, and rejects `banjo`
with the exact `banjo_extract.py` command that owns those samples.

The packaged orchestral2 README and provenance now distinguish the standalone
banjo extractor from the non-banjo `prepare.py` recipes. This removes the
successful no-op and the false producer attribution.

Root cause: `prepare.py` accepted arbitrary `--only` values and treated an empty
selected work set as success after banjo generation moved to its standalone
extractor.

Regression coverage:

- `PrepareOnlySelectionContractTest` and
  `Orchestral2RegenerationRecipeTest`: 3/3 passed.
- Full `tools/ferrosintesis-samples/test_prepare.py`: 82/82 passed.
- `python -m py_compile tools/ferrosintesis-samples/prepare.py
  tools/ferrosintesis-samples/test_prepare.py`: passed.

### Verification summary (2026-07-27, deltic:auto run=verify-20260727T165501Z-p9812-n885138800-c96 verified_fix_run=fix-20260727T090201Z-p9812-n987723200-c60 verdict=doubt)

Verifier note: Static trace and Rust gates all support the fix, but Python execution is blocked in this runner so I could not run the Python regression test or the symptom repro that the entire fix lives in. — Worktree == origin/main for all non-bugs paths (git diff --stat origin/main HEAD -- . ':!bugs' empty); fix commit de95960 is on main. RAN: cargo test --workspace = all 57 'test result: ok', 788 passed / 0 failed in ferrosintesis; cargo clippy --workspace --all-targets -- -D warnings = Finished clean; cargo fmt --all -- --check = no output. COULD NOT RUN: every python invocation beyond 'python --version...

## Notes

The retained Opus source is an intentional size/fidelity tradeoff; this bug does
not require bit-exact reproduction from the unavailable original lossless take.
It tracks the false command and false producer attribution.
