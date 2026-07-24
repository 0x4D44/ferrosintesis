# MM-BUG-KILN-00081 — valid default audio configurations can fail or stay silent in amp-lab

- **State:** Open
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

## Notes

Exact affected hardware on KILN remains unverified. The unsupported assumptions
and their deterministic failure branches are source-confirmed.
