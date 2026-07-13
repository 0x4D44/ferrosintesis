//! Offline MIDI-to-WAV rendering API used by the CLI.

use std::path::Path;

pub use crate::engine::{normalize_to_i16, Options, Stats};
pub use crate::loudness::integrated_lufs;
pub use crate::wav::write_wav;

pub struct Song(crate::midi::Song);

impl Song {
    pub fn seconds(&self) -> f64 {
        self.0.seconds
    }

    pub fn events_len(&self) -> usize {
        self.0.events.len()
    }

    pub fn markers_len(&self) -> usize {
        self.0.markers.len()
    }

    pub fn title(&self) -> &str {
        &self.0.title
    }

    pub fn initial_bpm(&self) -> f64 {
        self.0.initial_bpm
    }
}

pub fn load(path: &Path) -> Result<Song, String> {
    crate::midi::load(path).map(Song)
}

pub fn parse(data: &[u8]) -> Result<Song, String> {
    crate::midi::parse(data).map(Song)
}

pub fn render(song: &Song, opt: &Options) -> (Vec<f32>, Stats) {
    crate::engine::render(&song.0, opt)
}
