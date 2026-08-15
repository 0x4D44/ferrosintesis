# MM-BUG-NMI-00003 — sample_output_path binds repo_root=REPO_ROOT at import, so patching REPO_ROOT never redirects writes

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample tooling / output path resolution
- **Raised:** 2026-08-15T13:03:50Z
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
- **State history:** Open (2026-08-15T13:03:50Z, raised via `deltic bugs new`)

## Observation

`tools/ferrosintesis-samples/prepare.py` declares

```python
def sample_output_path(filename, repo_root=REPO_ROOT):
```

The default is evaluated **once, at import**. So `mock.patch.object(prepare,
"REPO_ROOT", tmp)` — the obvious way to redirect a bake at a scratch directory —
does not redirect anything: every call that omits `repo_root` still resolves under
the real repository, and the bake writes into the working tree.

Observed on 2026-08-15 while fixing MM-BUG-KILN-00182. A test drove `main()` with
`REPO_ROOT` patched to a `TemporaryDirectory` and, against deliberately-broken code
that skipped the output pre-flight, regenerated samples into
`crates/ferrosintesis-samples-core/samples/` and
`crates/ferrosintesis-samples-ccby/samples/` of the live worktree. `git status`
confirmed the modifications; they were restored by hand.

Expected: patching `REPO_ROOT` redirects every path the module derives from it.
Actual: it redirects only call sites that pass `repo_root` explicitly, and there is
nothing at the call site to show which those are.

The existing `HeadroomOutputInventoryTest` patches `REPO_ROOT` too. It is safe only
because it *also* mocks `write_wav_mono` — that is, by accident of a second
precaution, not because the patch works.

## Fix

<unfixed — raised only>

Drop the early-bound default: take `repo_root=None` and resolve `repo_root or
REPO_ROOT` inside the body, which reads the module attribute at CALL time and makes
the patch behave as every caller already assumes. Then audit the module for other
`=REPO_ROOT` / `=SOME_DIR` defaults with the same shape — `EASTMAN_SRC` and
friends are module-level constants derived from `REPO_ROOT` at import and have the
identical problem for anyone patching it.

A regression is easy and worth having: patch `REPO_ROOT` to a temp dir, call the
path helper with no explicit root, and assert the result is under the temp dir.

## Notes

- Severity is about blast radius, not subtlety: the failure mode is a test writing
  into the tracked sample crates, which is how a stale or wrong asset gets committed
  without anyone deciding to.
- Related in spirit to MM-BUG-KILN-00182 / MM-BUG-KILN-00191, which this was found
  while fixing, but independent of both: those are about *which* families get
  pre-validated, this is about *where* the writes land.
- Estimated effort: Small.

