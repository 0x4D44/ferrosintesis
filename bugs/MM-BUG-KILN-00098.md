# MM-BUG-KILN-00098 — A 1–4 Hz WAV makes calmeter loop forever while growing memory

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/ferrosintesis-cli/examples/calmeter
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
- **State history:** Open (2026-07-25, raised by Codex GPT-5.6-Sol during the `crates/ferrosintesis-cli/` coverage review) → Fixed (2026-07-25, Codex GPT-5.6-Sol; calmeter rate validation and zero-hop loudness hardening landed with regression coverage; awaiting independent two-eyes verification) → Closed (2026-07-25, Claude Opus 5, independent two-eyes — did not author the fix; calmeter now rejects 1 Hz promptly and accepts 8 kHz; the zero-hop root cause confirmed by arithmetic — the unbounded loop itself was deliberately NOT executed)

## Observation

Source-level reproduction at `2d90376` (not executed because the review pass is
read-only): give `calmeter` a small RIFF/WAVE containing at least one stereo
frame, a format chunk declaring a sample rate from 1 through 4 Hz, and a plan
row whose onset is frame 0.

`crates/ferrosintesis-cli/examples/calmeter.rs:102-145` validates the container,
channel count, and bit depth, but accepts the declared sample rate without a
lower bound. The one-frame note window reaches `momentary_lufs` at
`crates/ferrosintesis-cli/examples/calmeter.rs:203`.

In `crates/ferrosintesis/src/loudness.rs:124-140`, the 100 ms hop rounds to zero
at 1–4 Hz. The loop condition remains true, `start += hop` never advances, and
the function keeps appending blocks until the process is stopped or exhausts
memory.

Expected: reject an unsupported sample rate promptly.

Actual: a tiny input can make the development calibration tool nonterminating
and memory-growing.

## Fix

`calmeter::read_wav` now documents and enforces an 8 kHz minimum input rate,
which is the lowest conventional PCM rate with enough bandwidth for its
BS.1770 K-weighting filter. A one-frame 1 Hz RIFF is rejected immediately, and
an 8 kHz boundary fixture is accepted.

The shared loudness block builder now computes and validates its rounded 400 ms
block and 100 ms hop before allocating or filtering. A zero block or hop returns
an empty momentary series; integrated loudness consequently returns negative
infinity. Coverage exercises every rate from 0 through 4 Hz, while the existing
44.1/48 kHz EBU calibration and all other loudness tests remain green.

The 1 Hz calmeter regression failed before the fix because `read_wav` accepted
the file. The complete calmeter example suite, all loudness tests, and focused
clippy pass after the fix.

### Verification summary (2026-07-25, Claude Opus 5, independent — did not author the fix)

The recorded observation was never executed (it came from a read-only review), so there
is no runtime transcript to reproduce. Verified in two halves.

**Executable half — green.** A 1 Hz, one-frame stereo RIFF with a frame-0 plan row now returns
immediately:

```
Error: "…/hz1.wav: unsupported sample rate 1 Hz; need at least 8000 Hz"
```

No hang, no memory growth. The 8 kHz boundary fixture is **accepted** and meters normally, so
the new floor does not over-reject. `sub_five_hz_rates_return_without_looping` and the rest of
the loudness suite pass.

**Root cause — confirmed by evaluating the pre-fix expressions.** With
`hop = (0.100 * fs).round() as usize` and `block = (0.400 * fs).round() as usize`:

| fs (Hz) | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| block | 0 | 0 | 1 | 1 | 2 | 2 |
| hop | 0 | 0 | 0 | 0 | 0 | 1 |

`hop` is zero for fs 0–4 and one from fs 5 — matching the recorded "1 through 4 Hz" range
exactly, and `block` is 0/1/1 at fs 1/2/3 so the old `n_frames < block` guard does not shield a
one-frame buffer there. `start += hop` therefore cannot advance. The diagnosis holds.

**Deliberately NOT executed: the unbounded-allocation hang itself.** `deltic health` reported
commit charge at 79% on a box shared with other agents, and the pre-fix loop pushes into a
`Vec` at multiple GB/s with no bound. Running it risked exhausting the machine for everyone.
This is a stated omission, not a passed check — a future verifier with an isolated box and a
memory-capped job object could close that last gap.
Repo gates on the verification worktree: `cargo fmt --all --check` clean;
`cargo clippy --workspace --exclude amp-lab --all-targets --locked -- -D warnings` clean;
`cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings`
clean; `cargo test -p ferrosintesis --no-default-features --locked` 614 passed / 0 failed;
`cargo test --workspace --exclude amp-lab --locked` all suites ok, 714 passed / 0 failed /
27 ignored in the ferrosintesis lib suite and no failures anywhere; `cargo test -p amp-lab` 26/26;
`python tools/ferrosintesis-samples/test_prepare.py` 32/32.

## Notes

The tool is dev-only and normal calibration files are 44.1 kHz, which limits
exposure but does not change the deterministic nontermination.
