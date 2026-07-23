//! The audio thread: it owns the synth, the sequencer and all playback state.
//!
//! `RealtimeSynth::write_byte` buffers into a `Vec` that `render_add` drains, so
//! the synth must be owned by exactly one thread. Sharing it with the UI behind a
//! `Mutex` is the textbook way to get dropouts (a repaint holding the lock is a
//! priority inversion), so the UI only ever pushes commands into a lock-free ring
//! and this thread drains them.

use std::sync::atomic::{AtomicU32, AtomicUsize, Ordering};
use std::sync::Arc;

use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use ferrosintesis::live::{RealtimeOptions, RealtimeSynth};

use crate::ring::{Cmd, Consumer};
use crate::seq::{Loop, Player};

/// Read-only telemetry the UI polls. Atomics so neither side ever waits.
#[derive(Default)]
pub struct Meters {
    pub voices: AtomicUsize,
    /// Peak output since the last read, as a fixed-point 0..10000 of full scale.
    pub peak_x1e4: AtomicU32,
    pub xruns: AtomicUsize,
}

pub struct Engine {
    _stream: cpal::Stream,
    pub meters: Arc<Meters>,
    pub sample_rate: u32,
    pub device_name: String,
}

/// The channel carrying the guitar we are auditioning. Solo mutes everything else.
pub const GUITAR_CHANNELS: [u8; 2] = [0, 1];

pub fn start(rx: Consumer, midi: &[u8]) -> Result<Engine, String> {
    let host = cpal::default_host();
    let device = host
        .default_output_device()
        .ok_or_else(|| "no default output device".to_string())?;
    let device_name = device.name().unwrap_or_else(|_| "<unnamed>".into());
    let config = device
        .default_output_config()
        .map_err(|e| format!("no default output config: {e}"))?;
    let sample_rate = config.sample_rate().0;
    let channels = config.channels() as usize;

    let lp = Loop::parse(midi, f64::from(sample_rate))?;
    let mut synth = RealtimeSynth::new(
        RealtimeOptions::default()
            .with_sample_rate(sample_rate)
            .with_master_gain(0.8),
    );
    // Decode the embedded banks HERE, not lazily inside the callback — that is
    // what this call exists for.
    synth.prewarm_samples();

    let meters = Arc::new(Meters::default());
    let m = meters.clone();

    let mut player = Player::new();
    let mut playing = true;
    let mut solo = false;
    let mut scratch = vec![0f32; 4096 * 2];

    let err_meters = meters.clone();
    let stream = device
        .build_output_stream(
            &config.into(),
            move |out: &mut [f32], _| {
                let frames = out.len() / channels;
                out.fill(0.0);

                // 1. Drain the UI's commands.
                while let Some(c) = rx.pop() {
                    match c {
                        Cmd::Midi(b) => synth.write_byte(b),
                        Cmd::Play(p) => {
                            playing = p;
                            if !p {
                                all_notes_off(&mut synth);
                            }
                        }
                        Cmd::Solo(s) => {
                            solo = s;
                            // Muting mid-note would strand its note-off and leave
                            // the voice stuck, so silence the channels we stop
                            // feeding rather than just skipping their events.
                            all_notes_off(&mut synth);
                        }
                        Cmd::Panic => {
                            all_notes_off(&mut synth);
                            player.rewind();
                        }
                    }
                }

                // 2. Advance the loop, feeding the synth its scheduled bytes.
                if playing {
                    player.advance(&lp, frames as u64, |msg| {
                        if solo && msg[0] < 0xF0 {
                            let ch = msg[0] & 0x0F;
                            if !GUITAR_CHANNELS.contains(&ch) {
                                return;
                            }
                        }
                        for &b in msg {
                            synth.write_byte(b);
                        }
                    });
                }

                // 3. Render. `render_add` is additive and wants interleaved
                //    stereo; for a non-stereo device we render to scratch and
                //    fan out.
                if scratch.len() < frames * 2 {
                    // Should not happen after the initial size, and allocating
                    // here would be a realtime violation — count it and bail.
                    m.xruns.fetch_add(1, Ordering::Relaxed);
                    return;
                }
                let buf = &mut scratch[..frames * 2];
                buf.fill(0.0);
                if synth.render_add(frames, buf).is_err() {
                    m.xruns.fetch_add(1, Ordering::Relaxed);
                    return;
                }
                let mut peak = 0f32;
                for f in 0..frames {
                    let (l, r) = (buf[f * 2], buf[f * 2 + 1]);
                    peak = peak.max(l.abs()).max(r.abs());
                    match channels {
                        1 => out[f] = 0.5 * (l + r),
                        _ => {
                            out[f * channels] = l;
                            out[f * channels + 1] = r;
                        }
                    }
                }
                m.voices
                    .store(synth.active_voice_count(), Ordering::Relaxed);
                m.peak_x1e4
                    .store((peak.min(9.999) * 1e4) as u32, Ordering::Relaxed);
            },
            move |e| {
                eprintln!("audio stream error: {e}");
                err_meters.xruns.fetch_add(1, Ordering::Relaxed);
            },
            None,
        )
        .map_err(|e| format!("could not build output stream: {e}"))?;

    stream
        .play()
        .map_err(|e| format!("could not start stream: {e}"))?;
    Ok(Engine {
        _stream: stream,
        meters,
        sample_rate,
        device_name,
    })
}

fn all_notes_off(synth: &mut RealtimeSynth) {
    for ch in 0..16u8 {
        for cc in [123u8, 120] {
            synth.write_byte(0xB0 | ch);
            synth.write_byte(cc);
            synth.write_byte(0);
        }
    }
}
