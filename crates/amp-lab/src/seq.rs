//! The backing-loop sequencer.
//!
//! Parsing happens once at startup, off the audio thread, into a flat list of
//! (frame, message). Playback then lives ON the audio thread and is just "emit
//! everything due before `pos + frames`", which is sample-accurate and free.
//! Driving this from the UI thread instead would jitter every event by a frame
//! interval (~16 ms) — inaudible on a pad, obvious on a snare.
//!
//! ferrosintesis keeps its own MIDI parser private (only `live` and `offline` are
//! public), so this reads the subset of SMF the committed loop actually uses.

/// One scheduled message: up to three bytes at an absolute frame offset.
#[derive(Clone, Copy, Debug)]
pub struct Event {
    pub frame: u64,
    pub bytes: [u8; 3],
    pub len: u8,
}

pub struct Loop {
    pub events: Vec<Event>,
    pub frames: u64,
}

fn vlq(d: &[u8], i: &mut usize) -> u32 {
    let mut v = 0u32;
    loop {
        if *i >= d.len() {
            return v;
        }
        let b = d[*i];
        *i += 1;
        v = (v << 7) | u32::from(b & 0x7F);
        if b & 0x80 == 0 {
            return v;
        }
    }
}

fn be16(d: &[u8], i: usize) -> u16 {
    u16::from(d[i]) << 8 | u16::from(d[i + 1])
}
fn be32(d: &[u8], i: usize) -> u32 {
    (u32::from(d[i]) << 24)
        | (u32::from(d[i + 1]) << 16)
        | (u32::from(d[i + 2]) << 8)
        | u32::from(d[i + 3])
}

impl Loop {
    /// Parse an SMF (format 0 or 1) into frame-scheduled events.
    ///
    /// Tempo is taken from the first Set-Tempo meta event; the loop we ship has a
    /// single constant tempo, and a tempo map would only add a scheduling mode the
    /// tool has no use for.
    pub fn parse(data: &[u8], sample_rate: f64) -> Result<Loop, String> {
        if data.len() < 14 || &data[0..4] != b"MThd" {
            return Err("not a MIDI file".into());
        }
        let ntrk = be16(data, 10) as usize;
        let div = be16(data, 12);
        if div & 0x8000 != 0 {
            return Err("SMPTE division not supported".into());
        }
        let ppq = f64::from(div);

        // Pass 1: gather (tick, message) across all tracks.
        let mut raw: Vec<(u64, [u8; 3], u8)> = Vec::new();
        let mut tempo_us = 500_000f64; // 120 bpm until a Set-Tempo says otherwise
        let mut pos = 14usize;
        for _ in 0..ntrk {
            if pos + 8 > data.len() || &data[pos..pos + 4] != b"MTrk" {
                break;
            }
            let len = be32(data, pos + 4) as usize;
            let end = (pos + 8 + len).min(data.len());
            let mut i = pos + 8;
            let mut tick = 0u64;
            let mut status = 0u8;
            while i < end {
                tick += u64::from(vlq(data, &mut i));
                if i >= end {
                    break;
                }
                let mut b = data[i];
                if b & 0x80 != 0 {
                    status = b;
                    i += 1;
                    if i > end {
                        break;
                    }
                } else {
                    b = status; // running status
                }
                match b {
                    0xFF => {
                        let ty = data[i];
                        i += 1;
                        let l = vlq(data, &mut i) as usize;
                        if ty == 0x51 && l == 3 && i + 3 <= data.len() {
                            tempo_us = f64::from(
                                (u32::from(data[i]) << 16)
                                    | (u32::from(data[i + 1]) << 8)
                                    | u32::from(data[i + 2]),
                            );
                        }
                        i += l;
                    }
                    0xF0 | 0xF7 => {
                        let l = vlq(data, &mut i) as usize;
                        i += l; // the loop authors no SysEx; skip it
                    }
                    _ => {
                        let hi = b & 0xF0;
                        let n = if matches!(hi, 0xC0 | 0xD0) { 1 } else { 2 };
                        if i + n > end {
                            break;
                        }
                        let mut msg = [b, 0, 0];
                        msg[1..=n].copy_from_slice(&data[i..i + n]);
                        raw.push((tick, msg, (n + 1) as u8));
                        i += n;
                    }
                }
            }
            pos = pos + 8 + len;
        }

        raw.sort_by_key(|e| e.0);
        let spt = tempo_us * 1e-6 / ppq; // seconds per tick
        let events: Vec<Event> = raw
            .iter()
            .map(|&(t, bytes, len)| Event {
                frame: (t as f64 * spt * sample_rate) as u64,
                bytes,
                len,
            })
            .collect();
        let last_tick = raw.last().map(|e| e.0).unwrap_or(0);
        // Round the loop out to a whole bar-ish boundary so the seam lands
        // musically: one beat of tail past the last event, minimum one beat.
        let end_tick = last_tick + ppq as u64;
        let frames = (end_tick as f64 * spt * sample_rate) as u64;
        Ok(Loop { events, frames })
    }
}

