//! Minimal Standard MIDI File reader: extracts the tempo map, note,
//! controller, pitch-bend and aftertouch (channel and polyphonic) events
//! with absolute times in seconds. Supports type 0/1, running status, and
//! skips anything it does not model (sysex and metas such as lyrics and
//! key signatures).

use crate::error::{MidiError, MAX_MIDI_FILE_BYTES, MAX_SONG_SECONDS};
use std::path::Path;

/// Bytes an SMF variable-length quantity may occupy. SMF 1.0 fixes this at four,
/// which is why the largest representable VLQ is 0x0FFF_FFFF.
const VLQ_MAX_BYTES: usize = 4;

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
    /// Roland-GS "Use for Rhythm Part" (SysEx `40 1x 15`): declare/undeclare a
    /// channel a drum/rhythm part. `on` = the value was MAP1 or MAP2 (not OFF).
    DrumMode {
        ch: u8,
        on: bool,
    },
    /// Roland-GS Reset (SysEx `40 00 7F`): revert part modes to default — clears
    /// every GS-declared rhythm part (channel 10 stays drums by the ch==9 rule).
    GsReset,
    /// GM System On (universal `F0 7E .. 09 01 F7`): restore the full GM initial
    /// state, stopping voices and resetting channels and effects.
    GmReset,
    /// XG System On (`F0 43 1n 4C 00 00 7E 00 F7`): reset the XG effect state
    /// (reverb/chorus/variation insert) to engine defaults. Voices and channel
    /// state are untouched.
    XgReset,
    /// An XG Effect1-block parameter change (`F0 43 1n 4C 02 01 <lo> <data…>`).
    /// `addr_lo` is the Effect1 offset (e.g. 0x00 reverb type, 0x40 variation
    /// type); `data` holds the 1-2 7-bit data bytes (`len`). The engine holds
    /// all XG-effect semantics — the parser just forwards the raw parameter.
    XgEffectParam {
        addr_lo: u8,
        data: [u8; 2],
        len: u8,
    },
}

/// GS "block number" (the low nibble of the `0x1n` part-address byte) → 0-based
/// MIDI channel. The GS quirk: block 0 addresses Part 10 (channel 10); blocks
/// 1..9 address Parts 1..9; blocks A..F address Parts 11..16. Masks the nibble
/// internally so a malformed address byte can never produce an out-of-range
/// channel (the result is always 0..=15).
fn gs_block_to_channel(block: u8) -> u8 {
    match block & 0x0F {
        0 => 9,             // Part 10 (the default GM/GS drum channel)
        n @ 1..=9 => n - 1, // Parts 1..9
        n => n,             // A..F → Parts 11..16 (channels 11..16, index 10..15)
    }
}

