# MM-BUG-KILN-00062 — Warm archive caches bypass the sample generator's pinned SHA-256

- **State:** Open
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

## Notes

- Current packaged WAVs are structurally valid and tracked. This bug concerns
  reproducible provenance, not a claim that today's payloads are altered.
- The security, reliability, and devil's-advocate passes independently confirmed the
  bypass. No existing bug or requirement matched it.
- The helper is shared by other archive-backed banks, so the fix should cover every
  caller rather than special-case electric bass.
- Upstream archive contents and licence records were not fetched during this read-only
  review and remain externally unverified.

