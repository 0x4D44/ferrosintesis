# MM-BUG-KILN-00110 — A crate's own name still counts as a credit token, so a gutted NOTICE passes

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** licensing oracles / attribution
- **Raised:** 2026-07-25
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
- **State history:** Open (2026-07-25, raised by Claude Opus 4.6 from an adversarial re-check of the MM-BUG-KILN-00071 fix while landing MM-REQ-KILN-00029. Found by re-implementing the predicate and running it against a document built to defeat it, per the repo's "write the adversarial document that *should* fail your oracle" rule.)

## Observation

MM-BUG-KILN-00071 is closed, and its verbatim repro does now fail as intended. But the fix
moved the root of trust one hop rather than closing the hole: the parent README and parent
NOTICE are checked against **each crate's own `NOTICE`**, and that per-crate NOTICE is
guarded only by three weak assertions (`crates/ferrosintesis/src/licensing.rs:374-388` —
`text.trim().len() > 40`, `!credit_tokens(&text).is_empty()`, `names_license`).

The predicate is the problem. `credit_tokens`
(`crates/ferrosintesis/src/licensing.rs:142-166`) accepts **any** quoted run of ≥4
characters that contains no newline. It has no notion of "licensor-owned". The doc comment
at `:136-138` asserts that a crate name "proves nothing about attribution" and that a work
title or source URL "cannot be reproduced by accident" — but nothing in the code enforces
that distinction.

**Expected.** A document that credits nobody fails the attribution oracles. That is the
stated purpose of MM-BUG-KILN-00071's fix.

**Actual.** Set `crates/ferrosintesis-samples-ccby/NOTICE` to:

```
ferrosintesis-samples-ccby audio is licensed CC BY 4.0. See the "ccby" bank.
```

The sole extracted token is `ccby` — a **substring of our own crate name**. Gut the parent
README row to `` | `ferrosintesis-samples-ccby` | CC BY 4.0 | `` and the parent NOTICE
section to a rule / `CC BY 4.0` / rule heading plus the bare crate name, and all three
oracles stay green while `tim.kahn`, `iternetcone`, both work titles and both pack URLs are
gone. That is MM-BUG-KILN-00071's symptom verbatim ("the licensing oracles can be fully
satisfied by a document that credits nobody").

Confirmed by re-implementing `credit_tokens` / `mentions` / `names_license` faithfully from
the current source and running them over the constructed documents; the run reported credit
"travelling" into both the README and the parent NOTICE with no author, title or URL present
anywhere. **The check was on a faithful re-implementation, not by mutating the tracked
NOTICE files, so the exact in-tree behaviour is inferred from the predicate rather than
observed end-to-end.**

## Fix

A one-line predicate closes the demonstrated break, and it is derivable rather than
hand-maintained: reject any candidate token that is a substring of the crate name, of
`ferrosintesis`, or of the licence spellings. The crate name comes from the directory and
the licence from the manifest, so no list is introduced and no guard inherits the defect.

Land it with the gutted document above as a fixture that must go **red** — the repo's rule
is that a derived oracle is only as good as its enumeration predicate, and the way to find
out is to write the document that should fail it and check that it does.

## Notes

- Related but distinct: MM-BUG-KILN-00111 (a one-token manifest edit removes a crate from
  these oracles entirely). Either one alone defeats the attribution guarantee; they should
  probably be fixed together.
- Not a licence-compliance failure today. Every `NOTICE` in the tree currently carries real
  author and title text; this is about what the oracle would *let through*, which matters
  because the attribution documents are hand-maintained and the oracle is the only thing
  standing between a careless edit and a published crate that credits nobody.
