//! calmeter — DEV-ONLY. Per-note level extraction for the instrument-balance
//! calibration (SPEC_v2 §3).
//!
//!     cargo run --release -p ferrosintesis-cli --example calmeter -- \
//!         <in.wav> <plan.tsv> <engine> [--latency-frames N] > levels.tsv
//!
//! `engine` is one of `ferro` | `sc55` | `syxg50` and selects the event-dispatch
//! quantization that engine applies to a note-on.
//!
//! ## The level statistic: MAXIMUM momentary block
//!
//! `S(window) = max over BS.1770 momentary blocks wholly contained in the window`.
//!
//! Three things about this are easy to get wrong and expensive to debug:
//!
//! 1. It is **not** a percentile. Over the ~9 blocks a 1.2 s window contains,
//!    linear-interpolated p95 evaluates at index 7.6 and blends the top two blocks,
//!    costing up to 3.14 dB on a fast-decay note. Nearest-rank p95 happens to equal
//!    the max at n <= 19, so the two conventions are not approximations of each other
//!    here — they are different statistics that coincide only by rank arithmetic.
//! 2. **Do not reuse `voices.rs::percentile`.** Its doc comment says "nearest-rank"
//!    but its body is `sorted[floor(q * (len - 1))]`, which at n = 9 returns the
//!    SECOND-largest block. Measured through the full derivation that convention puts
//!    median 0.41 / max 18.77 dB of error into the trim table.
//! 3. Max is right *because the window is a single isolated note*. The usual
//!    objection to a maximum ("one hot moment sets it") is an argument about whole
//!    tracks and does not apply.
//!
//! ## Window placement
//!
//! Each engine dispatches a note-on quantized to its own block size, so the audible
//! onset sits up to one block EARLY relative to the nominal MIDI tick. That offset is
//! exactly known — no onset detection is needed (and onset detection actively
//! misfires here: attack shape is precisely what legitimately differs between engines,
//! so a threshold crossing disagrees by ~96 ms on an ordinary sustained program).
//!
//! ## Filter pre-roll
//!
//! `momentary_lufs` builds its K-weighting biquads with zero state, so metering a bare
//! slice gives the 38 Hz RLB high-pass a startup transient — worst for bass-heavy
//! programs, i.e. program-dependent and NOT cancelling in the differential. We meter a
//! slice that starts `PREROLL_S` early and discard the blocks that overlap it.

use ferrosintesis::offline::momentary_lufs;

/// Analysis window per note (SPEC_v2 §3.2).
const WINDOW_S: f64 = 1.2;
/// Extra audio metered before the window purely to warm the K-weighting filters.
const PREROLL_S: f64 = 0.4;
/// A note quieter than this never sounded on this engine.
const SILENCE_LUFS: f32 = -60.0;

/// Event-dispatch quantization, in frames, per engine.
fn chunk_frames(engine: &str) -> Result<u64, String> {
    match engine {
        // mdmidiemu's non-timed path advances the emulation in 512-frame chunks.
        "sc55" | "mu80" | "mu50" => Ok(512),
        // The S-YXG50 host dispatches with a per-event frame offset.
        "syxg50" => Ok(1),
        // ferrosintesis quantizes note starts to its internal BLOCK.
        "ferro" => Ok(64),
        other => Err(format!("unknown engine {other:?}")),
    }
}

struct Wav {
    samples: Vec<f32>, // interleaved stereo
    sr: u32,
}

