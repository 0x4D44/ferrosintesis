//! Library surface for ferrosintesis.

#![forbid(unsafe_code)]

pub mod live;
pub mod offline;

/// Whether this build contains the optional compile-time attack-sample bank.
///
/// Disable the crate's default features to build the fully modeled synth without
/// downloading or embedding the two sample packages.
pub const fn embedded_samples_available() -> bool {
    cfg!(feature = "embedded-samples")
}

pub(crate) mod altbank;
pub(crate) mod drums;
pub(crate) mod dsp;
pub(crate) mod engine;
pub(crate) mod midi;
pub(crate) mod reverb;
pub(crate) mod sampler;
#[cfg(test)]
pub(crate) mod testutil;
pub(crate) mod voices;
pub(crate) mod wav;
