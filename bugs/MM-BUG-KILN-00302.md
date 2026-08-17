# MM-BUG-KILN-00302 — WAV decoder tests: byte-rate check unreachable by construction, a mis-named truncation test, uncovered error arms, and a temp-path race

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** crates/ferrosintesis-cli
- **Raised:** 2026-08-17T22:56:53Z
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
- **State history:** Open (2026-08-17T22:56:53Z, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

Test debt around `crates/ferrosintesis-cli/examples/support/wav.rs`, the WAV decoder shared
by `calmeter`, `measure_wav` and `tests/wav_reader.rs`. Four items, grouped because they are
one afternoon's work in two files.

**1 — the byte-rate check cannot fail, by construction.** `tests/wav_reader.rs:7-9` builds
every fixture's `byte_rate` as `sample_rate * (channels * (bits / 8))`. `decode_wav`
validates with the identical formula: `expected_byte_rate = format.sample_rate as u64 *
expected_align as u64` (`examples/support/wav.rs:132-133`, with `expected_align` from
`:124-125`). The fixture and the code under test derive the same number, so the assertion can
only agree with itself — CLAUDE.md names this shape verbatim ("an assertion checked against a
constant the code under test also derives"). The one test that corrupts a header field,
`rejects_inconsistent_alignment_and_incomplete_data` (`tests/wav_reader.rs:104-108`),
overwrites bytes `32..34` — that is `block_align`, so the alignment check at
`support/wav.rs:126` returns first and the byte-rate branch at `:132-138` is never reached.

**2 — a test passes on a different error than its name claims.**
`rejects_missing_or_truncated_format_and_missing_data` (`tests/wav_reader.rs:88-92`) builds
`truncated_format` as `RIFF\x18\0\0\0WAVEfmt \x10\0\0\0` plus four bytes — 24 bytes total,
declaring a RIFF size of 0x18 = 24, so `riff_end = 32 > 24`. It therefore trips **"truncated
RIFF body"** at `support/wav.rs:35-39`, not the truncated-`fmt`-chunk branch at `:66-71`,
which stays uncovered. The assertion is only `.contains("truncated")`, which matches five
different messages in that file, so the mismatch is invisible.

**3 — uncovered error arms.** Beyond the `fmt`-body branch above, nothing exercises: "not a
RIFF/WAVE file" (`support/wav.rs:27`), "RIFF size overflows this platform" (`:33`),
"truncated WAV chunk header" (`:49`), "truncated {} chunk" (`:58`, and with it `chunk_name`
entirely), "need mono or stereo" for 0 or 3+ channels (`:104`), and both padding-overflow
arms (`:86`, `:88`).

**4 — two tests race for one temp filename.** `calmeter.rs:181-183` builds its path as
`format!("calmeter-rate-{}-{nonce}.wav", std::process::id())` — no discriminating label,
unlike every sibling helper in the crate (`src/output.rs:88`, `tests/output_safety.rs:15`,
`tests/wav_reader.rs:33-36`, which all take one). `read_wav_rejects_a_one_hz_meter_input` and
`read_wav_accepts_the_lowest_supported_rate` both call `TestWav::at_rate` from the same
process in parallel, separated only by a `SystemTime` nanosecond nonce. On a collision one
test reads the other's sample rate, or one `Drop` deletes the other's file mid-read. Latent
today only because those tests never run in the gate (tracked as MM-BUG-KILN-00301) — which
means fixing that bug is what makes this one bite.

Minor, same neighbourhood: `tests/wav_reader.rs:33-39` has no RAII guard, unlike every other
temp helper here — `remove_file` sits between the write and the assertion, so a panic at
`:38` leaks the fixture into `%TEMP%` permanently.

## Fix

<unfixed — raised only>

1. Give `wav_bytes` an explicit `byte_rate` parameter (or a `wav_bytes_with_byte_rate`
   variant) so a fixture can state a *wrong* value, and add a test that asserts the
   "inconsistent byte rate" message. Confirm it fails against the current decoder with the
   check commented out.
2. Fix fixture 2 to actually truncate the `fmt` body with a correct RIFF size, and tighten
   every assertion in that test from `contains("truncated")` to the specific message. The
   generic substring is what let the mis-aim hide.
3. Add cases for the arms in item 3. They are one `wav_bytes` call each.
4. Add a `label: &str` to `TestWav::at_rate` and thread it through both call sites, matching
   the sibling helpers. Wrap `tests/wav_reader.rs:33-39` in the same `TestDir`/`Drop` shape
   the rest of the crate uses.

## Notes

- Raised by an autonomous read-only code-review pass; surfaced by a devil's-advocate lens
  briefed to find tests that cannot fail. Items 1, 2 and 4 were re-derived independently
  from the source by the reviewer (header offsets counted by hand for item 1; byte counts
  for item 2).
- Ordering: land MM-BUG-KILN-00301 (which starts running these tests) and item 4 together,
  or the first green run may flake.
- Low severity: this is a dev-only calibration reader, not shipped synthesis. Filed because
  CLAUDE.md asks for test-infrastructure defects to be ticketed rather than worked around —
  the whole fleet depends on the suite meaning what it says.
