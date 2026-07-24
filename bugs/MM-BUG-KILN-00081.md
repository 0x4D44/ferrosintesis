# MM-BUG-KILN-00081 — valid default audio configurations can fail or stay silent in amp-lab

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** amp-lab / audio device
- **Raised:** 2026-07-24
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/amp-lab/`)
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). `fill_device` now renders any callback size
  in bounded chunks instead of bailing to silence; `start` selects a supported f32 config
  or fails with the exact reason. Callback-size + channel-mapping tests added. Evidence
  under "Fix landed" below. Awaits independent two-eyes closure.)

## Observation

Two independent assumptions reject valid CPAL defaults:

1. `default_output_config()` reports a sample format, but amp-lab discards it
   when converting to `StreamConfig`; the callback's `&mut [f32]` forces an
   `f32` stream (`crates/amp-lab/src/audio.rs:43-47` and `:68-71`). A default
   device/config that supports only an integer format fails to open even though
   the output device is usable.
2. Scratch storage is fixed at 4,096 stereo frames (`audio.rs:65`). If a valid
   default callback contains more than 4,096 frames, the callback first zeros
   output, increments `xruns`, and returns without rendering (`:117-127`).
   Stable large callbacks therefore produce permanent silence rather than a
   one-off underrun.

Expected: amp-lab either adapts to a valid default configuration or rejects it
clearly during setup. Actual: integer defaults may fail stream construction,
while large-buffer defaults can start successfully but remain silent.

The smoke-tested device used by the original implementation worked. Arthur's
current device format and callback size were not queried in this read-only pass.

## Fix

Retain and dispatch on the reported sample format, converting the internal
`f32` stereo render to `f32`, `i16`, or `u16` output as appropriate, or
explicitly select a supported `f32` configuration. Handle arbitrary callback
lengths by rendering/fanning out in bounded chunks, or negotiate and validate a
maximum buffer before `stream.play()`. Fail startup with the exact unsupported
constraint rather than entering a silent stream.

Factor the device-independent callback core and test integer conversion,
mono/stereo/multichannel mapping, and callback sizes immediately below, at, and
above 4,096 frames.

## Fix landed (2026-07-24)

Two independent defects, two fixes (`crates/amp-lab/src/audio.rs`).

**1. Large callbacks (the worse one — permanent silence).** `fill_device` required the
whole callback to fit in its 4096-frame scratch and returned `Err` otherwise. A host that
picks a bigger buffer does so on EVERY callback, so this was not a one-off underrun: it was
continuous silence with a climbing xrun count, on a config cpal considers valid. It now
renders in chunks of the scratch size, mapping each chunk to the device channels as it
goes. No allocation, and the sequencer stays sample-accurate because `process` advances the
player by exactly the frames it renders — proven by a test that renders the same span as
one 8192-frame call and as eight 1024-frame calls and asserts the samples are bit-identical.

**2. Non-f32 default format.** `start` discarded the reported sample format and forced an
f32 stream, so a device whose default is i16/u16 failed to open with cpal's own opaque
error. It now takes the default when it is f32, else searches `supported_output_configs()`
for an f32 one, else fails with the exact message — which format the device offered and
that amp-lab does not convert — rather than a silent or cryptic failure.

**Regression** — three tests:

- `any_callback_size_produces_audio`: 1024 / 4096 / 4097 / 8192 frames all render non-silent
  with zero xruns. The sizes straddle the scratch boundary, which is exactly where the old
  code flipped to failing.
- `chunking_does_not_change_the_audio`: one big callback == eight small ones, bit-for-bit.
- `device_channel_counts_are_mapped`: mono downmixes, stereo passes, and a 4-channel device
  gets the pair with the extra channels left silent (not fed garbage).

**Fails before / passes after.** Restoring the "whole callback must fit" bail-out fails all
three, with "4097-frame callback failed to render". Passing needs the chunked path.

**Honest scope limit.** The f32-format selection is **not** unit-tested: it needs a real
`cpal::Device`, which by this crate's own design (the `Core` split exists precisely because
a device-bound closure is untestable) cannot be constructed in a test. It is
source-verified and its failure branch now carries a precise diagnostic, but a device with
an integer-only default has to be verified on hardware. The silent-large-callback half —
the one that produced no error at all — is the half now covered by tests, which is the
right priority: a loud failure is far less dangerous than a silent one.

**Gates.** `cargo test -p amp-lab` 21 passed / 0 failed; clippy `-D warnings` clean; `cargo
fmt --check` clean. amp-lab is outside the workspace gate, so these were run explicitly.

## Notes

Exact affected hardware on KILN remains unverified. The unsupported assumptions
and their deterministic failure branches are source-confirmed.
