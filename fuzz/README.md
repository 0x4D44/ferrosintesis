# fuzz/ — libFuzzer target for `offline::parse`

`ferrosintesis::offline::parse(&[u8])` is the crate's **only untrusted-input surface**:
every other entry point takes a `Song` that `parse` produced. Its contract is total —
for any byte string it returns `Ok` or a `MidiError`, never a panic, never a hang, never
an unbounded allocation. This target tries to break that.

The hand-written oracles live in `crates/ferrosintesis/src/parse_robustness.rs` and cover
the inputs we thought of; this covers the ones we did not.

## Not part of the gate

This directory is **not** a workspace member — `fuzz/Cargo.toml` carries its own empty
`[workspace]` table, so `cargo build` / `cargo test` / `cargo clippy` at the repository
root never reach it. That is deliberate: cargo-fuzz needs a nightly toolchain and a
sanitizer runtime, while the repo gates locally on stable. Nothing in CI or in
`deltic integrate` runs a fuzzer.

It also builds `ferrosintesis` with `default-features = false`, dropping the 25 embedded
sample crates (~111 MiB of PCM). `parse` never touches a sample, so they would be pure
link-time cost, and a fuzzer's value is iterations per second.

## Running it

```
cargo install cargo-fuzz          # once
cd fuzz
cargo +nightly fuzz build parse   # build only
cargo +nightly fuzz run parse -- -max_total_time=600
```

Seed the corpus first — a fuzzer starting from random bytes spends its whole budget
rediscovering the `MThd` magic:

```
mkdir -p fuzz/corpus/parse
find albums -name '*.mid' -size -40k | head -12 | while read f; do
  cp "$f" "fuzz/corpus/parse/$(echo "$f" | tr '/ ' '__')"
done
```

`test-corpus/reference-midi/` (gitignored third-party files, if the machine has them) is
the better seed set: real sequencer output exercises running status, SysEx and controller
paths our own generative albums never emit.

### Windows

Two gotchas, both hit on the first attempt here:

- **`cargo fuzz build -s none` fails to link** with `unresolved external symbol
  __start___sancov_cntrs`. On MSVC the sancov section-boundary symbols come from the
  sanitizer runtime, so disabling the sanitizer removes the very symbols the coverage
  instrumentation still references. Use the **default** `-s address` instead — it links.
- **The built binary then exits `0xC0000135` (STATUS_DLL_NOT_FOUND)** because
  `clang_rt.asan_dynamic-x86_64.dll` is not on `PATH`. Add the MSVC toolchain's compiler
  directory, e.g.:

  ```
  export PATH="/c/Program Files/Microsoft Visual Studio/18/Enterprise/VC/Tools/MSVC/14.50.35717/bin/Hostx64/x64:$PATH"
  ```

  (Adjust the version. `ls .../bin/Hostx64/x64 | grep clang_rt` finds it.)

## What it asserts

Beyond "did not crash", the target restates the invariant `MidiError::TooLong` exists to
uphold: a song that parsed must report a length that is finite, non-negative and within
`MAX_SONG_SECONDS`. `render` allocates `(seconds + tail) * rate * 8` bytes up front, and
the tempo map is entirely attacker-controlled — a NaN or an inf slipping past the guard
becomes an allocator abort downstream, which no caller can `catch_unwind`.

It deliberately does **not** render. Rendering is orders of magnitude slower than parsing
and would starve the fuzzer of iterations, and the hazard it would probe is answered at
parse time by the assertion above.

It also deliberately does **not** assert `Song::initial_bpm()` is finite. A Set-Tempo of
zero microseconds per quarter (`00 FF 51 03 00 00 00`) parses cleanly — every tick maps
to 0 s, so the length guard is satisfied — and `60_000_000 / 0` gives `+inf`. That is a
wart in a reporting accessor, not a crash, and asserting it would fail the run on
iteration one for a non-defect.

## What it has found

**Nothing yet.** First run, 2026-07-25, on `ferrosintesis` 0.21.56:

```
cargo +nightly fuzz run parse -- -max_total_time=120 -print_final_stats=1
Done 174309 runs in 121 second(s)
stat::number_of_executed_units: 174309
stat::average_exec_per_sec:     1440
stat::new_units_added:          1504
stat::peak_rss_mb:              468
```

No crashes, no timeouts, no OOMs, `fuzz/artifacts/parse/` empty. Seeded from twelve album
MIDIs. This was a **smoke run**, not a campaign: two minutes is enough to prove the
harness works and to catch a shallow panic, and nothing more. A real campaign is hours,
and has not been run.

When a run does find something, drop the reproducer under `fuzz/artifacts/parse/` (they
land there automatically), turn it into a fixture in
`crates/ferrosintesis/src/parse_robustness.rs`, and record it here.