/// Decode one complete modeled SysEx payload, excluding the framing `F0`/`F7`.
///
/// The live parser and the SMF parser both call this exact recognizer so message
/// shapes and reset scopes cannot drift between entry points. SysEx data is
/// seven-bit; rejecting any status byte here also keeps malformed SMFs aligned
/// with the live byte parser, which terminates capture on status.
pub(crate) fn decode_sysex_payload(payload: &[u8]) -> Option<EvKind> {
    if payload.iter().any(|&byte| byte >= 0x80) {
        return None;
    }

    match payload {
        // Universal non-realtime, any device, General MIDI, System On.
        [0x7E, _, 0x09, 0x01] => Some(EvKind::GmReset),
        // Yamaha XG parameter change, System block, System On.
        [0x43, device, 0x4C, 0x00, 0x00, 0x7E, 0x00] if device & 0xF0 == 0x10 => {
            Some(EvKind::XgReset)
        }
        // Yamaha XG Effect1 parameter, one or two data bytes.
        [0x43, device, 0x4C, 0x02, 0x01, addr_lo, d0] if device & 0xF0 == 0x10 => {
            Some(EvKind::XgEffectParam {
                addr_lo: *addr_lo,
                data: [*d0, 0],
                len: 1,
            })
        }
        [0x43, device, 0x4C, 0x02, 0x01, addr_lo, d0, d1] if device & 0xF0 == 0x10 => {
            Some(EvKind::XgEffectParam {
                addr_lo: *addr_lo,
                data: [*d0, *d1],
                len: 2,
            })
        }
        // Roland GS DT1, System block, GS Reset. Device/checksum stay lenient.
        [0x41, _, 0x42, 0x12, 0x40, 0x00, 0x7F, _, _] => Some(EvKind::GsReset),
        // Roland GS DT1, Part block, Use for Rhythm Part. 0=off, 1/2=maps.
        [0x41, _, 0x42, 0x12, 0x40, block, 0x15, map @ 0..=2, _] if block & 0xF0 == 0x10 => {
            Some(EvKind::DrumMode {
                ch: gs_block_to_channel(*block),
                on: *map != 0,
            })
        }
        _ => None,
    }
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

    /// One channel-voice data byte, normalized to MIDI's seven-bit domain.
    ///
    /// Keep this at the parser boundary so malformed SMFs cannot put values above 127
    /// into engine state. Masking matches the established malformed-note-key policy
    /// while preserving event alignment for the rest of the track.
    fn channel_data(&mut self) -> Result<u8, MidiError> {
        self.u8().map(|byte| byte & 0x7F)
    }

    fn peek(&self) -> Result<u8, MidiError> {
        Ok(*self.data.get(self.pos).ok_or(MidiError::UnexpectedEof)?)
    }

    fn bytes(&mut self, n: usize) -> Result<&'a [u8], MidiError> {
        // `n` comes from an attacker-controlled VLQ length. `self.pos + n` is not safe
        // to compute: on a 32-bit `usize` (i686, armv7, wasm32) a length near u32::MAX
        // overflows — panicking in debug, and WRAPPING in release to a small value that
        // yields a plausible-looking slice. Saturating turns both into the honest
        // UnexpectedEof, because a saturated end is always past `data.len()`.
        // MM-BUG-KILN-00101.
        let end = self.pos.saturating_add(n);
        let s = self
            .data
            .get(self.pos..end)
            .ok_or(MidiError::UnexpectedEof)?;
        self.pos = end;
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

    /// One SMF variable-length quantity: at most four bytes, so at most 0x0FFF_FFFF.
    ///
    /// MM-BUG-CRUCIBLE-00028: this used to loop until a byte cleared the continuation
    /// bit, with no byte count. A delta like `90 80 80 80 00` — five bytes, each with
    /// the continuation bit set until the last — overflowed `v << 7` on the fifth
    /// shift: a panic in checked builds, and in release a silent wrap that accepted a
    /// *different* tick value than the file encoded. Shorter overlong forms were
    /// accepted silently even when they did not overflow.
    ///
    /// The four-byte cap is what makes the arithmetic safe, not a checked shift: after
    /// three bytes `v` is at most 0x001F_FFFF, so the fourth `v << 7` reaches at most
    /// 0x0FFF_FF80 and cannot overflow. A fifth byte is refused before it is shifted.
    fn vlq(&mut self) -> Result<u32, MidiError> {
        let mut v: u32 = 0;
        for _ in 0..VLQ_MAX_BYTES {
            let b = self.u8()?;
            v = (v << 7) | (b & 0x7F) as u32;
            if b < 0x80 {
                return Ok(v);
            }
        }
        Err(MidiError::OverlongVlq)
    }
}

pub fn load(path: &Path) -> Result<Song, MidiError> {
    parse(&read_bounded(path)?)
}

