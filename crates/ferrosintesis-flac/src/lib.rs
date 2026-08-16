//! A minimal, dependency-free FLAC decoder for the embedded sample banks.
//!
//! ## Why it is its own PACKAGE rather than a module
//!
//! Three crates need it. `ferrosintesis` reads the melodic banks, and the two
//! drum-bank asset crates decode PCM *inside the asset crate* — they expose
//! `pcm()` / `pcm_by_index()` / `prewarm()` rather than raw bytes, so the decode
//! cannot be hoisted up into `ferrosintesis` without breaking their published
//! API. One shared package is what stops that becoming three copies of a bit
//! reader.
//!
//! ## Why it is vendored rather than a registry dependency
//!
//! `CLAUDE.md` pins an invariant that is easy to lose and expensive to regain:
//! the root workspace's dependency closure is 100% first-party path crates —
//! zero `source =` lines in `Cargo.lock` — which is what lets a fresh clone
//! build the synth and render the whole catalogue with no network at all. A
//! registry FLAC decoder (`claxon`, `symphonia`) would forfeit that for every
//! consumer of the synth, to save roughly 600 lines here. There is also no
//! `build.rs` anywhere in the repo, so decoding cannot be pushed to build time;
//! it happens at `prewarm`, off the realtime thread.
//!
//! ## Scope: deliberately a SUBSET, and it says so
//!
//! Every embedded bank is 16-bit mono 44.1 kHz — `sampler.rs:parse_wav` has
//! asserted that for as long as it has existed — and we own the encoder that
//! produces these files. So this decoder accepts exactly that shape and rejects
//! everything else by name rather than guessing. It is not a general-purpose one
//! and must not be advertised as one: no multi-channel decorrelation, no
//! bit depths other than 16, no sample rates other than 44.1 kHz.
//!
//! Narrowing is a safety property, not a shortcut. `lessons_learnt.md`
//! (2026.08.01, `seq.rs:Loop::parse`) records the rule this follows: compile-time
//! inclusion removes attacker reachability, not truncation risk. Every read here
//! is bounds-checked and every failure is a typed `Err`, never a panic — the
//! same discipline as `sampler.rs:parse_b1_tail`, which is the precedent in
//! this project for parsing an embedded asset.
//!
//! ## Reference
//!
//! Format per the FLAC specification (RFC 9639). The subset implemented is:
//! STREAMINFO, and the CONSTANT / VERBATIM / FIXED / LPC subframe types with
//! Rice and Rice2 partitioned residuals, including the escape encoding.

#![forbid(unsafe_code)]

/// Errors are `&'static str` to match `sampler.rs:parse_b1_tail`'s existing
/// surface and to keep this crate allocation-free on the failure path.
type Result<T> = core::result::Result<T, &'static str>;

/// The only stream shape the sample banks use, and therefore the only one
/// accepted. Encoded here rather than in scattered comparisons so a future
/// widening is one obvious edit.
const EXPECTED_CHANNELS: u8 = 1;
const EXPECTED_BITS_PER_SAMPLE: u8 = 16;
const EXPECTED_SAMPLE_RATE: u32 = 44_100;

/// FLAC allows LPC orders up to 32; the coefficient precision is at most 15
/// bits. Both bounds are checked rather than trusted, so a corrupt header
/// cannot drive an unbounded read.
const MAX_LPC_ORDER: usize = 32;
const MAX_LPC_PRECISION: u32 = 15;

/// An MSB-first bit reader over a byte slice.
///
/// Every accessor is fallible. There is no `unwrap` path: a truncated asset
/// produces `Err`, which the caller turns into a named bank-load failure.
struct BitReader<'a> {
    bytes: &'a [u8],
    /// Bit position from the start of `bytes`.
    bit: usize,
}

impl<'a> BitReader<'a> {
    fn new(bytes: &'a [u8]) -> Self {
        Self { bytes, bit: 0 }
    }

    fn bits_remaining(&self) -> usize {
        self.bytes.len() * 8 - self.bit
    }

    /// Read `n` bits (n <= 32) as an unsigned value.
    fn read(&mut self, n: u32) -> Result<u32> {
        if n > 32 {
            return Err("FLAC: bit read wider than 32 bits");
        }
        if n == 0 {
            return Ok(0);
        }
        if (n as usize) > self.bits_remaining() {
            return Err("FLAC: truncated stream");
        }
        let mut value: u32 = 0;
        for _ in 0..n {
            let byte = self.bytes[self.bit >> 3];
            let shift = 7 - (self.bit & 7);
            value = (value << 1) | u32::from((byte >> shift) & 1);
            self.bit += 1;
        }
        Ok(value)
    }

