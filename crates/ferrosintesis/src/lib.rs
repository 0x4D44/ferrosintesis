//! A pure-Rust General MIDI synthesizer. Its DSP code has no third-party Rust
//! dependencies. Default builds embed separately licensed recorded material
//! from first-party asset crates, so no external SoundFont or runtime sound-bank
//! lookup is required. Input is a Standard MIDI File; output is interleaved
//! stereo `f32`.
//!
//! Two surfaces:
//!
//! - [`offline`] — load or parse an SMF, then render, normalize, and atomically
//!   write a WAV with bounded audio memory. The path shown below.
//! - [`live`] — [`live::RealtimeSynth`]: raw MIDI bytes in via
//!   [`write_byte`](live::RealtimeSynth::write_byte), stereo blocks summed
//!   into your output buffer via
//!   [`render_add`](live::RealtimeSynth::render_add).
//!
//! ```no_run
//! use ferrosintesis::offline::{self, Normalization, Options};
//! # fn main() -> Result<(), Box<dyn std::error::Error>> {
//! // A one-note Standard MIDI File, assembled in memory: format 0, one
//! // track, 480 ticks per quarter; a harp plays middle C for one beat.
//! let mut smf: Vec<u8> = Vec::new();
//! smf.extend(b"MThd");
//! smf.extend(6u32.to_be_bytes()); // header length
//! smf.extend(0u16.to_be_bytes()); // format 0
//! smf.extend(1u16.to_be_bytes()); // one track
//! smf.extend(480u16.to_be_bytes()); // ticks per quarter note
//! let track = [
//!     0x00, 0xC0, 46, // program change: harp
//!     0x00, 0x90, 60, 100, // note on: middle C, velocity 100
//!     0x83, 0x60, 0x80, 60, 0, // 480 ticks later: note off
//!     0x00, 0xFF, 0x2F, 0x00, // end of track
//! ];
//! smf.extend(b"MTrk");
//! smf.extend((track.len() as u32).to_be_bytes());
//! smf.extend(track);
//!
//! let song = offline::parse(&smf)?;
//! let opt = Options::default().with_tail(1.0); // short reverb tail
//! let stats = offline::render_to_wav(
//!     &song,
//!     &opt,
//!     std::path::Path::new("output.wav"),
//!     Normalization::loudness(-18.0, -1.0),
//! )?;
//! assert!(stats.voices_spawned >= 1 && stats.peak > 0.0);
//! # Ok(())
//! # }
//! ```
//!
//! Rendering is deterministic for a fixed executable, MIDI file, and options.
//! The default `embedded-samples` feature compiles
//! roughly 111 MiB of recorded audio — 1156 WAVs across twenty-five
//! first-party asset crates — into the binary; `default-features = false`
//! builds the fully modeled synth instead, a far smaller artifact with
//! synthetic note onsets in place of the recorded ones.
//! [`embedded_samples_available`] reports which build this is. No unsafe
//! code, no build scripts.
//!
//! Most of that audio is CC0; ten of the twenty-five crates carry an
//! attribution obligation that travels with a distributed binary. The
//! `NOTICE` file at the repository root is the index of what you must
//! reproduce, and each asset crate packages the exact required text.
//!
//! All 128 GM melodic program numbers route to a synthesized voice family, but
//! programs within a family may share an engine and support varies by program.
//! The GM sound-effects block 120–127 also has explicit voice paths. This is not
//! a claim of GM conformance or reference-module timbre. The README carries the
//! program-by-program table; DESIGN.md in the repository carries the full design
//! essay.

#![forbid(unsafe_code)]
// The public surface ships to docs.rs. An undocumented public item is a bug, and the
// gate (`clippy -D warnings`) makes this one fail the build rather than rot quietly.
#![warn(missing_docs)]

pub mod live;
pub mod offline;

mod error;
pub use error::MidiError;

/// Whether this build contains the optional compile-time attack-sample bank.
///
/// Disable the crate's default features to build the fully modeled synth without
/// embedding any of the sample-asset packages. See the README's "Sample provenance
/// and licensing" section for what a default build embeds and what it obliges a
/// binary distributor to reproduce.
pub const fn embedded_samples_available() -> bool {
    cfg!(feature = "embedded-samples")
}

pub(crate) mod altbank;
pub(crate) mod drums;
pub(crate) mod dsp;
pub(crate) mod engine;
// The embedded sample banks are stored as FLAC. Decoding them needs a decoder,
// and a registry one would forfeit the zero-`source =` offline build CLAUDE.md
// pins — so this crate carries its own, deliberately scoped to the 16-bit mono
// 44.1 kHz subset the banks actually use.
pub(crate) mod flac;
// These oracles inspect sibling packages and repository policy. `.cargo/config.toml`
// enables them in a checkout; the published archive omits both the inputs and the cfg.
#[cfg(all(test, ferrosintesis_repository_tests))]
mod inventory;

#[cfg(all(test, ferrosintesis_repository_tests))]
mod balance;
#[cfg(all(test, ferrosintesis_repository_tests))]
mod licensing;
pub(crate) mod loudness;
#[cfg(all(test, ferrosintesis_repository_tests))]
mod manifest;
pub(crate) mod midi;
#[cfg(test)]
mod parse_robustness;
#[cfg(all(test, ferrosintesis_repository_tests))]
mod payload;
#[cfg(all(test, ferrosintesis_repository_tests))]
mod provenance;
#[cfg(all(test, ferrosintesis_repository_tests))]
mod render_profile;
pub(crate) mod reverb;
pub(crate) mod sampler;
pub(crate) mod scratch;
#[cfg(test)]
pub(crate) mod testutil;
#[cfg(test)]
mod velocity_law;
pub(crate) mod voices;
pub(crate) mod wav;
