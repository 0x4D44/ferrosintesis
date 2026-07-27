# MM-BUG-KILN-00152 — Orchestral2 publishes a no-op banjo regeneration recipe

- **State:** Fixed
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
- **Held branch:** host-local:KILN:task/bug-MM-BUG-KILN-00152-run-fix-20260727T090201Z-p9812-n987723200-c60-code-1785143390172
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-07-27, deltic:auto role=fix run=fix-20260727T090201Z-p9812-n987723200-c60 branch=task/bug-MM-BUG-KILN-00152-run-fix-20260727T090201Z-p9812-n987723200-c60 code=8366bf79d414 gate=cargo model=codex@xhigh)

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

<unfixed — raised only>

### Fix summary (2026-07-27, deltic:auto run=fix-20260727T090201Z-p9812-n987723200-c60 code=8366bf79d414 gate=cargo)

Agent-reported summary: Fixed MM-BUG-KILN-00152, where the published orchestral2 banjo regeneration recipe pointed maintainers at a successful no-op. I reproduced the original observation: prepare.py --only=banjo exited 0 and printed only the sample-table header. The selector now rejects banjo with the real banjo_extract.py command and rejects unknown families before any bake path can report success. The orchestral2 README and PROVENANCE now distinguish non-banjo prepare.py families from the standalone banjo extractor. The focused regression and the surrounding sample-tool test file are green.

Root cause: prepare.py accepted arbitrary --only family names and treated an empty selected work set as success; banjo was still listed as a family in provenance/package metadata but its active bake path had been intentionally moved to banjo_extract.py.

Changed:
- tools/ferrosintesis-samples/prepare.py validates --only selectors against families with active prepare.py recipes and gives banjo a specific extractor hint.
- tools/ferrosintesis-samples/test_prepare.py adds regressions for --only=banjo, an unknown family, and the packaged orchestral2 banjo command.
- crates/ferrosintesis-samples-orchestral2/PROVENANCE.md and README.md document banjo_extract.py instead of attributing every WAV to prepare.py.

Tests:
- Before the fix: python -m unittest test_prepare.PrepareOnlySelectionContractTest test_prepare.Orchestral2RegenerationRecipeTest failed 3 tests.
- After the fix: python -m unittest test_prepare.PrepareOnlySelectionContractTest test_prepare.Orchestral2RegenerationRecipeTest passed 3 tests.
- After the fix: python -m unittest test_prepare passed 76 tests.
- After the fix: prepare.py --only=banjo and prepare.py --only=notafamily both exit nonzero with clear errors.

Left alone:
- No files under bugs/ were edited.

## Notes

The retained Opus source is an intentional size/fidelity tradeoff; this bug does
not require bit-exact reproduction from the unavailable original lossless take.
It tracks the false command and false producer attribution.