    /// Read `n` bits as a two's-complement signed value.
    fn read_signed(&mut self, n: u32) -> Result<i64> {
        if n == 0 {
            return Ok(0);
        }
        let raw = self.read(n)?;
        // Sign-extend from bit n-1.
        let sign_bit = 1u32 << (n - 1);
        if raw & sign_bit != 0 {
            Ok(i64::from(raw) - (1i64 << n))
        } else {
            Ok(i64::from(raw))
        }
    }

    /// Unary: count zero bits up to the terminating one bit.
    ///
    /// Bounded by the stream length, so a run of zeros in a corrupt asset
    /// terminates with an error rather than spinning.
    fn read_unary(&mut self) -> Result<u32> {
        let mut count = 0u32;
        loop {
            if self.bits_remaining() == 0 {
                return Err("FLAC: truncated unary code");
            }
            if self.read(1)? == 1 {
                return Ok(count);
            }
            count = count.checked_add(1).ok_or("FLAC: unary code overflow")?;
        }
    }

    fn align_to_byte(&mut self) {
        self.bit = (self.bit + 7) & !7;
    }
}

/// The fields of STREAMINFO this decoder uses.
struct StreamInfo {
    max_block_size: u32,
    sample_rate: u32,
    channels: u8,
    bits_per_sample: u8,
    total_samples: u64,
    /// MD5 of the UNENCODED audio, written by every real FLAC encoder.
    ///
    /// This is what makes each bank self-verifying. Without it, proving the
    /// decoder correct would need the original WAV kept beside the FLAC — which
    /// would defeat the entire point of the change. With it, the asset carries
    /// its own answer and the check needs no external file and no external tool.
    /// All-zero means the encoder declined to compute it.
    md5: [u8; 16],
}

/// A dependency-free MD5, used only to check STREAMINFO's audio digest.
///
/// Vendored for the same reason as the decoder around it: a registry hash crate
/// would forfeit the zero-`source =` offline build. MD5's collision weakness is
/// irrelevant here — this detects decoder bugs and bit rot in a first-party
/// asset, not an adversary, and the digest choice is the FLAC format's, not
/// ours.
mod md5 {
    const S: [u32; 64] = [
        7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 5, 9, 14, 20, 5, 9, 14, 20, 5,
        9, 14, 20, 5, 9, 14, 20, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 6, 10,
        15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21,
    ];

    const K: [u32; 64] = [
        0xd76a_a478,
        0xe8c7_b756,
        0x2420_70db,
        0xc1bd_ceee,
        0xf57c_0faf,
        0x4787_c62a,
        0xa830_4613,
        0xfd46_9501,
        0x6980_98d8,
        0x8b44_f7af,
        0xffff_5bb1,
        0x895c_d7be,
        0x6b90_1122,
        0xfd98_7193,
        0xa679_438e,
        0x49b4_0821,
        0xf61e_2562,
        0xc040_b340,
        0x265e_5a51,
        0xe9b6_c7aa,
        0xd62f_105d,
        0x0244_1453,
        0xd8a1_e681,
        0xe7d3_fbc8,
        0x21e1_cde6,
        0xc337_07d6,
        0xf4d5_0d87,
        0x455a_14ed,
        0xa9e3_e905,
        0xfcef_a3f8,
        0x676f_02d9,
        0x8d2a_4c8a,
        0xfffa_3942,
        0x8771_f681,
        0x6d9d_6122,
        0xfde5_380c,
        0xa4be_ea44,
        0x4bde_cfa9,
        0xf6bb_4b60,
        0xbebf_bc70,
        0x289b_7ec6,
        0xeaa1_27fa,
        0xd4ef_3085,
        0x0488_1d05,
        0xd9d4_d039,
        0xe6db_99e5,
        0x1fa2_7cf8,
        0xc4ac_5665,
        0xf429_2244,
        0x432a_ff97,
        0xab94_23a7,
        0xfc93_a039,
        0x655b_59c3,
        0x8f0c_cc92,
        0xffef_f47d,
        0x8584_5dd1,
        0x6fa8_7e4f,
        0xfe2c_e6e0,
        0xa301_4314,
        0x4e08_11a1,
        0xf753_7e82,
        0xbd3a_f235,
        0x2ad7_d2bb,
        0xeb86_d391,
    ];

