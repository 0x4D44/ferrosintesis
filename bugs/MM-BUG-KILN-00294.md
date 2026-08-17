# MM-BUG-KILN-00294 — Windows identity probe's exclusive input open aborts the render when any process is reading the MIDI

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/ferrosintesis-cli
- **Raised:** 2026-08-17T22:47:52Z
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
- **State history:** Open (2026-08-17T22:47:52Z, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

**Symptom (Windows only).** `ferrosintesis in.mid -o out.wav` refuses to render, exiting 1
with a bare `error: The process cannot access the file because it is being used by another
process. (os error 32)` — naming neither file — whenever **any** other process holds
`in.mid` open for reading and `out.wav` already exists. The two files are entirely
different. Without the alias check the same render succeeds.

**Root cause.** `crates/ferrosintesis-cli/src/output.rs:60` establishes file identity by
holding the *input* with no sharing at all:

```rust
let input_guard = OpenOptions::new().read(true).share_mode(0).open(input)?;
```

Windows sharing is bidirectional. `dwShareMode = 0` denies every access mode, so
`CreateFile` fails with `ERROR_SHARING_VIOLATION` if **any** existing handle holds access
this share mode denies — an ordinary `FILE_SHARE_READ` holder is enough. The `?` propagates
that error out of `paths_refer_to_same_file`, `reject_input_alias` returns `Err`, and
`crates/ferrosintesis-cli/src/main.rs:112-115` prints it and exits 1 **before**
`offline::load` at `main.rs:117` is ever reached.

**Why the render would otherwise have succeeded.** The library reads the MIDI with a plain
`std::fs::File::open` (`crates/ferrosintesis/src/midi.rs:251`), whose default share mode
(`READ | WRITE | DELETE`) tolerates a read-sharing third party. So the check aborts renders
that the renderer itself has no problem performing.

**Reachability is the common case, not an edge case.** `output.rs:28-32` returns early only
when the output is `NotFound`. Once the WAV exists — i.e. every re-render — and the
canonical paths differ, `output.rs:38` always calls `platform_same_file`, so the exclusive
open runs on every ordinary Windows re-render.

**This is the residual of MM-BUG-KILN-00120, not a duplicate of it.** That bug fixed the
*output* probe (`File::open(output)`, `output.rs:61-69`) and closed on the reasoning that
the blast radius was narrow because "ordinary players and editors share read"
(`bugs/MM-BUG-KILN-00120.md:102-106`). That reasoning **inverts** on the input side: read
sharing is precisely what collides with `share_mode(0)`. The author reasoned about
third-party interference for the output (`output.rs:56-59`) and guarded it with the
drop-and-retry; the symmetric input case is unguarded.

**Expected.** A third-party sharing condition on the *input* leaves the render unaffected,
or at worst produces an accurate, path-naming diagnostic. It must not abort a render the
synthesizer can perform.

**Actual.** Render aborted, exit 1, message names no file.

**Triggers in practice.** A sequencer or editor with the `.mid` open; a second
`ferrosintesis --solo <ch>` stem render of the same MIDI (the workflow the CLI's own
doc-comment advertises, `main.rs:9-10`) whose probes overlap; an indexer or backup agent
mid-scan.

**Test gap.** `share_mode` appears exactly once in the crate's tests —
`crates/ferrosintesis-cli/tests/output_safety.rs:130`, holding the **output**
(`exclusively_held_distinct_output_is_not_reported_as_an_input_alias`, lines 116-163).
Neither that file nor the four unit tests in `output.rs:112-170` ever holds the input.

## Fix

<unfixed — raised only>

Suggested shape (cheap, no new dependency, keeps `#![forbid(unsafe_code)]`): make the
exclusive open **conditional and non-fatal**.

1. Pre-filter on metadata before locking anything. Hard links share one inode, so
   `std::os::windows::fs::MetadataExt` (`file_size()`, `creation_time()`,
   `last_write_time()`, `file_attributes()` — all stable) must agree on every field for the
   two paths to be the same file. A `.mid` input and an existing `.wav` output essentially
   never agree, so the probe stops running on the common path entirely.
2. If the guard open still fails with `ERROR_SHARING_VIOLATION`, the probe has proved
   nothing about identity — treat it as "not aliased" (the metadata pre-filter already
   said the files differ) rather than propagating. Any *other* error may still propagate.
3. Add a regression that holds the **input** from a second handle with ordinary read
   sharing and asserts the render completes and the input is byte-identical afterwards —
   the mirror of `output_safety.rs:116-163`. Confirm it fails before the fix.

Note stable Rust does not expose `volume_serial_number`/`file_index` (the `windows_by_handle`
feature is unstable), so the probe cannot simply be replaced with real identity —
`MM-BUG-KILN-00120.md:107-109` records that constraint and it still holds.

## Notes

- Unix is unaffected: `output.rs:41-48` compares `dev`/`ino`, which is real identity and
  takes no lock.
- Raised by an autonomous code-review pass over `crates/ferrosintesis-cli/`; the code path
  and the Windows `CreateFile` sharing rule were established by reading
  `output.rs`, `main.rs`, `midi.rs` and `bugs/MM-BUG-KILN-00120.md`. The runtime failure
  has **not** been reproduced by executing the binary — this pass is read-only and does not
  run the app. Reproduce before fixing.
