# MM-BUG-KILN-00147 — GM44 tremolo strings is the last bowed program on the saw voice, and has no sampled onset

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** voices / bowed strings
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
- **Held branch:** host-local:KILN:task/bug-MM-BUG-KILN-00147-run-fix-20260727T034803Z-p9812-n357621900-c48-code-1785124935354
- **Legacy fixed run:** -
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=claude-opus-4.6@high) → Fixed (2026-07-27, GPT-5.6 Codex on KILN-Windows — source `12df88f0a96bc7ea661055ab184f18c7383799bc`; GM44 now uses a direction-reversing bowed-string waveguide plus the string-section LA onset)

## Observation

GM 40/41/110 moved to the `BowedString` waveguide on 2026-07-26, joining 42/43. GM 44 (tremolo strings) is now the ONLY bowed program still rendering as the saw-based `Bowed` voice, and the only bowed program with no LA sampled onset at all — see the bare `44 => Box::new(Bowed::new(44, ...))` arm in crates/ferrosintesis/src/voices.rs.

It was left behind deliberately, not overlooked. Migrating it is NOT a voicing-table entry like the other three were:

- Tremolo is rapid bow-DIRECTION change, so each stroke needs its own re-articulation in the waveguide — the stick-slip interaction re-established per stroke, not a gain LFO over a sustained tone. `Bowed` fakes it with amplitude modulation plus per-stroke jitter (the BOW_TREM_* constants).
- There is a design question to settle first: GM 44 is a SECTION sound ('Tremolo Strings'), so the solo-string waveguide may be the wrong target and an ensemble treatment may fit better. Decide that before implementing.

Impact is low. A census of every committed .mid on 2026-07-26 found no album or demo in the repo authoring GM 44, so nothing currently renders differently — this is about ferrosintesis being a faithful general GM player, which CLAUDE.md is explicit is the standard to judge it by ('never cull a feature just because no in-repo album uses it').

## Fix

### Fix summary (2026-07-27, GPT-5.6 Codex on KILN-Windows)

Source: `12df88f0a96bc7ea661055ab184f18c7383799bc`.

GM44 was the last default bowed program still routed to the retired saw-based
`Bowed` voice. The earlier bowed-string migration had no physical tremolo
treatment and had not settled whether this GM section patch should use a solo or
section onset.

The fix routes GM44 through the violin-family `BowedString` waveguide, with a
GM44-only tremolo treatment that:

- reverses bow direction at 6–9 Hz, accelerated by velocity;
- jitters each stroke's timing and force;
- re-establishes the stick-slip scratch catch at every reversal;
- keeps reversal discontinuities bounded so the re-bite does not become a click.

The default samples-on path uses the existing LA string-section bank rather than
a solo-violin onset. The sample changes the attack, then hands over to the
waveguide. The per-program velocity compensation table includes GM44 because the
waveguide adds a monotonic excitation slope beyond the shared square law.

Review also found controller tests still measuring GM44 with the old saw voice's
zero-crossing oracle. They now use the bowed-family autocorrelation oracle, and
GM44 is included in the all-`BowedString` controller matrix. The retired saw
implementation remains only as an explicitly named test migration reference; it
can no longer be mistaken for the shipping default.

Evidence:

- `cargo test -p ferrosintesis --lib`: 807 passed, 41 diagnostics ignored.
- `cargo test -p ferrosintesis --lib --no-default-features`: 686 passed,
  36 diagnostics ignored.
- `cargo clippy -p ferrosintesis --all-targets -- -D warnings`: green.
- `cargo clippy -p ferrosintesis --all-targets --no-default-features -- -D warnings`:
  green.
- `cargo fmt --check` and `git diff --check`: green.
- The reversal oracle measured the largest reversal step at 1.29× ordinary
  sample-step RMS, below its 8× click guard.
- Raw low/mid/high A/B pack:
  `C:\Users\marti\AppData\Local\Temp\MM-BUG-KILN-00147-candidate`.
  Candidate layered/model sustain correlation is 0.999985–0.999995, confirming
  the section sample changes the onset and hands over to the model. Candidate
  model versus baseline sustain correlation is −0.147 to +0.133, confirming the
  physical model genuinely replaces the saw voice. Raw candidate peak stays
  below 0.206.
- Full 124-MIDI render-diff against exact base
  `22c7e0c200603f929d55cf2e88f9fc3bc6e9660c`, classified as GM44 at the
  tool-supported 11.025 kHz rate: 1 expected change, 123 expected identical,
  0 contamination, and 0 not reached.

## Notes