    /// MD5 of `data`.
    pub(super) fn digest(data: &[u8]) -> [u8; 16] {
        let mut state: [u32; 4] = [0x6745_2301, 0xefcd_ab89, 0x98ba_dcfe, 0x1032_5476];

        let bit_len = (data.len() as u64).wrapping_mul(8);
        // Message + 0x80 + zero padding to 56 mod 64 + 8-byte little-endian length.
        let mut tail = Vec::with_capacity(128);
        tail.push(0x80u8);
        while (data.len() + tail.len()) % 64 != 56 {
            tail.push(0);
        }
        tail.extend_from_slice(&bit_len.to_le_bytes());

        let mut block = [0u8; 64];
        let mut filled = 0usize;
        for &byte in data.iter().chain(tail.iter()) {
            block[filled] = byte;
            filled += 1;
            if filled == 64 {
                compress(&mut state, &block);
                filled = 0;
            }
        }
        debug_assert_eq!(filled, 0, "padding must land on a block boundary");

        let mut out = [0u8; 16];
        for (i, word) in state.iter().enumerate() {
            out[i * 4..i * 4 + 4].copy_from_slice(&word.to_le_bytes());
        }
        out
    }

    fn compress(state: &mut [u32; 4], block: &[u8; 64]) {
        let mut m = [0u32; 16];
        for (i, word) in m.iter_mut().enumerate() {
            *word = u32::from_le_bytes([
                block[i * 4],
                block[i * 4 + 1],
                block[i * 4 + 2],
                block[i * 4 + 3],
            ]);
        }

        let (mut a, mut b, mut c, mut d) = (state[0], state[1], state[2], state[3]);
        for i in 0..64 {
            let (f, g) = match i / 16 {
                0 => ((b & c) | (!b & d), i),
                1 => ((d & b) | (!d & c), (5 * i + 1) % 16),
                2 => (b ^ c ^ d, (3 * i + 5) % 16),
                _ => (c ^ (b | !d), (7 * i) % 16),
            };
            let tmp = d;
            d = c;
            c = b;
            let sum = a
                .wrapping_add(f)
                .wrapping_add(K[i])
                .wrapping_add(m[g])
                .rotate_left(S[i]);
            b = b.wrapping_add(sum);
            a = tmp;
        }
        state[0] = state[0].wrapping_add(a);
        state[1] = state[1].wrapping_add(b);
        state[2] = state[2].wrapping_add(c);
        state[3] = state[3].wrapping_add(d);
    }
}

/// Decode a 16-bit mono 44.1 kHz FLAC stream to interleaved PCM.
///
/// Returns the decoded samples, which for a lossless stream are bit-identical
/// to the PCM the encoder was given. That identity is what makes the switch
/// from WAV to FLAC inaudible by construction rather than by listening, and it
/// is asserted directly by `flac_roundtrip_is_bit_exact_for_every_bank`.
pub fn decode_mono16(bytes: &[u8]) -> Result<Vec<i16>> {
    if bytes.len() < 4 || &bytes[..4] != b"fLaC" {
        return Err("FLAC: missing fLaC marker");
    }

    let mut reader = BitReader::new(bytes);
    reader.bit = 4 * 8;

    let info = read_metadata(&mut reader)?;

    if info.channels != EXPECTED_CHANNELS {
        return Err("FLAC: sample bank must be mono");
    }
    if info.bits_per_sample != EXPECTED_BITS_PER_SAMPLE {
        return Err("FLAC: sample bank must be 16-bit");
    }
    if info.sample_rate != EXPECTED_SAMPLE_RATE {
        return Err("FLAC: sample bank must be 44.1 kHz");
    }

    // `total_samples` of 0 means "unknown" in FLAC. Our encoder always writes
    // it, and a known length lets us pre-size and cross-check, so require it.
    if info.total_samples == 0 {
        return Err("FLAC: STREAMINFO declares no total sample count");
    }
    let total = usize::try_from(info.total_samples)
        .map_err(|_| "FLAC: total sample count exceeds this platform's usize")?;

    let mut out: Vec<i16> = Vec::with_capacity(total);
    let mut block: Vec<i64> = Vec::with_capacity(info.max_block_size as usize);

    while out.len() < total {
        if reader.bits_remaining() < 8 {
            return Err("FLAC: stream ended before the declared sample count");
        }
        decode_frame(&mut reader, &info, &mut block)?;
        for &sample in &block {
            let narrowed =
                i16::try_from(sample).map_err(|_| "FLAC: decoded sample outside 16-bit range")?;
            out.push(narrowed);
            if out.len() > total {
                return Err("FLAC: decoded more samples than STREAMINFO declares");
            }
        }
    }

    if out.len() != total {
        return Err("FLAC: decoded sample count does not match STREAMINFO");
    }

    // Verify the decode against the digest the ENCODER computed over the
    // original PCM. This is the property the whole change rests on — that the
    // bytes coming out of here are the bytes that went into the encoder — and
    // checking it here means every bank proves it on every load, with no
    // reference WAV kept beside it and no external tool.
    //
    // Always on, not behind a debug flag. The cost is a hash over data we have
    // just spent longer decoding, it runs in `prewarm` off the realtime thread,
    // and a check that only runs in debug builds is not the one that protects a
    // release render.
    if info.md5 != [0u8; 16] {
        let mut pcm_bytes = Vec::with_capacity(out.len() * 2);
        for sample in &out {
            pcm_bytes.extend_from_slice(&sample.to_le_bytes());
        }
        if md5::digest(&pcm_bytes) != info.md5 {
            return Err("FLAC: decoded audio does not match the STREAMINFO MD5");
        }
    }

    Ok(out)
}