/// Playback cursor. Lives on the audio thread.
pub struct Player {
    pub pos: u64,
    idx: usize,
}

impl Default for Player {
    fn default() -> Self {
        Self::new()
    }
}

impl Player {
    pub fn new() -> Self {
        Player { pos: 0, idx: 0 }
    }

    pub fn rewind(&mut self) {
        self.pos = 0;
        self.idx = 0;
    }

    /// Advance `frames` and hand every message that falls in the span to `emit`.
    /// Wraps at the loop end, so playback is seamless and indefinite.
    pub fn advance(&mut self, lp: &Loop, frames: u64, mut emit: impl FnMut(&[u8])) {
        if lp.frames == 0 {
            return;
        }
        let mut left = frames;
        while left > 0 {
            let to_end = lp.frames - self.pos;
            let step = left.min(to_end);
            let until = self.pos + step;
            while self.idx < lp.events.len() && lp.events[self.idx].frame < until {
                let e = &lp.events[self.idx];
                emit(&e.bytes[..e.len as usize]);
                self.idx += 1;
            }
            self.pos += step;
            left -= step;
            if self.pos >= lp.frames {
                self.pos = 0;
                self.idx = 0;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A tiny format-0 file: one note on/off at tick 0 and 480.
    fn tiny() -> Vec<u8> {
        let mut trk = vec![
            0x00, 0xFF, 0x51, 0x03, 0x07, 0xA1, 0x20, // tempo 500000
            0x00, 0x90, 0x40, 0x64, // note on at tick 0
            0x83, 0x60, 0x80, 0x40, 0x00, // note off +480
            0x00, 0xFF, 0x2F, 0x00,
        ];
        let mut out = b"MThd".to_vec();
        out.extend_from_slice(&[0, 0, 0, 6, 0, 0, 0, 1, 0x01, 0xE0]); // ppq 480
        out.extend_from_slice(b"MTrk");
        out.extend_from_slice(&(trk.len() as u32).to_be_bytes());
        out.append(&mut trk);
        out
    }

    #[test]
    fn parses_and_schedules_by_frame() {
        let lp = Loop::parse(&tiny(), 44100.0).expect("parse");
        assert_eq!(lp.events.len(), 2);
        assert_eq!(lp.events[0].frame, 0);
        // 480 ticks at 500000us/quarter, ppq 480 -> 0.5 s -> 22050 frames
        assert_eq!(lp.events[1].frame, 22050);
    }

    #[test]
    fn wraps_seamlessly_and_repeats() {
        let lp = Loop::parse(&tiny(), 44100.0).expect("parse");
        let mut p = Player::new();
        let mut n = 0;
        // three full loops in one-block steps must emit 3x the events
        let blocks = (lp.frames * 3).div_ceil(512);
        for _ in 0..blocks {
            p.advance(&lp, 512, |_| n += 1);
        }
        assert!(n >= 6, "expected >= 6 events over three loops, got {n}");
    }

    /// Is this message something that changes a channel's VOICE (as opposed to its
    /// mix placement)? Program Change, or a Bank Select MSB/LSB.
    fn is_voice_change(msg: &[u8]) -> bool {
        match msg[0] & 0xF0 {
            0xC0 => true,
            0xB0 => msg.len() >= 2 && (msg[1] == 0 || msg[1] == 32),
            _ => false,
        }
    }

    /// MM-BUG-KILN-00076: the committed backing asset must not author the VOICE of the
    /// channel the GUI owns.
    ///
    /// `Player::advance` resets its event index to zero at every wrap, so a tick-zero
    /// Program Change or Bank Select on the UI channel is not a one-off — it is replayed
    /// every 8 bars, silently reverting whatever rig the user selected while the UI keeps
    /// showing their choice. UI rig changes are one-shot messages, so the backing wins.
    ///
    /// Derived from the ASSET, not from a list of what the generator happens to write:
    /// this parses the same `include_bytes!` blob the binary ships and rejects the whole
    /// class. Regenerating `backing.mid` from an edited `make_backing_loop.py` therefore
    /// cannot quietly reintroduce it, and neither can a hand-edited asset.
    ///
    /// Volume and pan on that channel stay legitimately backing-owned — they place the
    /// guitar in the mix; they do not choose which guitar it is.
    #[test]
    fn backing_asset_leaves_the_ui_channel_voice_alone() {
        let lp = Loop::parse(crate::BACKING, 44100.0).expect("the shipped backing parses");
        let offenders: Vec<String> = lp
            .events
            .iter()
            .filter(|e| {
                let m = &e.bytes[..e.len as usize];
                m[0] < 0xF0 && (m[0] & 0x0F) == crate::GUITAR_CH && is_voice_change(m)
            })
            .map(|e| {
                format!(
                    "frame {} bytes {:02X?}",
                    e.frame,
                    &e.bytes[..e.len as usize]
                )
            })
            .collect();
        assert!(
            offenders.is_empty(),
            "backing.mid authors {} voice-change message(s) on channel {}, which amp-lab's \
             GUI owns. Every loop wrap replays them and reverts the user's selected rig:\n  \
             {}\n\nRemove them from crates/amp-lab/tools/make_backing_loop.py and \
             regenerate the asset — `Lab::new` already initializes the channel from the \
             current Rig.",
            offenders.len(),
            crate::GUITAR_CH,
            offenders.join("\n  ")
        );
    }

    /// The same claim through the PLAYER, across two wraps (MM-BUG-KILN-00076).
    ///
    /// The census above reads the asset; this reads what actually reaches the synth, so a
    /// future `advance()` that re-emitted setup state at a boundary would be caught even
    /// with a clean asset. Two full wraps, because the defect is invisible on the first
    /// pass — it needs the index reset.
    #[test]
    fn two_wraps_never_re_send_the_ui_channel_voice() {
        let lp = Loop::parse(crate::BACKING, 44100.0).expect("the shipped backing parses");
        let mut p = Player::new();
        let mut offenders = Vec::new();
        let blocks = (lp.frames * 2).div_ceil(512) + 1;
        for _ in 0..blocks {
            p.advance(&lp, 512, |msg| {
                if msg[0] < 0xF0 && (msg[0] & 0x0F) == crate::GUITAR_CH && is_voice_change(msg) {
                    offenders.push(format!("{msg:02X?}"));
                }
            });
        }
        assert!(
            lp.frames > 0 && blocks > 2,
            "the backing loop is degenerate, so this proves nothing"
        );
        assert!(
            offenders.is_empty(),
            "over two loop wraps the player emitted {} voice-change message(s) on the \
             GUI-owned channel {}: {:?}. The user's selected program/bank would revert at \
             the wrap.",
            offenders.len(),
            crate::GUITAR_CH,
            offenders
        );
    }
}
