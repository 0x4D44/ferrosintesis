# MM-BUG-KILN-00099 — measure_wav meters every WAV as 44.1 kHz signed 16-bit stereo

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/ferrosintesis-cli/examples/measure_wav
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
- **State history:** Open (2026-07-25, raised by Codex GPT-5.6-Sol during the `crates/ferrosintesis-cli/` coverage review) → Fixed (2026-07-25, Codex GPT-5.6-Sol; strict shared WAV parsing and sample-rate propagation landed with regression coverage; awaiting independent two-eyes verification) → Closed (2026-07-25, Claude Opus 5, independent two-eyes — did not author the fix; the pre-fix example mis-meters the same 48 kHz render by 0.25 dB; the fixed one does not)

## Observation

Source-level reproduction at `2d90376` (not executed because the review pass is
read-only): render a valid 48 kHz, 16-bit stereo WAV with the shipping CLI, then
pass it to the `measure_wav` example.

`crates/ferrosintesis-cli/examples/measure_wav.rs:14-33` finds only the `data`
chunk. It never reads or validates the `fmt ` chunk, channel count, bit depth,
or declared sample rate. Lines 35–38 decode every pair of bytes as signed
16-bit PCM, and lines 39–40 always pass 44,100 Hz to the loudness and true-peak
meters.

Expected: a valid 48 kHz WAV is decoded as 48 kHz stereo PCM, and unsupported
layouts are rejected.

Actual: 48 kHz audio is evaluated with 44.1 kHz K-weighting coefficients and
400/100 ms block geometry. Mono, float, 24-bit, or other layouts are silently
reinterpreted as interleaved 16-bit stereo. The tool prints plausible numeric
results even when its interpretation is wrong.

## Fix

`measure_wav` and `calmeter` now use one bounded RIFF/WAVE reader. It validates
the container and declared RIFF extent, chunk sizes and padding, `fmt ` metadata,
supported sample rate, byte rate, block alignment, complete frames, and required
`data`. The meter selects strict 16-bit stereo PCM mode; calmeter retains its
existing mono/stereo PCM and float support.

`measure_wav` passes the parsed sample rate to both loudness and true-peak
meters. Regression fixtures prove 44.1 and 48 kHz propagation, strict mono and
float rejection, non-PCM and unsupported-rate rejection, and malformed or
missing `fmt ` and `data` handling. The focused tests and clippy pass on the
native toolchain and the declared Rust 1.87 floor.

### Verification summary (2026-07-25, Claude Opus 5, independent — did not author the fix)

Re-ran the **original observation end-to-end**: rendered a 48 kHz, 16-bit stereo WAV with
the shipping CLI (`--rate 48000`), then metered it with the `measure_wav` example.

- Pre-fix example (restored verbatim from `583d8d3^`): **−18.02** LUFS.
- Fixed example on trunk, same file: **−17.77** LUFS.

A 0.25 dB error purely from applying 44.1 kHz K-weighting coefficients and 400/100 ms block
geometry to 48 kHz audio — the recorded "prints plausible numeric results even when its
interpretation is wrong". The 44.1 kHz render meters at −17.83 on the fixed build, so the
propagation is real rather than a constant offset.

Green after: `wav_reader.rs` passes 7/7, including `pcm_stereo_preserves_44k1_and_48k_rates`
and the strict mono / float / non-PCM / unsupported-rate rejections.
Repo gates on the verification worktree: `cargo fmt --all --check` clean;
`cargo clippy --workspace --exclude amp-lab --all-targets --locked -- -D warnings` clean;
`cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings`
clean; `cargo test -p ferrosintesis --no-default-features --locked` 614 passed / 0 failed;
`cargo test --workspace --exclude amp-lab --locked` all suites ok, 714 passed / 0 failed /
27 ignored in the ferrosintesis lib suite and no failures anywhere; `cargo test -p amp-lab` 26/26;
`python tools/ferrosintesis-samples/test_prepare.py` 32/32.

## Notes

`raw_dump` currently produces only 44.1 kHz float WAVs, but the shipping CLI
supports `--rate 48000` and the example describes itself as a WAV meter rather
than a raw-dump-only meter. Its purpose is to distinguish limiter defects from
meter defects, so authoritative-looking wrong measurements are a real
calibration risk.