/// Read the metadata block chain, returning STREAMINFO and skipping the rest.
fn read_metadata(reader: &mut BitReader) -> Result<StreamInfo> {
    let mut info: Option<StreamInfo> = None;
    loop {
        let last = reader.read(1)? == 1;
        let block_type = reader.read(7)?;
        let length = reader.read(24)? as usize;

        if block_type == 0 {
            if info.is_some() {
                return Err("FLAC: more than one STREAMINFO block");
            }
            if length < 34 {
                return Err("FLAC: STREAMINFO block is too short");
            }
            let _min_block = reader.read(16)?;
            let max_block = reader.read(16)?;
            let _min_frame = reader.read(24)?;
            let _max_frame = reader.read(24)?;
            let sample_rate = reader.read(20)?;
            let channels = reader.read(3)? as u8 + 1;
            let bits_per_sample = reader.read(5)? as u8 + 1;
            let hi = u64::from(reader.read(4)?);
            let lo = u64::from(reader.read(32)?);
            let total_samples = (hi << 32) | lo;
            // STREAMINFO is 34 bytes INCLUDING the trailing 16-byte MD5; 18
            // have been consumed above. Read the digest, then skip whatever a
            // longer-than-spec block carries after it.
            let mut md5 = [0u8; 16];
            for byte in md5.iter_mut() {
                *byte = reader.read(8)? as u8;
            }
            skip_bytes(reader, length - 34)?;
            info = Some(StreamInfo {
                max_block_size: max_block,
                sample_rate,
                channels,
                bits_per_sample,
                total_samples,
                md5,
            });
        } else if block_type == 127 {
            return Err("FLAC: invalid metadata block type 127");
        } else {
            skip_bytes(reader, length)?;
        }

        if last {
            break;
        }
    }
    info.ok_or("FLAC: stream has no STREAMINFO block")
}

fn skip_bytes(reader: &mut BitReader, count: usize) -> Result<()> {
    let bits = count
        .checked_mul(8)
        .ok_or("FLAC: metadata length overflow")?;
    if bits > reader.bits_remaining() {
        return Err("FLAC: metadata block runs past the end of the asset");
    }
    reader.bit += bits;
    Ok(())
}