/// Read a path into memory, refusing anything over [`MAX_MIDI_FILE_BYTES`].
///
/// MM-BUG-CRUCIBLE-00027: this used to be a bare `std::fs::read`, which materializes
/// the whole file before `parse` can apply a single check — so the parser's careful
/// treatment of MIDI bytes as attacker-controlled was bypassed by the very entry point
/// most callers use. A multi-gigabyte regular or sparse file exhausted memory before
/// any `MidiError` could be returned.
///
/// Two bounds, not one. The advertised size is checked FIRST, so an oversized file is
/// refused without reading a byte of it — that is what makes the sparse case cheap.
/// The read is then bounded as well, because the advertised size is not a promise: a
/// file can grow between the two calls, and not every filesystem reports a meaningful
/// length. Whichever bound trips, the error carries the size that tripped it.
fn read_bounded(path: &Path) -> Result<Vec<u8>, MidiError> {
    use std::io::Read;

    let io = |source| MidiError::Io {
        path: path.to_path_buf(),
        source,
    };
    let file = std::fs::File::open(path).map_err(io)?;
    let advertised = file.metadata().map_err(io)?.len();
    if advertised > MAX_MIDI_FILE_BYTES {
        return Err(MidiError::TooLarge { bytes: advertised });
    }

    let mut data = Vec::new();
    file.take(MAX_MIDI_FILE_BYTES + 1)
        .read_to_end(&mut data)
        .map_err(io)?;
    if data.len() as u64 > MAX_MIDI_FILE_BYTES {
        return Err(MidiError::TooLarge {
            bytes: data.len() as u64,
        });
    }
    Ok(data)
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
    // Saturating for the same reason as `Cursor::bytes`: `hlen` is the header's own
    // declared length, straight off the wire. A saturated position simply reads as EOF.
    // MM-BUG-KILN-00101.
    c.pos = 8usize.saturating_add(hlen);

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
        // Read the declared payload once, then parse through its own cursor. This makes
        // the MTrk boundary structural for every fixed-size field, VLQ, meta payload and
        // SysEx payload. A whole-file cursor only checked where an event STARTED, so a
        // truncated event could borrow bytes from the next chunk and then rewind.
        let track_data = c.bytes(len)?;
        let mut track = Cursor {
            data: track_data,
            pos: 0,
        };
        let mut tick: u32 = 0;
        // The running status is the last CHANNEL VOICE status byte (0x80..=0xEF).
        // A system byte — meta (0xFF) or SysEx (0xF0/0xF7) — applies to its own
        // event only and must NOT be latched here: latching it made the next
        // running-status event re-enter the meta/SysEx arm, where its data bytes
        // were read as a `kind`+`len` pair and `len` further bytes were swallowed,
        // desyncing the rest of the track (usually surfacing as `UnexpectedEof`).
        // SMF 1.0 says meta/SysEx cancel running status, so continuing it is
        // strictly malformed — but sequencers emit such files, so we carry the
        // latch across instead of desyncing.
        let mut running_status: u8 = 0;
        while track.pos < track.data.len() {
            tick = tick.wrapping_add(track.vlq()?);
            let status = if track.peek()? >= 0x80 {
                let explicit = track.u8()?;
                if (0x80..=0xEF).contains(&explicit) {
                    running_status = explicit;
                }
                explicit
            } else {
                // No channel status seen yet leaves the latch at 0, which falls to
                // the catch-all arm below and errors as `BadStatusByte { status: 0 }`.
                running_status
            };
            match status {
                0xFF => {
                    let kind = track.u8()?;
                    let len = track.vlq()? as usize;
                    let payload = track.bytes(len)?;
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
                    let len = track.vlq()? as usize;
                    let payload = track.bytes(len)?;
                    // In an SMF only F0 begins a SysEx message. Accept a complete
                    // single-event message; standalone F7 escape/continuation data
                    // and unterminated F0 packets are deliberately not recognized.
                    if status == 0xF0 {
                        if let Some(body) = payload.strip_suffix(&[0xF7]) {
                            if let Some(kind) = decode_sysex_payload(body) {
                                raw.push((tick, seq, kind));
                                seq += 1;
                            }
                        }
                    }
                }
                _ => {
                    let ch = status & 0x0F;
                    let kind = status & 0xF0;
                    match kind {
                        0x80 => {
                            let key = track.channel_data()?;
                            let _v = track.channel_data()?;
                            raw.push((tick, seq, EvKind::NoteOff { ch, key }));
                        }
                        0x90 => {
                            let key = track.channel_data()?;
                            let vel = track.channel_data()?;
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
                            let num = track.channel_data()?;
                            let val = track.channel_data()?;
                            raw.push((tick, seq, EvKind::Cc { ch, num, val }));
                        }
                        0xC0 => {
                            let prog = track.channel_data()?;
                            raw.push((tick, seq, EvKind::Prog { ch, prog }));
                        }
                        0xD0 => {
                            let val = track.channel_data()?;
                            raw.push((tick, seq, EvKind::Aftertouch { ch, val }));
                        }
                        0xE0 => {
                            let lsb = track.channel_data()? as i32;
                            let msb = track.channel_data()? as i32;
                            let val = (msb << 7) | lsb; // 0..16383, centre 8192
                            let semis = (val - 8192) as f32 / 8192.0 * 2.0;
                            raw.push((tick, seq, EvKind::Bend { ch, semis }));
                        }
                        0xA0 => {
                            let key = track.channel_data()?;
                            let val = track.channel_data()?;
                            raw.push((tick, seq, EvKind::PolyAftertouch { ch, key, val }));
                        }
                        _ => return Err(MidiError::BadStatusByte { status }),
                    }
                    seq += 1;
                }
            }
        }
    }

    // tick -> seconds via the tempo map
    // A track may author several Set-Tempo events at one tick. Preserve their encounter
    // order while sorting by tick, then make the effective map explicit: the last
    // authored value governs the following interval. Sorting the `(tick, tempo)` tuples
    // used to break this by ordering equal-tick entries numerically by tempo instead.
    tempos.sort_by_key(|&(tick, _)| tick);
    let mut effective_tempos: Vec<(u32, u32)> = Vec::with_capacity(tempos.len());
    for (tick, us) in tempos {
        if let Some(last) = effective_tempos.last_mut() {
            if last.0 == tick {
                last.1 = us;
                continue;
            }
        }
        effective_tempos.push((tick, us));
    }
    let mut tempos = effective_tempos;
    if tempos.is_empty() {
        tempos.push((0, 500_000)); // MIDI default 120 bpm
    } else if tempos[0].0 > 0 {
        // The SMF default 120 bpm governs until the first Set-Tempo. Without a
        // tick-0 anchor, the prefix [0, first_tempo_tick) would be timed at the
        // first *authored* tempo, and every pre-tempo event would collapse onto
        // that change's timestamp via the `to_sec` saturating-sub floor
        // (MM-BUG-KILN-00032). Insert the default so the prefix is 120 bpm.
        tempos.insert(0, (0, 500_000));
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

    // GM System On establishes the defaults for a tick; simultaneous authored
    // setup then overrides them. Format-1 track order must not reverse that.
    raw.sort_by_key(|&(tick, seq, kind)| (tick, !matches!(kind, EvKind::GmReset), seq));
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

    fn read_vlq(bytes: &[u8]) -> Result<u32, MidiError> {
        Cursor {
            data: bytes,
            pos: 0,
        }
        .vlq()
    }

    /// MM-BUG-CRUCIBLE-00028: the VLQ reader honours SMF's four-byte limit.
    ///
    /// The decoder is tested directly rather than through a whole file because the
    /// interesting values cannot survive a round trip: a maximal delta of 0x0FFF_FFFF
    /// ticks is about 6.5 days at 480 tpqn and 120 bpm, so a file carrying one is
    /// rejected as `TooLong` before its VLQ handling could be observed. Testing the
    /// boundary here separates "the decoder is correct" from "the song is plausible".
    #[test]
    fn vlq_honours_the_four_byte_limit_at_both_ends() {
        // Every valid length, including both boundaries.
        assert_eq!(read_vlq(&[0x00]).unwrap(), 0);
        assert_eq!(read_vlq(&[0x7F]).unwrap(), 127);
        assert_eq!(read_vlq(&[0x81, 0x00]).unwrap(), 128);
        assert_eq!(read_vlq(&[0xC0, 0x80, 0x00]).unwrap(), 0x0010_0000);
        // The largest value four bytes can encode. The old reader reached this fine;
        // what it could not do was refuse the byte AFTER it.
        assert_eq!(read_vlq(&[0xFF, 0xFF, 0xFF, 0x7F]).unwrap(), 0x0FFF_FFFF);

        // The bug's own fixture: five bytes, the first four all continuations. The old
        // reader shifted a fifth time — a panic in a checked build, and in release a
        // silent wrap to a DIFFERENT tick value than the file encoded.
        assert!(matches!(
            read_vlq(&[0x90, 0x80, 0x80, 0x80, 0x00]),
            Err(MidiError::OverlongVlq)
        ));
        // An overlong encoding is refused even when it would not have overflowed:
        // five bytes encoding the value 0.
        assert!(matches!(
            read_vlq(&[0x80, 0x80, 0x80, 0x80, 0x00]),
            Err(MidiError::OverlongVlq)
        ));
        // A truncated VLQ is still EOF, not an overlong one — the two must not merge.
        assert!(matches!(
            read_vlq(&[0x80, 0x80]),
            Err(MidiError::UnexpectedEof)
        ));
    }

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

    #[test]
    fn equal_tick_tempo_changes_are_last_authored_wins() {
        fn file_with_tempos(first: u32, second: u32) -> Vec<u8> {
            let mut d = Vec::new();
            d.extend(b"MThd");
            d.extend(6u32.to_be_bytes());
            d.extend(0u16.to_be_bytes());
            d.extend(1u16.to_be_bytes());
            d.extend(480u16.to_be_bytes());

            let mut tr = Vec::new();
            for us_per_quarter in [first, second] {
                tr.extend([0x00, 0xFF, 0x51, 0x03]);
                tr.extend(&us_per_quarter.to_be_bytes()[1..]);
            }
            tr.extend([0x00, 0x90, 60, 100]);
            tr.extend([0x83, 0x60, 0x80, 60, 0]);
            tr.extend([0x00, 0xFF, 0x2F, 0x00]);
            d.extend(b"MTrk");
            d.extend((tr.len() as u32).to_be_bytes());
            d.extend(tr);
            d
        }

        let cases = [
            (1_000_000, 500_000, 120.0, 0.5),
            (500_000, 1_000_000, 60.0, 1.0),
        ];
        for (first, second, expected_bpm, expected_seconds) in cases {
            let song = parse(&file_with_tempos(first, second)).unwrap();
            assert!(
                (song.initial_bpm - expected_bpm).abs() < 1e-9,
                "{first} then {second}: initial BPM {} != {expected_bpm}",
                song.initial_bpm
            );
            assert!(
                (song.seconds - expected_seconds).abs() < 1e-9,
                "{first} then {second}: timeline {} s != {expected_seconds} s",
                song.seconds
            );
        }
    }

    /// MM-BUG-KILN-00032: when the first Set-Tempo is at a tick > 0, the SMF
    /// default 120 bpm must govern the prefix. Pre-tempo events must be timed at
    /// 120 bpm — NOT at the later authored tempo, and NOT collapsed onto the
    /// first tempo change's timestamp.
    #[test]
    fn default_tempo_governs_before_a_delayed_first_tempo() {
        let mut d: Vec<u8> = Vec::new();
        d.extend(b"MThd");
        d.extend(6u32.to_be_bytes());
        d.extend(0u16.to_be_bytes()); // format 0
        d.extend(1u16.to_be_bytes()); // 1 track
        d.extend(480u16.to_be_bytes()); // 480 ticks per quarter
        let mut tr: Vec<u8> = Vec::new();
        // Note-on at tick 0, BEFORE any Set-Tempo.
        tr.extend([0x00, 0x90, 60, 100]);
        // First Set-Tempo DELAYED to tick 480 (delta 480 = VLQ 0x83 0x60):
        // 60 bpm = 1_000_000 us/quarter = 0x0F4240.
        tr.extend([0x83, 0x60, 0xFF, 0x51, 0x03, 0x0F, 0x42, 0x40]);
        // Note-on at tick 480.
        tr.extend([0x00, 0x90, 62, 100]);
        // Note-on at tick 960.
        tr.extend([0x83, 0x60, 0x90, 64, 100]);
        tr.extend([0x00, 0xFF, 0x2F, 0x00]);
        d.extend(b"MTrk");
        d.extend((tr.len() as u32).to_be_bytes());
        d.extend(&tr);

        let song = parse(&d).unwrap();
        let secs: Vec<f64> = song.events.iter().map(|e| e.sec).collect();
        assert_eq!(song.events.len(), 3, "{:?}", song.events);
        // tick 0 at the 120 bpm default → 0.0 s (the bug times the prefix at 60
        // bpm and collapses this to the first tempo change's time, 1.0 s).
        assert!(
            secs[0].abs() < 1e-9,
            "pre-tempo note not at 0 s: {}",
            secs[0]
        );
        // tick 480 = one quarter at the 120 bpm default → 0.5 s (bug: 1.0 s).
        assert!(
            (secs[1] - 0.5).abs() < 1e-9,
            "tick-480 note mis-timed: {}",
            secs[1]
        );
        // tick 960 = 480 ticks @120bpm (0.5 s) + 480 ticks @60bpm (1.0 s) → 1.5 s.
        assert!(
            (secs[2] - 1.5).abs() < 1e-9,
            "post-tempo note mis-timed: {}",
            secs[2]
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

    #[test]
    fn program_change_data_bytes_are_limited_to_seven_bits() {
        let song = parse(&file_from_track(&[0x00, 0xC0, 0xFF])).unwrap();
        assert!(
            matches!(song.events[0].kind, EvKind::Prog { ch: 0, prog: 127 }),
            "{:?}",
            song.events[0].kind
        );
    }

    /// Format-0 file wrapping one track's raw event bytes (+ end-of-track).
    fn file_from_track(events: &[u8]) -> Vec<u8> {
        let mut d = Vec::new();
        d.extend(b"MThd");
        d.extend(6u32.to_be_bytes());
        d.extend(0u16.to_be_bytes()); // format 0
        d.extend(1u16.to_be_bytes()); // 1 track
        d.extend(480u16.to_be_bytes());
        let mut tr = Vec::from(events);
        tr.extend([0x00, 0xFF, 0x2F, 0x00]); // end of track
        d.extend(b"MTrk");
        d.extend((tr.len() as u32).to_be_bytes());
        d.extend(&tr);
        d
    }

    #[test]
    fn event_reads_cannot_cross_the_declared_track_boundary() {
        let mut d = Vec::new();
        d.extend(b"MThd");
        d.extend(6u32.to_be_bytes());
        d.extend(1u16.to_be_bytes()); // format 1
        d.extend(2u16.to_be_bytes()); // 2 tracks
        d.extend(480u16.to_be_bytes());

        // Track 0 ends after the Program Change status, before its required data byte.
        d.extend(b"MTrk");
        d.extend(2u32.to_be_bytes());
        d.extend([0x00, 0xC0]);

        // A valid track follows immediately. The old whole-file cursor borrowed its
        // leading 'M' as track 0's missing program byte, then rewound and parsed it again.
        let track_1 = [
            0x00, 0x90, 60, 100, // note on
            0x60, 0x80, 60, 0, // note off
            0x00, 0xFF, 0x2F, 0x00, // end of track
        ];
        d.extend(b"MTrk");
        d.extend((track_1.len() as u32).to_be_bytes());
        d.extend(track_1);

        assert!(
            matches!(parse(&d), Err(MidiError::UnexpectedEof)),
            "an event truncated by its MTrk boundary borrowed bytes from the next chunk"
        );
    }

    /// A GS "Use for Rhythm Part" SysEx track event (delta 0): part block `blk`
    /// (low nibble), map value `mm`. The Roland checksum byte is arbitrary here —
    /// the parser is deliberately lenient about it.
    fn gs_rhythm(blk: u8, mm: u8) -> Vec<u8> {
        let payload = [
            0x41,
            0x10,
            0x42,
            0x12,
            0x40,
            0x10 | blk,
            0x15,
            mm,
            0x00,
            0xF7,
        ];
        let mut ev = vec![0x00, 0xF0, payload.len() as u8];
        ev.extend(payload);
        ev
    }

    /// GS "Use for Rhythm Part" decodes to `DrumMode` with the GS block→channel map.
    #[test]
    fn gs_use_for_rhythm_part_decodes() {
        // block A → Part 11 → channel index 10; MAP1 → on.
        let s = parse(&file_from_track(&gs_rhythm(0x0A, 1))).unwrap();
        assert_eq!(s.events.len(), 1);
        assert!(
            matches!(s.events[0].kind, EvKind::DrumMode { ch: 10, on: true }),
            "{:?}",
            s.events[0].kind
        );
        // block 0 → Part 10 → channel 9 (the GS quirk).
        assert!(matches!(
            parse(&file_from_track(&gs_rhythm(0x00, 2))).unwrap().events[0].kind,
            EvKind::DrumMode { ch: 9, on: true }
        ));
        // block 1 → Part 1 → channel 0 (exercises the `1..=9 → n-1` arm).
        assert!(matches!(
            parse(&file_from_track(&gs_rhythm(0x01, 1))).unwrap().events[0].kind,
            EvKind::DrumMode { ch: 0, on: true }
        ));
        // map value 0 → off.
        assert!(matches!(
            parse(&file_from_track(&gs_rhythm(0x0A, 0))).unwrap().events[0].kind,
            EvKind::DrumMode { ch: 10, on: false }
        ));
    }

    /// GS Reset decodes to `GsReset`; near-miss and malformed messages emit nothing
    /// (and never panic) — the byte-identical-album invariant rests on this.
    #[test]
    fn gs_reset_and_near_misses() {
        // GS Reset (40 00 7F) → GsReset, not DrumMode.
        let reset = {
            let p = [0x41u8, 0x10, 0x42, 0x12, 0x40, 0x00, 0x7F, 0x00, 0x41, 0xF7];
            let mut e = vec![0x00, 0xF0, p.len() as u8];
            e.extend(p);
            e
        };
        assert!(matches!(
            parse(&file_from_track(&reset)).unwrap().events[0].kind,
            EvKind::GsReset
        ));

        // Wrong param offset (0x16 not 0x15) → ignored. payload[6] = ev[3+6].
        let mut near = gs_rhythm(0x0A, 1);
        near[3 + 6] = 0x16;
        assert!(parse(&file_from_track(&near)).unwrap().events.is_empty());

        // Non-part high nibble (address 40 2x 15) → ignored. payload[5] = ev[3+5].
        let mut np = gs_rhythm(0x0A, 1);
        np[3 + 5] = 0x2A;
        assert!(parse(&file_from_track(&np)).unwrap().events.is_empty());

        // Invalid map value (mm = 3) → no DrumMode.
        assert!(parse(&file_from_track(&gs_rhythm(0x0A, 3)))
            .unwrap()
            .events
            .is_empty());

        // Truncated payload (len < 8) → no event, no panic.
        let trunc = {
            let p = [0x41u8, 0x10, 0x42, 0x12, 0x40];
            let mut e = vec![0x00, 0xF0, p.len() as u8];
            e.extend(p);
            e
        };
        assert!(parse(&file_from_track(&trunc)).unwrap().events.is_empty());
    }

    /// Wrap a raw SysEx payload (the bytes after F0, ending in F7) as a delta-0
    /// track event.
    fn sysex_event(payload: &[u8]) -> Vec<u8> {
        let mut ev = vec![0x00, 0xF0, payload.len() as u8];
        ev.extend(payload);
        ev
    }

    /// XG effect-block parameter changes decode to `XgEffectParam` with the right
    /// offset, data and length; XG and GM System On retain their distinct reset
    /// scopes; non-effect XG addresses and near-misses are ignored.
    #[test]
    fn xg_effect_sysex_decodes() {
        // Variation Type (02 01 40 = 4B 11) → 2-byte param at offset 0x40.
        let var = sysex_event(&[0x43, 0x10, 0x4C, 0x02, 0x01, 0x40, 0x4B, 0x11, 0xF7]);
        assert!(
            matches!(
                parse(&file_from_track(&var)).unwrap().events[0].kind,
                EvKind::XgEffectParam {
                    addr_lo: 0x40,
                    data: [0x4B, 0x11],
                    len: 2
                }
            ),
            "{:?}",
            parse(&file_from_track(&var)).unwrap().events[0].kind
        );

        // Variation Connection (02 01 5A = 00) → 1-byte param at offset 0x5A.
        let conn = sysex_event(&[0x43, 0x10, 0x4C, 0x02, 0x01, 0x5A, 0x00, 0xF7]);
        assert!(matches!(
            parse(&file_from_track(&conn)).unwrap().events[0].kind,
            EvKind::XgEffectParam {
                addr_lo: 0x5A,
                data: [0x00, _],
                len: 1
            }
        ));

        // XG System On (00 00 7E 00) → XgReset.
        let xg_on = sysex_event(&[0x43, 0x10, 0x4C, 0x00, 0x00, 0x7E, 0x00, 0xF7]);
        assert!(matches!(
            parse(&file_from_track(&xg_on)).unwrap().events[0].kind,
            EvKind::XgReset
        ));

        // GM System On (universal 7E 7F 09 01) → its own full reset.
        let gm_on = sysex_event(&[0x7E, 0x7F, 0x09, 0x01, 0xF7]);
        assert!(matches!(
            parse(&file_from_track(&gm_on)).unwrap().events[0].kind,
            EvKind::GmReset
        ));

        // A non-effect XG address (System block 00 00 04 = master volume) → ignored.
        let sysblk = sysex_event(&[0x43, 0x10, 0x4C, 0x00, 0x00, 0x04, 0x7F, 0xF7]);
        assert!(parse(&file_from_track(&sysblk)).unwrap().events.is_empty());

        // Wrong Yamaha model ID (0x4B not 0x4C) → ignored.
        let badmodel = sysex_event(&[0x43, 0x10, 0x4B, 0x02, 0x01, 0x40, 0x4B, 0x11, 0xF7]);
        assert!(parse(&file_from_track(&badmodel))
            .unwrap()
            .events
            .is_empty());
    }

    /// MM-BUG-KILN-00035: destructive reset recognition requires a complete,
    /// exact, seven-bit payload in an F0 event. Prefixes and standalone F7 escape
    /// data must not change engine state.
    #[test]
    fn system_sysex_rejects_malformed_shapes() {
        let cases = [
            sysex_event(&[0x7E, 0x7F, 0x09, 0x01]), // unterminated GM On
            sysex_event(&[0x7E, 0x7F, 0x09, 0x01, 0x00, 0xF7]), // extended prefix
            sysex_event(&[0x7E, 0xFF, 0x09, 0x01, 0xF7]), // high-bit payload
            sysex_event(&[0x43, 0x10, 0x4C, 0x00, 0x00, 0x7E, 0x01, 0xF7]), // bad XG data
            sysex_event(&[0x43, 0x10, 0x4C, 0x02, 0x01, 0x5A, 0, 1, 2, 0xF7]), // too long
        ];
        for events in cases {
            assert!(
                parse(&file_from_track(&events)).unwrap().events.is_empty(),
                "malformed SysEx decoded: {events:02X?}"
            );
        }

        let escaped_gm = [0x00, 0xF7, 0x05, 0x7E, 0x7F, 0x09, 0x01, 0xF7];
        assert!(
            parse(&file_from_track(&escaped_gm))
                .unwrap()
                .events
                .is_empty(),
            "standalone F7 escape data decoded as GM On"
        );
    }

    /// A format-1 track holding GM On must establish defaults before simultaneous
    /// setup events from earlier tracks, regardless of file track order.
    #[test]
    fn gm_reset_sorts_before_same_tick_setup_across_tracks() {
        let mut data = Vec::new();
        data.extend(b"MThd");
        data.extend(6u32.to_be_bytes());
        data.extend(1u16.to_be_bytes());
        data.extend(2u16.to_be_bytes());
        data.extend(480u16.to_be_bytes());
        for events in [
            vec![0x00, 0xC0, 30],
            sysex_event(&[0x7E, 0x7F, 0x09, 0x01, 0xF7]),
        ] {
            let mut track = events;
            track.extend([0x00, 0xFF, 0x2F, 0x00]);
            data.extend(b"MTrk");
            data.extend((track.len() as u32).to_be_bytes());
            data.extend(track);
        }

        let song = parse(&data).unwrap();
        assert!(matches!(song.events[0].kind, EvKind::GmReset));
        assert!(matches!(
            song.events[1].kind,
            EvKind::Prog { ch: 0, prog: 30 }
        ));
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

    #[test]
    fn note_key_data_bytes_are_limited_to_seven_bits() {
        let song = parse(&file_from_track(&[
            0x00, 0x90, 200, 100, // NoteOn: 200 -> 72
            0x00, 0xA0, 200, 64, // PolyAftertouch: 200 -> 72
            0x60, 0x80, 200, 0, // NoteOff: 200 -> 72
        ]))
        .unwrap();

        assert!(matches!(
            song.events[0].kind,
            EvKind::NoteOn {
                ch: 0,
                key: 72,
                vel: 100
            }
        ));
        assert!(matches!(
            song.events[1].kind,
            EvKind::PolyAftertouch {
                ch: 0,
                key: 72,
                val: 64
            }
        ));
        assert!(matches!(
            song.events[2].kind,
            EvKind::NoteOff { ch: 0, key: 72 }
        ));
    }

    #[test]
    fn all_retained_channel_data_fields_are_limited_to_seven_bits() {
        let song = parse(&file_from_track(&[
            0x00, 0x90, 60, 228, // NoteOn velocity: 228 -> 100
            0x00, 0xB0, 199, 255, // CC number/value: 199 -> 71, 255 -> 127
            0x00, 0xD0, 192, // channel pressure: 192 -> 64
            0x00, 0xE0, 255, 255, // bend bytes: both -> 127
            0x00, 0xA0, 60, 192, // poly pressure: 192 -> 64
            0x60, 0x80, 60, 255, // ignored NoteOff velocity is consumed consistently
        ]))
        .unwrap();

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
            EvKind::Cc {
                ch: 0,
                num: 71,
                val: 127
            }
        ));
        assert!(matches!(
            song.events[2].kind,
            EvKind::Aftertouch { ch: 0, val: 64 }
        ));
        assert!(matches!(
            song.events[3].kind,
            EvKind::Bend { ch: 0, semis }
                if (semis - 1.999_755_9).abs() < 1e-6
        ));
        assert!(matches!(
            song.events[4].kind,
            EvKind::PolyAftertouch {
                ch: 0,
                key: 60,
                val: 64
            }
        ));
        assert!(matches!(
            song.events[5].kind,
            EvKind::NoteOff { ch: 0, key: 60 }
        ));
    }

    /// Running status must survive an interleaved META event.
    ///
    /// SMF 1.0 says meta/SysEx cancel running status, so a file that continues it
    /// is strictly malformed — but real sequencers emit these. The failure mode we
    /// are ruling out is not a clean rejection but a SILENT DESYNC: with the system
    /// byte latched as the
    /// running status, the following data bytes are read as a meta `kind` + `len`
    /// pair and `len` further bytes are swallowed, corrupting the rest of the track.
    #[test]
    fn running_status_survives_meta_event() {
        let song = parse(&file_from_track(&[
            0x00, 0xB6, 0x0A, 0x4B, // explicit CC10=75 on channel 6
            0x00, 0xFF, 0x59, 0x02, 0x00, 0x00, // key-signature meta
            0x00, 0x40, 0x7F, // CC64=127 through the preceding running status
        ]))
        .unwrap();

        assert_eq!(song.events.len(), 2, "{:?}", song.events);
        assert!(
            matches!(
                song.events[1].kind,
                EvKind::Cc {
                    ch: 6,
                    num: 64,
                    val: 127
                }
            ),
            "{:?}",
            song.events[1].kind
        );
    }

    /// The same guarantee across a SysEx event — the `0xF0` arm reads its own
    /// length, so a latched `0xF0` swallows an arbitrary run of the track.
    #[test]
    fn running_status_survives_sysex_event() {
        let mut track = vec![0x00, 0x92, 60, 100]; // explicit NoteOn ch 2
        track.extend(gs_rhythm(0x0A, 1)); // GS SysEx between the two
        track.extend([0x60, 60, 0]); // NoteOff via running status

        let song = parse(&file_from_track(&track)).unwrap();

        assert_eq!(song.events.len(), 3, "{:?}", song.events);
        assert!(
            matches!(song.events[2].kind, EvKind::NoteOff { ch: 2, key: 60 }),
            "{:?}",
            song.events[2].kind
        );
    }

    /// A system status byte is used for its own event but must NOT become the
    /// running status: after meta/SysEx the latch still holds the last CHANNEL
    /// status, which is what the two tests above rely on.
    #[test]
    fn system_status_never_becomes_the_running_status() {
        // No channel status has been seen when the data byte arrives, so the latch
        // is still empty — that must surface as a clean error, never as a meta
        // event parsed from the preceding 0xFF.
        match parse(&file_from_track(&[
            0x00, 0xFF, 0x59, 0x02, 0x00, 0x00, // meta first
            0x00, 0x40, 0x7F, // data bytes with no channel status ever set
        ])) {
            Err(MidiError::BadStatusByte { status: 0 }) => {}
            Err(e) => panic!("expected BadStatusByte {{ status: 0 }}, got {e:?}"),
            Ok(_) => panic!("expected a clean error, not a silently parsed song"),
        }
    }
}
