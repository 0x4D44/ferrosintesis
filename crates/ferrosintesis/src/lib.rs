//! Library surface for ferrosintesis.

pub mod live;
pub mod offline;

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
