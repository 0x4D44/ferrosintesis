//! Minimal Standard MIDI File reader: extracts the tempo map, note,
//! controller, pitch-bend and aftertouch (channel and polyphonic) events
//! with absolute times in seconds. Supports type 0/1, running status, and
//! skips anything it does not model (sysex and metas such as lyrics and
//! key signatures).

use crate::error::{MidiError, MAX_SONG_SECONDS};
use std::path::Path;

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum EvKind {
    NoteOn {
        ch: u8,
        key: u8,
        vel: u8,
    },
    NoteOff {
        ch: u8,
        key: u8,
    },
    Cc {
        ch: u8,
        num: u8,
        val: u8,
    },
    Prog {
        ch: u8,
        prog: u8,
    },
    /// Decoded at the GM default ±2-semitone range; the engine rescales by
    /// the channel's RPN 0 bend range.
    Bend {
        ch: u8,
        semis: f32,
    },
    /// Channel aftertouch (0xDn): one pressure value for the whole channel.
    Aftertouch {
        ch: u8,
        val: u8,
    },
    /// Polyphonic (key) aftertouch (0xAn): pressure on one held key.
    PolyAftertouch {
        ch: u8,
        key: u8,
        val: u8,
    },
}

#[derive(Debug, Clone)]
pub struct Ev {
    pub sec: f64,
    pub kind: EvKind,
}

pub struct Song {
    pub events: Vec<Ev>,
    pub seconds: f64,
    pub markers: Vec<(f64, String)>,
    pub title: String,
    pub initial_bpm: f64,
}

struct Cursor<'a> {
    data: &'a [u8],
    pos: usize,
}

impl<'a> Cursor<'a> {
    fn u8(&mut self) -> Result<u8, MidiError> {
        let b = *self.data.get(self.pos).ok_or(MidiError::UnexpectedEof)?;
        self.pos += 1;
        Ok(b)
    }

    fn peek(&self) -> Result<u8, MidiError> {
        Ok(*self.data.get(self.pos).ok_or(MidiError::UnexpectedEof)?)
    }

    fn bytes(&mut self, n: usize) -> Result<&'a [u8], MidiError> {
        let s = self
            .data
            .get(self.pos..self.pos + n)
            .ok_or(MidiError::UnexpectedEof)?;
        self.pos += n;
        Ok(s)
    }

    fn u16(&mut self) -> Result<u16, MidiError> {
        let b = self.bytes(2)?;
        Ok(u16::from_be_bytes([b[0], b[1]]))
    }

    fn u32(&mut self) -> Result<u32, MidiError> {
        let b = self.bytes(4)?;
        Ok(u32::from_be_bytes([b[0], b[1], b[2], b[3]]))
    }

    fn vlq(&mut self) -> Result<u32, MidiError> {
        let mut v: u32 = 0;
        loop {
            let b = self.u8()?;
            v = (v << 7) | (b & 0x7F) as u32;
            if b < 0x80 {
                return Ok(v);
            }
        }
    }
}

pub fn load(path: &Path) -> Result<Song, MidiError> {
    let data = std::fs::read(path).map_err(|source| MidiError::Io {
        path: path.to_path_buf(),
        source,
    })?;
    parse(&data)
}

