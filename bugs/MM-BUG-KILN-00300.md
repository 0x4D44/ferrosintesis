# MM-BUG-KILN-00300 — The published CLI package carries no NOTICE, and the licensing oracles' enumeration predicate cannot see it

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/ferrosintesis-cli
- **Raised:** 2026-08-17T22:55:50Z
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
- **State history:** Open (2026-08-17T22:55:50Z, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

**The fact.** `crates/ferrosintesis-cli/` contains no `NOTICE` file, and
`crates/ferrosintesis-cli/Cargo.toml:14` packages only
`["src/**", "examples/**", "tests/**", "README.md", "LICENSE-APACHE", "LICENSE-MIT"]`.
Its `README.md:60-61` handles attribution by pointing at *another package*: "The embedded
audio shipped by the library's asset crates carries its own terms; see the library's
`NOTICE`."

The contrast is immediate. `crates/ferrosintesis/` **does** hold a `NOTICE` and packages it
(`crates/ferrosintesis/Cargo.toml:13`). But `ferrosintesis` has no `[[bin]]` — as its own
manifest comment says (`ferrosintesis-cli/Cargo.toml:10-13`), `cargo install ferrosintesis`
installs nothing. **`ferrosintesis-cli` is the crate that produces the executable**, and by
default that executable has every attribution-bearing sample bank linked into it via
`include_bytes!`.

**Why no oracle caught it.** `crates/ferrosintesis/src/licensing.rs` derives the set it
checks from `default_sample_crates()` (`licensing.rs:55-86`), which parses the
`embedded-samples` feature list out of `crates/ferrosintesis/Cargo.toml`. The documents it
then requires are each bank's own `NOTICE`/`PROVENANCE.md` plus `ferrosintesis/NOTICE` and
`ferrosintesis/README.md` (`licensing.rs:322-337`, `:432-444`). `ferrosintesis-cli` is
structurally outside that enumeration — it is neither a bank named in the feature list nor
the parent library, so no assertion in the module can ever reach it.

**This is the documented recurring defect class, one level up.** CLAUDE.md records that a
derived oracle "is only as good as its enumeration predicate, and the predicate is itself an
assumption" (KILN-00071/00072/00073). Here the predicate is "banks in the feature list, plus
the library". It is a correct predicate for *which banks need crediting* and a wrong one for
*which published packages ship the credited material*.

**Expected.** Either the CLI package carries a `NOTICE` covering the audio its binary
embeds, or a human records the deliberate decision that pointing at the library package is
sufficient — and in both cases an oracle asserts the choice so it cannot rot.

**Actual.** Neither. The gap is invisible to every check in the repo.

## Fix

<unfixed — raised only>

**This needs a human decision first, not a patch.** Whether MIT/CC-BY attribution must
travel inside the CLI *package* — as opposed to being satisfied at build time, when cargo
has already fetched `ferrosintesis` and all 24 asset crates with their notices — is a
licensing judgement, and the obligation genuinely attaches to whoever redistributes the
compiled `ferrosintesis` binary rather than to `cargo install`. Do not let an autonomous fix
pass invent an answer.

Once decided, the mechanical parts are small:

- If a `NOTICE` is wanted: add `crates/ferrosintesis-cli/NOTICE` (the parent's content, or a
  pointer plus the copyright lines), and add `"NOTICE"` to the `include` list at
  `Cargo.toml:14` — omitting the include is the silent half, since the file would exist in
  git and still not ship.
- Either way, widen the oracle so the question is asked. The cheapest honest form: assert
  that **every workspace crate with `publish` enabled and a `[[bin]]`, or that depends on an
  attribution-bearing crate, packages a `NOTICE`** — derived from the manifests, not from a
  list. A second hand-written list here would inherit the exact defect being fixed.
- Adversarial acceptance check, per CLAUDE.md: delete the new `NOTICE`, or drop it from
  `include`, and confirm the oracle goes red. A packaging oracle that only reads the
  filesystem will pass on a file git has but cargo does not ship — check the `include` list
  too, or check `cargo package --list`.

## Notes

- Raised by an autonomous read-only code-review pass over `crates/ferrosintesis-cli/`,
  surfaced by a devil's-advocate lens briefed to attack the enumeration predicates. Verified
  independently: the directory listing shows no `NOTICE`; `Cargo.toml:14` omits one;
  `crates/ferrosintesis/Cargo.toml:13` includes one; `licensing.rs:55-86` shows the
  predicate.
- Related history: MM-BUG-KILN-00060 (the licensing guide named 5 of 10 attribution-bearing
  banks) and MM-BUG-KILN-00071 (the oracle passed on a gutted NOTICE). Same family, new
  member.
- Severity Medium rather than High because the material *is* present in every install tree
  and the license texts themselves ship; the exposure is redistribution of the built binary
  and a compliance check nothing performs.