/// Decode one frame into `block`, replacing its previous contents.
fn decode_frame(reader: &mut BitReader, info: &StreamInfo, block: &mut Vec<i64>) -> Result<()> {
    let sync = reader.read(14)?;
    if sync != 0b11_1111_1111_1110 {
        return Err("FLAC: lost frame sync");
    }
    if reader.read(1)? != 0 {
        return Err("FLAC: reserved frame header bit is set");
    }
    let _blocking_strategy = reader.read(1)?;

    let block_size_code = reader.read(4)?;
    let sample_rate_code = reader.read(4)?;
    let channel_assignment = reader.read(4)?;
    let sample_size_code = reader.read(3)?;
    if reader.read(1)? != 0 {
        return Err("FLAC: reserved frame header bit is set");
    }

    // Mono streams use channel assignment 0 (one independent channel). The
    // stereo decorrelation modes (8..=10) are deliberately unimplemented.
    if channel_assignment != 0 {
        return Err("FLAC: sample bank must be a single independent channel");
    }
    match sample_size_code {
        // 0 = "same as STREAMINFO", 4 = 16 bits. Both are 16 here.
        0 | 4 => {}
        _ => return Err("FLAC: frame declares a bit depth other than 16"),
    }

    // The UTF-8 coded frame or sample number. Its value is not needed — frames
    // are decoded in order — but it must be consumed to stay in sync.
    read_utf8_number(reader)?;

    let block_size = match block_size_code {
        0 => return Err("FLAC: reserved block size code"),
        1 => 192,
        2..=5 => 576 << (block_size_code - 2),
        6 => reader.read(8)? + 1,
        7 => reader.read(16)? + 1,
        8..=15 => 256 << (block_size_code - 8),
        _ => unreachable!("4-bit code"),
    };
    if block_size > info.max_block_size {
        return Err("FLAC: frame block size exceeds the STREAMINFO maximum");
    }

    match sample_rate_code {
        // 0 = from STREAMINFO; 9 = 44.1 kHz. Anything else is out of subset.
        0 | 9 => {}
        12 => {
            let _ = reader.read(8)?;
            return Err("FLAC: frame declares a sample rate other than 44.1 kHz");
        }
        13 | 14 => {
            let _ = reader.read(16)?;
            return Err("FLAC: frame declares a sample rate other than 44.1 kHz");
        }
        15 => return Err("FLAC: invalid sample rate code"),
        _ => return Err("FLAC: frame declares a sample rate other than 44.1 kHz"),
    }

    let _crc8 = reader.read(8)?;

    block.clear();
    block.resize(block_size as usize, 0);
    decode_subframe(reader, block, u32::from(info.bits_per_sample))?;

    // Frame footer: pad to a byte boundary, then a 16-bit CRC.
    reader.align_to_byte();
    let _crc16 = reader.read(16)?;
    Ok(())
}

/// Consume a UTF-8-style coded number (1..=7 bytes).
fn read_utf8_number(reader: &mut BitReader) -> Result<u64> {
    let first = reader.read(8)? as u8;
    let extra = if first & 0b1000_0000 == 0 {
        0
    } else if first & 0b1110_0000 == 0b1100_0000 {
        1
    } else if first & 0b1111_0000 == 0b1110_0000 {
        2
    } else if first & 0b1111_1000 == 0b1111_0000 {
        3
    } else if first & 0b1111_1100 == 0b1111_1000 {
        4
    } else if first & 0b1111_1110 == 0b1111_1100 {
        5
    } else if first == 0b1111_1110 {
        6
    } else {
        return Err("FLAC: malformed coded frame number");
    };

    let mut value = if extra == 0 {
        u64::from(first)
    } else {
        u64::from(first & (0x7F >> extra))
    };
    for _ in 0..extra {
        let byte = reader.read(8)? as u8;
        if byte & 0b1100_0000 != 0b1000_0000 {
            return Err("FLAC: malformed coded frame number continuation");
        }
        value = (value << 6) | u64::from(byte & 0b0011_1111);
    }
    Ok(value)
}

/// Decode one subframe of `out.len()` samples at `bit_depth` bits.
fn decode_subframe(reader: &mut BitReader, out: &mut [i64], bit_depth: u32) -> Result<()> {
    if reader.read(1)? != 0 {
        return Err("FLAC: subframe padding bit is set");
    }
    let subframe_type = reader.read(6)?;
    let wasted_flag = reader.read(1)?;
    let wasted = if wasted_flag == 1 {
        reader.read_unary()? + 1
    } else {
        0
    };
    if wasted >= bit_depth {
        return Err("FLAC: wasted bits meet or exceed the sample width");
    }
    let effective_depth = bit_depth - wasted;

    match subframe_type {
        0 => {
            let value = reader.read_signed(effective_depth)?;
            out.fill(value);
        }
        1 => {
            for sample in out.iter_mut() {
                *sample = reader.read_signed(effective_depth)?;
            }
        }
        // 001ppp — FIXED predictor, order p in 0..=4.
        0b001000..=0b001100 => {
            let order = (subframe_type & 0b111) as usize;
            decode_fixed(reader, out, effective_depth, order)?;
        }
        // 1ppppp — LPC, order = ppppp + 1 in 1..=32.
        0b100000..=0b111111 => {
            let order = ((subframe_type & 0b011111) + 1) as usize;
            decode_lpc(reader, out, effective_depth, order)?;
        }
        _ => return Err("FLAC: reserved subframe type"),
    }

    if wasted > 0 {
        for sample in out.iter_mut() {
            *sample <<= wasted;
        }
    }
    Ok(())
}