/// Minimal 16-bit PCM reader — `wav.rs` in the library is write-only.
fn read_wav(path: &str) -> Result<Wav, String> {
    let b = std::fs::read(path).map_err(|e| format!("{path}: {e}"))?;
    if b.len() < 12 || &b[0..4] != b"RIFF" || &b[8..12] != b"WAVE" {
        return Err(format!("{path}: not a RIFF/WAVE file"));
    }
    let (mut pos, mut sr, mut channels, mut bits) = (12usize, 0u32, 0u16, 0u16);
    let mut data: &[u8] = &[];
    while pos + 8 <= b.len() {
        let id = &b[pos..pos + 4];
        let sz = u32::from_le_bytes([b[pos + 4], b[pos + 5], b[pos + 6], b[pos + 7]]) as usize;
        let body = pos + 8;
        if id == b"fmt " && body + 16 <= b.len() {
            channels = u16::from_le_bytes([b[body + 2], b[body + 3]]);
            sr = u32::from_le_bytes([b[body + 4], b[body + 5], b[body + 6], b[body + 7]]);
            bits = u16::from_le_bytes([b[body + 14], b[body + 15]]);
        } else if id == b"data" {
            data = &b[body..(body + sz).min(b.len())];
        }
        pos = body + sz + (sz & 1); // chunks are word-aligned
    }
    if bits != 16 || channels == 0 {
        return Err(format!(
            "{path}: need 16-bit PCM, got {bits}-bit x{channels}"
        ));
    }
    let frames = data.len() / (2 * channels as usize);
    let mut samples = Vec::with_capacity(frames * 2);
    for f in 0..frames {
        let at = |c: usize| {
            let o = (f * channels as usize + c) * 2;
            i16::from_le_bytes([data[o], data[o + 1]]) as f32 / 32768.0
        };
        let l = at(0);
        let r = if channels > 1 { at(1) } else { l };
        samples.push(l);
        samples.push(r);
    }
    Ok(Wav { samples, sr })
}

/// The valid momentary blocks in **onset-relative** order: index 0 is the first block
/// at/after the true onset (absolute index `first_valid` into `m` — earlier blocks are
/// K-weighting filter warm-up and are discarded), through `last_valid` (the last block
/// whose 400 ms body is wholly inside the window). Returned as a plain series so the
/// caller can both take the max (level) and compare the trajectory across engines (the
/// M-CAL v2 shape guard). Pure — unit-tested below.
fn onset_blocks(m: &[f32], first_valid: usize, last_valid: i64) -> Vec<f32> {
    if last_valid < first_valid as i64 || first_valid >= m.len() {
        return Vec::new();
    }
    let last = (last_valid as usize).min(m.len() - 1);
    m[first_valid..=last].to_vec()
}

/// The onset-relative momentary-block trajectory over the window, plus the count of
/// clipped samples inside it. The caller derives max_m / peak_block / sounded from the
/// trajectory; emitting the whole series (not just the max) is what lets the derive step
/// compare peak-normalised envelopes between engines.
fn measure(w: &Wav, start: i64, window_frames: i64, preroll_frames: i64) -> (Vec<f32>, u32) {
    let n = (w.samples.len() / 2) as i64;
    let slice_start = (start - preroll_frames).max(0);
    let slice_end = (start + window_frames).min(n);
    if slice_end <= slice_start {
        return (Vec::new(), 0);
    }
    let lo = (slice_start * 2) as usize;
    let hi = (slice_end * 2) as usize;
    let slice = &w.samples[lo..hi];

    let clipped = slice
        .iter()
        .filter(|v| v.abs() >= 32700.0 / 32768.0)
        .count() as u32;

    let m = momentary_lufs(slice, w.sr as f32);
    // Block j covers [j*hop, j*hop + 400ms) inside the slice. Keep only blocks that
    // start at or after the true window origin — everything earlier is filter warm-up.
    let hop = 0.100 * w.sr as f64;
    let actual_preroll = (start - slice_start) as f64;
    let first_valid = (actual_preroll / hop).ceil() as usize;
    // ...and only blocks whose 400 ms body is wholly inside the window.
    let block = 0.400 * w.sr as f64;
    let last_valid = (((actual_preroll + window_frames as f64) - block) / hop).floor() as i64;

    (onset_blocks(&m, first_valid, last_valid), clipped)
}

#[cfg(test)]
mod tests {
    use super::onset_blocks;