pub fn parse(data: &[u8]) -> Result<Song, MidiError> {
    let mut c = Cursor { data, pos: 0 };
    if c.bytes(4)? != b"MThd" {
        return Err(MidiError::NotMidi);
    }
    let hlen = c.u32()? as usize;
    let fmt = c.u16()?;
    let ntracks = c.u16()?;
    let division = c.u16()?;
    if division & 0x8000 != 0 {
        return Err(MidiError::UnsupportedTimeDivision);
    }
    if fmt > 1 {
        return Err(MidiError::UnsupportedFormat { format: fmt });
    }
    c.pos = 8 + hlen;

    // pass over every track, collecting tick-stamped events
    let mut raw: Vec<(u32, u32, EvKind)> = Vec::new(); // (tick, seq, kind)
    let mut tempos: Vec<(u32, u32)> = Vec::new(); // (tick, us per quarter)
    let mut raw_markers: Vec<(u32, String)> = Vec::new();
    let mut title = String::new();
    let mut seq: u32 = 0;

    for track_index in 0..ntracks {
        if c.bytes(4)? != b"MTrk" {
            return Err(MidiError::MissingTrack { index: track_index });
        }
        let len = c.u32()? as usize;
        let end = c.pos + len;
        let mut tick: u32 = 0;
        let mut status: u8 = 0;
        while c.pos < end {
            tick = tick.wrapping_add(c.vlq()?);
            if c.peek()? >= 0x80 {
                status = c.u8()?;
            }
            match status {
                0xFF => {
                    let kind = c.u8()?;
                    let len = c.vlq()? as usize;
                    let payload = c.bytes(len)?;
                    match kind {
                        0x51 if len >= 3 => {
                            let us = ((payload[0] as u32) << 16)
                                | ((payload[1] as u32) << 8)
                                | payload[2] as u32;
                            tempos.push((tick, us));
                        }
                        0x06 => {
                            raw_markers.push((tick, String::from_utf8_lossy(payload).into_owned()))
                        }
                        0x03 if track_index == 0 && title.is_empty() => {
                            title = String::from_utf8_lossy(payload).into_owned();
                        }
                        _ => {}
                    }
                }
                0xF0 | 0xF7 => {
                    let len = c.vlq()? as usize;
                    c.bytes(len)?;
                }
                _ => {
                    let ch = status & 0x0F;
                    let kind = status & 0xF0;
                    match kind {
                        0x80 => {
                            let key = c.u8()?;
                            let _v = c.u8()?;
                            raw.push((tick, seq, EvKind::NoteOff { ch, key }));
                        }
                        0x90 => {
                            let key = c.u8()?;
                            let vel = c.u8()?;
                            raw.push((
                                tick,
                                seq,
                                if vel > 0 {
                                    EvKind::NoteOn { ch, key, vel }
                                } else {
                                    EvKind::NoteOff { ch, key }
                                },
                            ));
                        }
                        0xB0 => {
                            let num = c.u8()?;
                            let val = c.u8()?;
                            raw.push((tick, seq, EvKind::Cc { ch, num, val }));
                        }
                        0xC0 => {
                            let prog = c.u8()?;
                            raw.push((tick, seq, EvKind::Prog { ch, prog }));
                        }
                        0xD0 => {
                            let val = c.u8()?;
                            raw.push((tick, seq, EvKind::Aftertouch { ch, val }));
                        }
                        0xE0 => {
                            let lsb = c.u8()? as i32;
                            let msb = c.u8()? as i32;
                            let val = (msb << 7) | lsb; // 0..16383, centre 8192
                            let semis = (val - 8192) as f32 / 8192.0 * 2.0;
                            raw.push((tick, seq, EvKind::Bend { ch, semis }));
                        }
                        0xA0 => {
                            let key = c.u8()?;
                            let val = c.u8()?;
                            raw.push((tick, seq, EvKind::PolyAftertouch { ch, key, val }));
                        }
                        _ => return Err(MidiError::BadStatusByte { status }),
                    }
                    seq += 1;
                }
            }
        }
        c.pos = end;
    }

    // tick -> seconds via the tempo map
    tempos.sort_unstable();
    if tempos.is_empty() {
        tempos.push((0, 500_000)); // MIDI default 120 bpm
    }
    let tpq = division as f64;
    // cumulative seconds at each tempo change
    let mut cum: Vec<(u32, f64, f64)> = Vec::with_capacity(tempos.len()); // (tick, sec, sec/tick)
    let mut sec = 0.0;
    let mut prev_tick = 0u32;
    let mut spt = tempos[0].1 as f64 / 1_000_000.0 / tpq;
    for &(tick, us) in &tempos {
        sec += (tick - prev_tick) as f64 * spt;
        prev_tick = tick;
        spt = us as f64 / 1_000_000.0 / tpq;
        cum.push((tick, sec, spt));
    }
    let to_sec = |tick: u32| -> f64 {
        let i = match cum.binary_search_by_key(&tick, |e| e.0) {
            Ok(i) => i,
            Err(0) => 0,
            Err(i) => i - 1,
        };
        let (t0, s0, spt) = cum[i];
        s0 + (tick.saturating_sub(t0)) as f64 * spt
    };

    raw.sort_by_key(|&(tick, seq, _)| (tick, seq));
    let events: Vec<Ev> = raw
        .into_iter()
        .map(|(tick, _, kind)| Ev {
            sec: to_sec(tick),
            kind,
        })
        .collect();
    let seconds = events.last().map(|e| e.sec).unwrap_or(0.0);
    // The tempo map is entirely attacker-controlled, and `render` allocates in
    // proportion to `seconds`. Refuse an absurd length here rather than let the
    // allocator abort the process on a few dozen bytes of hostile input.
    if !(seconds.is_finite() && seconds <= MAX_SONG_SECONDS) {
        return Err(MidiError::TooLong { seconds });
    }
    let markers = raw_markers
        .into_iter()
        .map(|(tick, text)| (to_sec(tick), text))
        .collect();
    let initial_bpm = 60_000_000.0 / tempos[0].1 as f64;
    Ok(Song {
        events,
        seconds,
        markers,
        title,
        initial_bpm,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Hand-assembled one-track file: 120 bpm for one quarter note, then
    /// 60 bpm; note-on at tick 0, note-off at tick 960 (two quarters).
    #[test]
    fn tempo_map_and_notes() {
        let mut d: Vec<u8> = Vec::new();
        d.extend(b"MThd");
        d.extend(6u32.to_be_bytes());
        d.extend(1u16.to_be_bytes());
        d.extend(1u16.to_be_bytes());
        d.extend(480u16.to_be_bytes());
        let mut tr: Vec<u8> = Vec::new();
        tr.extend([0x00, 0xFF, 0x51, 0x03, 0x07, 0xA1, 0x20]); // 500000 us
        tr.extend([0x00, 0x90, 60, 100]);
        // delta 480 = 0x83 0x60 in VLQ
        tr.extend([0x83, 0x60, 0xFF, 0x51, 0x03, 0x0F, 0x42, 0x40]); // 1000000 us
        tr.extend([0x83, 0x60, 0x80, 60, 0]);
        tr.extend([0x00, 0xFF, 0x2F, 0x00]);
        d.extend(b"MTrk");
        d.extend((tr.len() as u32).to_be_bytes());
        d.extend(&tr);

        let song = parse(&d).unwrap();
        assert_eq!(song.events.len(), 2);
        assert!(matches!(
            song.events[0].kind,
            EvKind::NoteOn {
                ch: 0,
                key: 60,
                vel: 100
            }
        ));
        // one quarter at 120 bpm (0.5 s) + one at 60 bpm (1.0 s)
        assert!(
            (song.events[1].sec - 1.5).abs() < 1e-9,
            "{}",
            song.events[1].sec
        );
    }

    /// Oracle 36 (midi half): a raw 0xC0 program-change byte reaches
    /// `EvKind::Prog` with the raw program number — no off-by-one.
    #[test]
    fn program_change_decodes_raw() {
        let mut d: Vec<u8> = Vec::new();
        d.extend(b"MThd");
        d.extend(6u32.to_be_bytes());
        d.extend(1u16.to_be_bytes());
        d.extend(1u16.to_be_bytes());
        d.extend(480u16.to_be_bytes());
        let mut tr: Vec<u8> = Vec::new();
        tr.extend([0x00, 0xC3, 30]); // program change: ch 3, prog 30 (overdrive)
        tr.extend([0x00, 0x93, 60, 100]); // note-on so the song has length
        tr.extend([0x60, 0x83, 60, 0]); // note-off (running-status new status)
        tr.extend([0x00, 0xFF, 0x2F, 0x00]);
        d.extend(b"MTrk");
        d.extend((tr.len() as u32).to_be_bytes());
        d.extend(&tr);

        let song = parse(&d).unwrap();
        assert!(
            matches!(song.events[0].kind, EvKind::Prog { ch: 3, prog: 30 }),
            "{:?}",
            song.events[0].kind
        );
    }

    /// A pitch-bend message decodes to the right signed semitone value.
    #[test]
    fn pitch_bend_decodes() {
        let mut d: Vec<u8> = Vec::new();
        d.extend(b"MThd");
        d.extend(6u32.to_be_bytes());
        d.extend(1u16.to_be_bytes());
        d.extend(1u16.to_be_bytes());
        d.extend(480u16.to_be_bytes());
        let mut tr: Vec<u8> = Vec::new();
        tr.extend([0x00, 0xFF, 0x51, 0x03, 0x07, 0xA1, 0x20]);
        // max-up bend: 0x3FFF (raw 16383) on channel 0
        tr.extend([0x00, 0xE0, 0x7F, 0x7F]);
        // centre (no bend)
        tr.extend([0x00, 0xE0, 0x00, 0x40]);
        // max-down bend: raw 0
        tr.extend([0x00, 0xE0, 0x00, 0x00]);
        tr.extend([0x00, 0xFF, 0x2F, 0x00]);
        d.extend(b"MTrk");
        d.extend((tr.len() as u32).to_be_bytes());
        d.extend(&tr);

        let song = parse(&d).unwrap();
        let bends: Vec<f32> = song
            .events
            .iter()
            .filter_map(|e| match e.kind {
                EvKind::Bend { semis, .. } => Some(semis),
                _ => None,
            })
            .collect();
        assert_eq!(bends.len(), 3);
        assert!((bends[0] - 2.0).abs() < 0.01, "{}", bends[0]);
        assert!(bends[1].abs() < 0.01, "{}", bends[1]);
        assert!((bends[2] - (-2.0)).abs() < 0.01, "{}", bends[2]);
    }

    /// Lyric (0x05) and key-signature (0x59) metas are skipped cleanly,
    /// and channel aftertouch (0xDn) decodes to an event.
    #[test]
    fn skips_lyrics_and_keysigs_parses_aftertouch() {
        let mut d: Vec<u8> = Vec::new();
        d.extend(b"MThd");
        d.extend(6u32.to_be_bytes());
        d.extend(1u16.to_be_bytes());
        d.extend(1u16.to_be_bytes());
        d.extend(480u16.to_be_bytes());
        let mut tr: Vec<u8> = Vec::new();
        tr.extend([0x00, 0xFF, 0x05, 0x03]); // lyric "hum"
        tr.extend(b"hum");
        tr.extend([0x00, 0xFF, 0x59, 0x02, 0x02, 0x00]); // key sig: 2 sharps, major
        tr.extend([0x00, 0x90, 60, 100]);
        tr.extend([0x00, 0xD1, 80]); // channel aftertouch, ch 1
        tr.extend([0x00, 0xFF, 0x05, 0x02]); // mid-note lyric
        tr.extend(b"ah");
        tr.extend([0x83, 0x60, 0x80, 60, 0]);
        tr.extend([0x00, 0xFF, 0x2F, 0x00]);
        d.extend(b"MTrk");
        d.extend((tr.len() as u32).to_be_bytes());
        d.extend(&tr);

        let song = parse(&d).unwrap();
        assert_eq!(song.events.len(), 3);
        assert!(matches!(
            song.events[0].kind,
            EvKind::NoteOn {
                ch: 0,
                key: 60,
                vel: 100
            }
        ));
        assert!(matches!(
            song.events[1].kind,
            EvKind::Aftertouch { ch: 1, val: 80 }
        ));
        assert!(matches!(
            song.events[2].kind,
            EvKind::NoteOff { ch: 0, key: 60 }
        ));
    }
}
