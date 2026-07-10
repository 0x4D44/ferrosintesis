# Bugs — `bugs/` directory ledger

**Purpose.** One markdown file per bug under `bugs/`, the filename == the bug
ID; deltic assembles the ledger in memory by globbing `bugs/*.md`. There is
**no master table** by design, and **there is no `BUGS.md` — never create one.**

**ID grammar.** `PREFIX-TYPE-HOST-NNNNN`.
- **PREFIX** — this repo's acronym: `MM`.
- **TYPE** — `BUG` in this ledger; the sibling `reqs/` ledger mints `REQ`
  (see `reqs/README.md`). Both ledgers share one ID parser, so deltic never
  inspects the token.
- **HOST** — the minting machine's hostname, uppercased with every non
`[A-Z0-9]` char stripped, **not truncated**.
- **NNNNN** — a per-host sequence, zero-padded to at least 5 digits.
- Legacy `PREFIX-NNNNN` ids (pre-conversion) remain valid, verbatim, forever.

**Per-host allocation.** To raise a bug: derive HOST at runtime
(`echo %COMPUTERNAME%` on Windows, `hostname` on Linux/WSL), list the existing
`MM-BUG-<HOST>-*` files, take `max(NNNNN)+1`, and commit that one new
file. No central allocator, no lock. **Caveat (R-SAMEHOST):** two actors
sharing a HOST token (worktrees on one box, a Win+WSL pair with the same
hostname) can mint the same id from stale views — this surfaces **loudly** as
an add/add conflict at integration, never the silent collision of the old
highest+1 scheme. The resolver renumbers.

**States & transitions.** `Open → Blocked → Fixed → Closed`, each dated and
attributed in the append-only `State history:` line. State is a **field inside
the file** (`- **State:** …`) — never rename a file to change its state.

**Two-eyes rule.** A bug moves to `Closed` only after a second pair of eyes
verifies the fix (regression test green, root cause understood).

**Priority vs severity.** `Priority` is fix urgency (`Must` / `Should` /
`Could`). `Severity` is user impact (`Critical` / `High` / `Medium` / `Low`).
Automation picks by priority first, then severity; malformed or missing
priority is automation-ineligible until corrected.

**Ownership.** The current owner lives in the bug file. `Owner role: human`
parks automation indefinitely for a named human owner. `Owner role: fix` and
`Owner role: verify` are leased automation claims; every automation owner must
carry the matching `Owner run`, `Owner host`, `Owner branch`, `Owner base`,
timestamps, and, for verify owners, `Owner fingerprint`. The unowned marker is
the ASCII hyphen `-` in every owner field. Partial, blank, or inconsistent owner
data is treated as malformed and skipped by automation.

**Attempts and parking.** `Attempts: fix=N, doubt=N, indeterminate=N` records
durable unattended retry history. `Held branch` preserves useful fixer work that
needs human follow-up. `Verify retry after` temporarily parks indeterminate
verification without blocking future fix attempts. `Legacy fixed run` is set on
pre-schema `Fixed` bugs so the verify loop has explicit provenance.

**File format.** Each `bugs/<ID>.md`:

```markdown
# MM-BUG-HOST-00001 — Short title

- **State:** Open
- **Priority:** Should
- **Severity:** High
- **Area:** ui
- **Raised:** YYYY-MM-DD
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
- **State history:** Open (YYYY-MM-DD, raised by …) → Fixed (YYYY-MM-DD, `sha`)

## Observation
<symptom, repro, expected vs actual>

## Fix
<accepted fix summary and verification notes>

## Notes
<other notes, links, failed attempts>
```

> This ledger was bootstrapped by `deltic bugs init`. Edit it freely — it is your
> repo's own copy, not a fleet-managed cache.

Deltic appends successful `### Fix summary (...)` and `### Verification summary (...)`
sections under `## Fix`. Failed autonomous attempts still append `### Fix attempt
summary (...)` under `## Notes`. Older ledgers may have `### Fix summary (...)`
under `## Notes`; the Repos browser treats that legacy content as Fix prose. The
modeled header fields and `State history` remain the machine-readable ledger truth.
