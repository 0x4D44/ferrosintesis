# MM-BUG-KILN-00062 — Warm archive caches bypass the sample generator's pinned SHA-256

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample generation / provenance
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
- **State history:** Open (2026-07-24, raised by Codex during the coverage-ledger review of `crates/ferrosintesis-samples-bass/`)
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). The member cache is now content-addressed: a
  manifest binds every extracted member to the archive PIN, and anything short of a proof
  rebuilds. Covers all five archive-backed banks, not just electric bass. Nine tests, seven
  of which fail on the old code. Evidence under "Fix landed" below. Awaits independent
  two-eyes closure.)
  → Closed (2026-07-24, independently verified by Codex GPT-5.6-Sol; fails-before,
  passes-after, root-cause review, and green gate evidence are recorded in
  `wrk_journals/2026.07.24 - JRN - Fixed queue two-eyes closure pass.md`.)

## Observation

**Symptom.** The bass regeneration path claims to use SHA-256-pinned FreePats archives,
but a normal warm cache returns before any hash verification. Stale or altered extracted
WAVs can therefore be rebaked into the tracked asset crate as if they came from the
pinned archives.

**Expected.** Every regeneration should establish that cached source members correspond
to the pinned archive, or to a trusted per-member manifest derived from it. A corrupt
cache should be invalidated and rebuilt.

**Actual.** `tools/ferrosintesis-samples/prepare.py:1095-1119` implements
`ensure_archive_sources()`. Lines 1104-1105 return solely because every destination path
exists; the archive SHA-256 check at lines 1110-1112 is then unreachable. The bass path
calls the helper for both archives at lines 1128-1133, uses a persistent shared OS-temp
cache rooted at lines 2493-2495, reads the cached members at line 2653, and overwrites
the packaged WAVs at line 2680.

This has three concrete failure modes:

- a wave-valid but altered cached member passes `read_wav()` and is silently rebaked;
- a future archive pin with unchanged member names reuses the old extracted files;
- a truncated member aborts during the later read instead of self-healing.

The two documented archive hashes at
`crates/ferrosintesis-samples-bass/PROVENANCE.md:9-14` match the constants in source.
The defect is that warm-cache control flow does not enforce them.

## Fix

Make archive/member caching content-addressed. Always validate the cached archive and
re-extract the exact members, or retain and validate a trusted per-member hash manifest.
On a hash or member mismatch, remove/refetch once atomically and rebuild the extracted
cache.

Add focused cache tests for a wave-valid altered member, a truncated member, a changed
pin with unchanged member names, and a bad cached archive. Each should either restore
the pinned bytes or fail without touching tracked output.

## Fix landed (2026-07-24)

**Code** (`tools/ferrosintesis-samples/prepare.py`). `ensure_archive_sources` is now three
steps, and the warm path is a PROOF rather than an existence check:

- `cached_members_match(src, url, sha256, member_map)` reads a manifest written beside the
  archive (`<archive>.members.json`) recording the archive pin plus each extracted member's
  SHA-256. It returns True only if the manifest's pin equals the pin being asked for, it
  covers every requested member, and every member on disk still hashes to its recorded
  value. Anything else — no manifest, unreadable manifest, different pin, missing, altered
  or truncated member — returns False and the cache is rebuilt.
- `rebuild_archive_cache(...)` fetches if needed, verifies against the pin, extracts, copies
  members. A local archive whose digest does not match is removed and re-fetched **once**
  (the common cause is a truncated or superseded download); a second mismatch raises, because
  at that point the served bytes disagree with the pin and that is not ours to paper over.
- `write_member_manifest(...)` records the pin and member hashes, written to a `.part` file
  and `os.replace`d so an interrupted run cannot leave a manifest that vouches for nothing.

`sha256_file` reads in 1 MiB chunks — these archives are hundreds of MB and the old code
did `open(arc, "rb").read()` into memory.

**Every archive-backed bank is covered**, per this bug's own note: the five call sites are
Spanish guitar, electric bass finger, electric bass pick, bagpipe and honky-tonk, all
through the one helper. Nothing was special-cased to electric bass.

**Legacy caches are untrusted by construction.** No cache on any machine has a manifest
today, so the first run after this lands rebuilds each archive's members once — which is
the correct behaviour, not a cost to avoid: those are exactly the caches whose provenance
this bug says cannot be established.

**Regression** — nine tests in `tools/ferrosintesis-samples/test_prepare.py`, driving the
real `ensure_archive_sources` with fetch/extract stubbed, so they test the cache DECISION
with no network and no 7z. `rebuilt` counts stub invocations: 0 means the warm cache was
trusted, 1 means rejected and rebuilt.

**Fails before / passes after**, each behaviour proved against the code it replaces:

- Restoring the old `os.path.exists` warm path fails **5**: altered member, truncated
  member, changed pin with unchanged member names, legacy cache with no manifest, corrupt
  manifest. (The bug's four scenarios plus the legacy case, which is every existing cache.)
- Restoring the single-attempt archive verify fails the other **2**: the corrupt local
  archive is not re-fetched, and the "still mismatches after one refetch" path never raises.

The remaining two (valid warm cache reused; missing member rejected) pass on both, as they
should — the old code did rebuild when a member was absent. That is the one case it got
right, and it is pinned so the fix cannot lose it.

**Gates.** `python -m unittest test_prepare` — 27 passed (18 pre-existing + 9 new). No Rust
code changed.

**Noted, not fixed** (scratchpad, dated today): `test_prepare.py` is not run by any gate —
`.deltic-integrate.toml`'s `workspace` component lists `tools/` in its paths but every
command in its gate is cargo, so these tests would have landed unexecuted by anything but
me. Same shape as MM-BUG-KILN-00070.

## Notes

- Current packaged WAVs are structurally valid and tracked. This bug concerns
  reproducible provenance, not a claim that today's payloads are altered.
- The security, reliability, and devil's-advocate passes independently confirmed the
  bypass. No existing bug or requirement matched it.
- The helper is shared by other archive-backed banks, so the fix should cover every
  caller rather than special-case electric bass.
- Upstream archive contents and licence records were not fetched during this read-only
  review and remain externally unverified.