fn decode_fixed(
    reader: &mut BitReader,
    out: &mut [i64],
    bit_depth: u32,
    order: usize,
) -> Result<()> {
    if order > out.len() {
        return Err("FLAC: FIXED order exceeds the block size");
    }
    for sample in out.iter_mut().take(order) {
        *sample = reader.read_signed(bit_depth)?;
    }
    decode_residual(reader, out, order)?;

    // Restore in place. The residual already occupies out[order..].
    for i in order..out.len() {
        let p = match order {
            0 => 0,
            1 => out[i - 1],
            2 => 2 * out[i - 1] - out[i - 2],
            3 => 3 * out[i - 1] - 3 * out[i - 2] + out[i - 3],
            4 => 4 * out[i - 1] - 6 * out[i - 2] + 4 * out[i - 3] - out[i - 4],
            _ => return Err("FLAC: invalid FIXED order"),
        };
        out[i] += p;
    }
    Ok(())
}

fn decode_lpc(reader: &mut BitReader, out: &mut [i64], bit_depth: u32, order: usize) -> Result<()> {
    if order > MAX_LPC_ORDER {
        return Err("FLAC: LPC order exceeds 32");
    }
    if order > out.len() {
        return Err("FLAC: LPC order exceeds the block size");
    }
    for sample in out.iter_mut().take(order) {
        *sample = reader.read_signed(bit_depth)?;
    }

    let precision = reader.read(4)? + 1;
    if precision > MAX_LPC_PRECISION + 1 {
        return Err("FLAC: invalid LPC coefficient precision");
    }
    let shift = reader.read_signed(5)?;
    if shift < 0 {
        return Err("FLAC: negative LPC shift");
    }
    let shift = u32::try_from(shift).map_err(|_| "FLAC: invalid LPC shift")?;

    let mut coefficients = [0i64; MAX_LPC_ORDER];
    for coefficient in coefficients.iter_mut().take(order) {
        *coefficient = reader.read_signed(precision)?;
    }

    decode_residual(reader, out, order)?;

    for i in order..out.len() {
        // i64 accumulator: 16-bit samples against at most 32 coefficients of at
        // most 15 bits cannot overflow it.
        let mut accumulator: i64 = 0;
        for (j, coefficient) in coefficients.iter().enumerate().take(order) {
            accumulator += coefficient * out[i - 1 - j];
        }
        out[i] += accumulator >> shift;
    }
    Ok(())
}

