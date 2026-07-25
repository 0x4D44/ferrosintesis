# MM-BUG-KILN-00101 — MIDI parser overflows on 32-bit targets; a truncated track silently parses as an empty song

- **State:** Fixed
- **Priority:** Must
- **Severity:** High
- **Area:** midi / parser
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, found while building the parser-robustness test suite
  that the ferrosintesis review flagged as the crate's largest coverage gap; found by reading
  the arithmetic, not by the fuzzer, which builds 64-bit and cannot reach it)
  → Fixed (2026-07-25, Claude Opus 4.5; all three sites saturated. The crafted fixtures now
  pass under `--target i686-pc-windows-msvc`, where they previously panicked. Awaits
  independent two-eyes closure.)

## Observation

`offline::parse` breaks its `Result` contract on any target with a 32-bit `usize`.
Three additions take an **attacker-controlled `u32` length** and add it to a `usize`
position with no overflow guard:

| Site | Code | Attacker-controlled field |
|---|---|---|
| `crates/ferrosintesis/src/midi.rs:166` | `self.data.get(self.pos..self.pos + n)` | meta / SysEx VLQ payload length |
| `crates/ferrosintesis/src/midi.rs:217` | `c.pos = 8 + hlen;` | header-chunk length field |
| `crates/ferrosintesis/src/midi.rs:231` | `let end = c.pos + len;` | track-chunk length field |

On a 64-bit `usize` these are unreachable — `u32::MAX` cannot overflow a 64-bit add, and
every fixture correctly returns `UnexpectedEof`. On a **32-bit `usize`** — i686, armv7,
and **wasm32**, a wholly plausible target for a synthesizer — `usize::MAX == u32::MAX`,
so a declared length near `u32::MAX` overflows by construction.

Observed on `--target i686-pc-windows-msvc`:

```
debug (overflow checks ON)
  header-len fixture -> panicked at midi.rs:217: attempt to add with overflow
  track-len  fixture -> panicked at midi.rs:231: attempt to add with overflow
  meta-len   fixture -> panicked at midi.rs:166: attempt to add with overflow
  sysex-len  fixture -> panicked at midi.rs:166: attempt to add with overflow

release (checks OFF, values wrap)
  header-len fixture -> MissingTrack { index: 0 }  (misdiagnosed; 64-bit says UnexpectedEof)
  track-len  fixture -> Ok, 0 events, 0.00 s       (SILENT)
```

**The release track-length case is the serious one.** No panic, no error, no diagnostic —
a truncated file parses as a valid, empty song. A caller doing the documented thing
(`match parse(bytes) { Ok(song) => …, Err(e) => … }`) is handed an `Ok` and renders
silence. Debug at least fails loudly; release fails quietly, which is worse.

Reproducing bytes (35 B) — a valid SMF whose track length is `FF FF FF FF`:

```
4D 54 68 64 00 00 00 06 00 00 00 01 01 E0 4D 54 72 6B FF FF FF FF
00 90 3C 64 83 60 80 3C 00 00 FF 2F 00
```

## Why it matters

`parse` is the crate's **only untrusted-input surface**, and its whole contract is that
malformed input yields a typed `MidiError` rather than a panic or a wrong answer. That
contract holds on 64-bit and silently does not hold on 32-bit.

Note the ledger's own framing was wrong when this was raised: a note claimed the crate is
already published to crates.io. It is not — only a `0.0.0` name-reservation stub exists.
That lowers the urgency (no downstream user is exposed today) but not the priority: this
should not be in the first real release, and wasm32 is exactly the kind of target someone
adds later without re-auditing the parser's arithmetic.

## Fix

All three sites now use `saturating_add`. Saturation is the right operator rather than
`checked_add` + explicit error: a saturated end is by definition past `data.len()`, so the
existing `.get(..).ok_or(MidiError::UnexpectedEof)?` already produces exactly the right
error, and the guard adds no new branch or error path.

`Cursor::bytes` additionally assigns `self.pos = end` (the saturated value) rather than
recomputing `self.pos += n`, so the cursor cannot be advanced past the saturation point by
a second unguarded add.

## Regression

`crates/ferrosintesis/src/parse_robustness.rs` carries all four reproducing inputs as
fixtures in its variant-reachability table, each asserting `UnexpectedEof`. They pass on
64-bit trivially; the meaningful run is:

```
cargo test -p ferrosintesis --lib --target i686-pc-windows-msvc --no-default-features parse_robustness
  4 passed; 0 failed
```

**That command is the regression test and it is not in the gate.** The integration gate is
64-bit only, where these fixtures cannot fail. Adding a 32-bit target to the gate is a
separate decision (it needs the target installed on every runner); until then, this bug is
the record of why the fixtures exist and how to exercise them meaningfully.
