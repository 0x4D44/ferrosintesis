# ferrosintesis-flac

A deliberately minimal, dependency-free FLAC decoder for the
[`ferrosintesis`](https://crates.io/crates/ferrosintesis) embedded sample banks.

## This is not a general-purpose FLAC decoder

It accepts **16-bit mono 44.1 kHz** streams and rejects everything else by name.
No multi-channel decorrelation, no other bit depths, no other sample rates. That
is the exact shape of the banks it exists to read, and narrowing the input space
is a safety property rather than a shortcut — every read is bounds-checked and
every failure is a typed `Err`, never a panic.

If you want a full FLAC implementation, use [`claxon`] or [`symphonia`]. They are
better at that job and they are what you should reach for.

[`claxon`]: https://crates.io/crates/claxon
[`symphonia`]: https://crates.io/crates/symphonia

## Why it exists as a crate at all

The `ferrosintesis` workspace's dependency closure is 100% first-party path
crates — zero `source =` lines in its `Cargo.lock` — which is what lets a fresh
clone build the synth and render its whole catalogue with no network access at
all. A registry decoder would forfeit that for every consumer.

It is a separate package rather than a module because three crates need it:
`ferrosintesis` itself, and the two drum-bank asset crates, which decode PCM
inside the asset crate rather than handing raw bytes upward. One shared crate is
what stops that becoming three copies of a bit reader.

## What it implements

Per the FLAC specification (RFC 9639): STREAMINFO, and the CONSTANT / VERBATIM /
FIXED / LPC subframe types with Rice and Rice2 partitioned residuals including
the escape encoding.

Decoding verifies the result against the MD5 of the unencoded audio that the
encoder recorded in STREAMINFO, so a stream carries its own proof that what came
out is what went in.

## Usage

```rust
let pcm: Vec<i16> = ferrosintesis_flac::decode_mono16(bytes)?;
```

## Licence

MIT OR Apache-2.0, matching `ferrosintesis`.