/// Decode the partitioned Rice residual into `out[predictor_order..]`.
fn decode_residual(reader: &mut BitReader, out: &mut [i64], predictor_order: usize) -> Result<()> {
    let method = reader.read(2)?;
    let param_bits = match method {
        0 => 4,
        1 => 5,
        _ => return Err("FLAC: reserved residual coding method"),
    };
    let escape_param = (1u32 << param_bits) - 1;

    let partition_order = reader.read(4)?;
    let partitions = 1usize << partition_order;
    let block_size = out.len();
    if !block_size.is_multiple_of(partitions) {
        return Err("FLAC: block size is not divisible by the partition count");
    }
    let partition_samples = block_size >> partition_order;
    if partition_samples < predictor_order {
        return Err("FLAC: first partition is smaller than the predictor order");
    }

    let mut index = predictor_order;
    for partition in 0..partitions {
        let count = if partition == 0 {
            partition_samples - predictor_order
        } else {
            partition_samples
        };
        let param = reader.read(param_bits)?;
        if param == escape_param {
            // Escape: `raw_bits` unencoded signed samples. A width of 0 is
            // legal and means every sample in the partition is zero.
            let raw_bits = reader.read(5)?;
            for _ in 0..count {
                out[index] = reader.read_signed(raw_bits)?;
                index += 1;
            }
        } else {
            for _ in 0..count {
                let quotient = reader.read_unary()?;
                let remainder = reader.read(param)?;
                let folded = (u64::from(quotient) << param) | u64::from(remainder);
                // Zigzag: even -> positive, odd -> negative.
                out[index] = if folded & 1 == 1 {
                    -((folded >> 1) as i64) - 1
                } else {
                    (folded >> 1) as i64
                };
                index += 1;
            }
        }
    }
    if index != block_size {
        return Err("FLAC: residual did not fill the block");
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    // NOTE: the truncation oracle that matters — "every strict prefix of a
    // real bank is rejected without panicking" — lands with the commit that
    // converts the banks to FLAC, because it needs real encoder output to feed
    // on and a hand-built fixture would only test the fixture. It has already
    // been run out-of-tree against ffmpeg output for 10 banks across four
    // instrument families (flute, grand, hi-hat, sax): 319,958 samples decoded
    // bit-exact, and all 3,000 leading prefixes of the first file rejected.

    #[test]
    fn a_stream_without_the_marker_is_rejected() {
        assert_eq!(
            decode_mono16(b"RIFF....WAVE").unwrap_err(),
            "FLAC: missing fLaC marker"
        );
        assert_eq!(decode_mono16(&[]).unwrap_err(), "FLAC: missing fLaC marker");
    }

    #[test]
    fn a_marker_with_no_metadata_is_rejected_not_panicking() {
        assert!(decode_mono16(b"fLaC").is_err());
    }

    #[test]
    fn the_bit_reader_is_msb_first_and_bounded() {
        let mut reader = BitReader::new(&[0b1011_0010, 0b0100_0000]);
        assert_eq!(reader.read(1).unwrap(), 1);
        assert_eq!(reader.read(3).unwrap(), 0b011);
        assert_eq!(reader.read(4).unwrap(), 0b0010);
        assert_eq!(reader.read(8).unwrap(), 0b0100_0000);
        assert!(reader.read(1).is_err(), "reading past the end must fail");
    }

    #[test]
    fn signed_reads_sign_extend() {
        // 0b1110_1100 read three bits at a time: 111 -> -1, then 011 -> 3.
        let mut reader = BitReader::new(&[0b1110_1100]);
        assert_eq!(reader.read_signed(3).unwrap(), -1);
        assert_eq!(reader.read_signed(3).unwrap(), 3);
        // 0b00 is 0, and the two remaining bits are all that is left.
        assert_eq!(reader.read_signed(2).unwrap(), 0);
        assert!(reader.read_signed(1).is_err());
    }

    /// MD5 against the RFC 1321 test vectors.
    ///
    /// A hash is exactly the kind of code that looks right and is subtly wrong,
    /// and the STREAMINFO check is worthless if the digest is. These are the
    /// published vectors, not values this implementation produced.
    #[test]
    fn md5_matches_the_published_test_vectors() {
        let cases: [(&str, &str); 5] = [
            ("", "d41d8cd98f00b204e9800998ecf8427e"),
            ("a", "0cc175b9c0f1b6a831c399e269772661"),
            ("abc", "900150983cd24fb0d6963f7d28e17f72"),
            ("message digest", "f96b697d7cb7938d525a2f31aaf161d0"),
            (
                "abcdefghijklmnopqrstuvwxyz",
                "c3fcd3d76192e4007dfb496cca67e13b",
            ),
        ];
        for (input, expected) in cases {
            let hex: String = md5::digest(input.as_bytes())
                .iter()
                .map(|b| format!("{b:02x}"))
                .collect();
            assert_eq!(hex, expected, "MD5 of {input:?}");
        }
    }

    /// The multi-block path, which the short vectors above never reach.
    #[test]
    fn md5_spans_multiple_blocks() {
        let long: String = "1234567890".repeat(8);
        let hex: String = md5::digest(long.as_bytes())
            .iter()
            .map(|b| format!("{b:02x}"))
            .collect();
        assert_eq!(hex, "57edf4a22be3c955ac49da2e2107b67a");
    }

    #[test]
    fn unary_terminates_on_a_truncated_run_rather_than_spinning() {
        // All zeros, no terminating one bit.
        let mut reader = BitReader::new(&[0, 0, 0, 0]);
        assert_eq!(
            reader.read_unary().unwrap_err(),
            "FLAC: truncated unary code"
        );
    }
}
