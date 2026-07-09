//! Placeholder crate reserving the `ferrosintesis` package name.
//!
//! The real crate will expose the modeled MIDI synthesizer currently developed
//! in the `midi-music` repository.

#![forbid(unsafe_code)]

/// The reserved public crate name.
pub const CRATE_NAME: &str = "ferrosintesis";

/// Returns the reservation status for this placeholder release.
pub fn status() -> &'static str {
    "ferrosintesis is reserved for a modeled MIDI synthesizer in Rust"
}