    #[test]
    fn onset_blocks_drops_warmup_and_tail() {
        // m indices 0..6; first_valid=2 drops the two warm-up blocks, last_valid=4
        // drops block 5,6 (400 ms body would spill past the window).
        let m = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0];
        assert_eq!(onset_blocks(&m, 2, 4), vec![12.0, 13.0, 14.0]);
    }

    #[test]
    fn onset_blocks_clamps_last_to_len() {
        let m = [1.0, 2.0, 3.0];
        // last_valid past the end -> clamp to the final block.
        assert_eq!(onset_blocks(&m, 1, 99), vec![2.0, 3.0]);
    }

    #[test]
    fn onset_blocks_empty_when_inverted_or_out_of_range() {
        let m = [1.0, 2.0, 3.0];
        assert!(onset_blocks(&m, 2, 1).is_empty()); // last < first
        assert!(onset_blocks(&m, 5, 9).is_empty()); // first past the end
        assert!(onset_blocks(&[], 0, 0).is_empty());
    }
}

fn main() -> Result<(), String> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 4 {
        return Err(
            "usage: calmeter <in.wav> <plan.tsv> <ferro|sc55|syxg50> [--latency-frames N]".into(),
        );
    }
    let (wav_path, plan_path, engine) = (&args[1], &args[2], args[3].as_str());
    let chunk = chunk_frames(engine)?;
    let latency: i64 = args
        .iter()
        .position(|a| a == "--latency-frames")
        .and_then(|i| args.get(i + 1))
        .map(|v| v.parse().unwrap_or(0))
        .unwrap_or(0);

    let w = read_wav(wav_path)?;
    let window_frames = (WINDOW_S * w.sr as f64).round() as i64;
    let preroll_frames = (PREROLL_S * w.sr as f64).round() as i64;

    // Fixed onset-relative block count for the (unclamped) window geometry — every
    // non-truncated probe note yields exactly this many blocks, so `b0..b{n-1}` is a
    // stable schema. A block below the meter floor prints as -120.000 (sentinel).
    let hopf = 0.100 * w.sr as f64;
    let blockf = 0.400 * w.sr as f64;
    let fv = (preroll_frames as f64 / hopf).ceil() as i64;
    let lv = ((preroll_frames as f64 + window_frames as f64 - blockf) / hopf).floor() as i64;
    let nblocks = (lv - fv + 1).max(0) as usize;
    let fmt = |v: f32| {
        if v.is_finite() {
            format!("{v:.3}")
        } else {
            "-120.000".to_string()
        }
    };

    let plan = std::fs::read_to_string(plan_path).map_err(|e| format!("{plan_path}: {e}"))?;
    let mut header =
        String::from("idx\tprogram\tkey\tvelocity\tmax_m\tpeak_block\tclipped\tsounded");
    for j in 0..nblocks {
        header.push_str(&format!("\tb{j}"));
    }
    println!("{header}");
    for line in plan.lines().skip(1) {
        let f: Vec<&str> = line.split('\t').collect();
        if f.len() < 6 {
            continue;
        }
        let (idx, onset_frames, program, key, vel) = (f[0], f[2], f[3], f[4], f[5]);
        let onset: u64 = onset_frames.parse().map_err(|_| "bad onset_frames")?;
        // The engine dispatched this note at the last chunk boundary at or before the
        // nominal onset, then the module took `latency` frames to make sound.
        let start = (onset - onset % chunk) as i64 + latency;
        let (blocks, clipped) = measure(&w, start, window_frames, preroll_frames);
        let max_m = blocks.iter().copied().fold(f32::NEG_INFINITY, f32::max);
        let peak_block = blocks
            .iter()
            .enumerate()
            .filter(|(_, b)| b.is_finite())
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap())
            .map(|(i, _)| i as i32)
            .unwrap_or(-1);
        let sounded = max_m > SILENCE_LUFS;
        let mut row = format!(
            "{idx}\t{program}\t{key}\t{vel}\t{}\t{peak_block}\t{clipped}\t{}",
            fmt(max_m),
            if sounded { 1 } else { 0 }
        );
        for j in 0..nblocks {
            row.push('\t');
            row.push_str(&fmt(blocks.get(j).copied().unwrap_or(f32::NEG_INFINITY)));
        }
        println!("{row}");
    }
    Ok(())
}
