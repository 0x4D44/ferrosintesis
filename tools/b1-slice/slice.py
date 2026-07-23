"""Slice Arthur's Yamaha B1 ladder takes into per-note archival WAVs.

Arthur recorded his own upright with a Tascam DR-05: one take per dynamic
("soft" / "normal" / "hard"), each playing single notes ascending in thirds and
holding every note to full ring-out. This tool cuts those takes into one file
per struck note, identifies each note's pitch from its INHARMONIC partial
series, checks the detected sequence against the expected ladder, and writes a
manifest that `prepare.py` (the sample-bank baker) consumes.

Everything here is ARCHIVAL: a slice is the original 24-bit samples of channel
L, byte for byte. No resampling, no normalisation, no filtering, no dither —
all of that is downstream DSP and belongs in `prepare.py`. The only decisions
this tool makes are WHERE a note starts and WHAT note it is.

Four facts about the source material shape the whole design:

  * The recordings are 24-bit stereo. Python's `wave` reports
    `getsampwidth() == 3` and hands back raw bytes; reading those as 16-bit
    yields plausible-looking noise, so the decode here is explicit and is
    pinned by a test against a synthesised known-value fixture.
  * Take CHANNEL L ONLY. Summing L+R costs a ~3 dB shelf above 1.6 kHz plus
    1.6-4 kHz comb notches (measured); L alone costs 0.1-0.3 dB.
  * The passes differ by ~21-28 dB and note spacing runs from ~16 s in the bass
    to ~4 s in the treble, so onsets are found by ATTACK STEEPNESS (dB rise per
    ~20 ms in a 300 Hz-3 kHz band), never by an absolute level threshold. A
    hammer strike is steep; a sympathetic swell is not.
  * The instrument has a real Railsback stretch (A0 ~-50 c, C8 ~+40 c) on top
    of a ~10 c flat A4, and a bass/treble bridge break at F3/F#3. So pitch is
    fitted as f_k = k*f0*sqrt(1 + B*k^2), never by autocorrelation/YIN/zero
    crossings — all of which octave-error here, because the bass fundamental is
    weak and the top octave has only one detectable partial.

Pure stdlib; run from anywhere:
    python tools/b1-slice/slice.py --take=DR0000_0195.wav --out=D:/tmp_b1/slices
    python tools/b1-slice/slice.py --all --src=C:/Users/marti/Downloads --out=...
"""

import bisect
import hashlib
import json
import math
import os
import shutil
import struct
import subprocess
import sys
from array import array

TOOL_VERSION = "1.0"
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(TOOL_DIR, os.pardir, os.pardir))

# ---------------------------------------------------------------------------
# The ladders Arthur played.
#
# Both chains ascend in thirds and both START ON A0 (not C1). The soft pass
# follows the same chain only as far as B3 and then switches to the OTHER
# thirds chain from C4 up, so genuine 3-layer coverage exists only A0-B3.
# ---------------------------------------------------------------------------
LADDERS = {
    "thirds_a0": (
        "A0 C1 E1 G1 B1 D2 F2 A2 C3 E3 G3 B3 D4 F4 A4 C5 E5 G5 B5 "
        "D6 F6 A6 C7 E7 G7 B7 C8"
    ).split(),
    "thirds_a0_soft": (
        "A0 C1 E1 G1 B1 D2 F2 A2 C3 E3 G3 B3 C4 E4 G4 B4 D5 F5 A5 "
        "C6 E6 G6 B6 D7 F7 A7 C8"
    ).split(),
}

# Arthur's three usable takes and where each pass sits inside them. The
# windows are DELIBERATELY GENEROUS: extra events inside a window are reported
# as extras by the ladder matcher, which is safer than clipping a window so
# tight that a real note falls outside it. (An earlier analysis pass put
# 0195's normal pass at 1.6-166.7 s and its soft pass at 234-441 s; both are
# short — the normal pass runs to ~226 s and the soft pass to ~498 s. The
# windows below are what the attack detector actually finds.)
#
# `gain_group` records which takes share a recorder gain setting, because the
# inter-layer dB offsets are only physically meaningful within a group: 0195
# and 0197 were recorded at identical gain, 0200 at a deliberately lower one.
TAKES = {
    "DR0000_0195.wav": {
        "gain_group": "A",
        "note": "pass 'normal' then pass 'soft'; zero clipped samples",
        "passes": [
            ("normal", 0.0, 230.0, "thirds_a0"),
            ("soft", 230.0, 503.0, "thirds_a0_soft"),
        ],
    },
    "DR0000_0197.wav": {
        "gain_group": "A",
        "note": "pass 'hard', OLD take — CLIPPED (3558 rail samples); superseded by 0200",
        "passes": [("hard", 0.0, 258.0, "thirds_a0")],
    },
    "DR0000_0200.wav": {
        "gain_group": "B",
        "note": "pass 'hard', NEW take at reduced input gain; zero clipped samples",
        "passes": [("hard", 0.0, 303.0, "thirds_a0")],
    },
}

# ---------------------------------------------------------------------------
# Onset detection.
#
# The onset function lives in a 300 Hz-3 kHz band. That is not arbitrary: the
# recordings carry strong 2-5 Hz infrasonic rumble (median -57 dBFS) below it,
# and above ~4 kHz the soft pass has NO usable content at all (measured 4-8 kHz
# SNR: -1.1 dB), so a conventional high-frequency onset detector reads pure
# recorder noise and misses two thirds of the notes. The band is reached by a
# boxcar-8 decimation to 6 kHz (its first null at 6 kHz does the anti-alias
# work; the residual fold-down is transient-correlated, so it helps rather than
# hurts an onset detector) followed by a 2nd-order Butterworth highpass.
# ---------------------------------------------------------------------------
DECIM = 8               # 48 kHz -> 6 kHz
ONSET_HP_HZ = 300.0
ONSET_HOP = 16          # 2.67 ms at 6 kHz
ONSET_WIN = 32          # 5.3 ms
ONSET_LAG = 8           # flux look-back, ~21 ms
ONSET_FLUX_DB = 8.0     # dB rise over the look-back that counts as an attack
ONSET_GATE_DB = 10.0    # frame must sit this far above the take's noise floor
ONSET_REFRACTORY_S = 0.30
# A struck note raises the level DURABLY. Partials beating against each other
# inside a held note raise it for one beat period and fall back, and in the
# bass those beats are only ~30 ms apart — comfortably fast enough to look like
# an attack to a 21 ms flux window. Requiring the rise to still be there 80 ms
# later is what separates a hammer from a beat.
ONSET_RISE_DB = 6.0
ONSET_RISE_POST_S = 0.080
ONSET_RISE_PRE_S = (0.160, 0.040)
# A quiet transient within SHADOW_S of a much louder one is key/action noise,
# not a struck note (slow soft key presses make a clear mechanical thump ~0.4-
# 0.9 s before the hammer throws). Genuine repeats in these takes are at most
# ~8 dB apart, so the level difference separates them cleanly.
SHADOW_S = 2.0
SHADOW_DB = 8.0
# Backstop for transients that survive the shadow test but are far quieter
# than the playing around them. The reference is the 75th percentile of events
# within LEVEL_LOCAL_S, NOT of the whole take: 0195 holds the normal pass and
# the soft pass in one file, ~25 dB apart, and a whole-file reference either
# lets the normal pass's junk through or eats the soft pass's real notes.
LEVEL_GATE_DB = 24.0
LEVEL_LOCAL_S = 60.0

# ---------------------------------------------------------------------------
# Pitch: inharmonic partial fit  f_k = k*f0*sqrt(1 + B*k^2).
#
# Analysed at several window lengths because no single one works across the
# instrument. Long windows resolve the bass partial spacing (A0's partials are
# 27 Hz apart) but split treble unisons into beating triplets and, up top,
# contain more ring-out than note. Short windows merge the unisons and catch
# the fast treble decay but cannot resolve the bass. The 0.15 s skip variants
# exist because a hard strike's broadband KNOCK (a 900-1250 Hz soundboard
# thump) can exceed the string partial itself in the top octave; the knock is
# gone by 150 ms while the string is still ringing.
# ---------------------------------------------------------------------------
SCALES = ((4096, 0.15), (16384, 0.03), (16384, 0.15), (32768, 0.06))
F0_LO, F0_HI = 24.0, 4800.0     # A0 stretched flat .. C8 stretched sharp
FMIN, FMAX = 20.0, 19000.0      # spectral analysis band
MAXPART = 48                    # most partials any hypothesis may claim
COVER_PARTIALS = 12             # coverage is judged over the first N partials
STRONG_DB = 22.0                # a peak this close to the in-band max is "strong"
PEAK_REL_DB = -60.0
PEAK_TOP = 160
PEAK_MERGE = 0.004              # fractional spacing below which peaks are one
ANCHORS = 4                     # strongest peaks used to seed f0 candidates
KMAX = 20                       # anchor may be partial 1..KMAX
B_SEEDS = (0.0, 1e-4, 4e-4, 1.5e-3, 6e-3, 2.5e-2)
RESIDUAL_SCALE = 0.004          # partial-position error that halves the score

# ---------------------------------------------------------------------------
# Slice geometry.
# ---------------------------------------------------------------------------
PRE_ROLL_S = 0.005      # kept before the attack; the detector backtracks to
                        # the foot of the rise, so this lands in true silence
SLICE_S = 8.0
NEXT_GUARD_S = 0.15     # never run into the following attack

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


# ===========================================================================
# note names
# ===========================================================================

def note_to_midi(name):
    """'A0' -> 21, 'F#3' -> 54. Raises ValueError on anything else."""
    s = name.strip()
    if not s:
        raise ValueError("empty note name")
    letter = s[0].upper()
    i = 1
    if i < len(s) and s[i] in "#b":
        letter += "#" if s[i] == "#" else "b"
        i += 1
    octave = s[i:]
    if letter.endswith("b"):        # respell flats as sharps
        base = NOTE_NAMES.index(letter[0])
        letter = NOTE_NAMES[(base - 1) % 12]
    if letter not in NOTE_NAMES:
        raise ValueError(f"bad note name {name!r}")
    try:
        octv = int(octave)
    except ValueError:
        raise ValueError(f"bad note name {name!r}") from None
    return (octv + 1) * 12 + NOTE_NAMES.index(letter)


def midi_to_note(midi):
    m = int(round(midi))
    return f"{NOTE_NAMES[m % 12]}{m // 12 - 1}"


def et_hz(midi):
    """Equal-tempered frequency, A4 = 440 Hz (the reference the tuning survey
    used; this piano reads ~-10 cents at A4 plus its Railsback stretch)."""
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def hz_to_midi(hz):
    return 69.0 + 12.0 * math.log2(hz / 440.0)


def cents_vs(hz, midi):
    return 1200.0 * math.log2(hz / et_hz(midi))


# ===========================================================================
# RIFF / WAV
# ===========================================================================

class WavInfo:
    """Geometry of a PCM WAV, found by walking the chunk list.

    The DR-05 writes a 636-byte `bext` chunk before `data`, so the payload does
    NOT start at the canonical offset 44 — the walk is load-bearing, not
    defensive tidiness.
    """

    def __init__(self, path, channels, sample_rate, bits, block_align,
                 data_offset, data_size):
        self.path = path
        self.channels = channels
        self.sample_rate = sample_rate
        self.bits = bits
        self.block_align = block_align
        self.data_offset = data_offset
        self.data_size = data_size
        self.frames = data_size // block_align if block_align else 0

    @property
    def duration_s(self):
        return self.frames / float(self.sample_rate)


def read_wav_info(path):
    """Parse a RIFF/WAVE header. Accepts PCM and WAVE_FORMAT_EXTENSIBLE."""
    with open(path, "rb") as f:
        head = f.read(12)
        if len(head) < 12 or head[:4] != b"RIFF" or head[8:12] != b"WAVE":
            raise ValueError(f"{path}: not a RIFF/WAVE file")
        fmt = None
        data = None
        while True:
            hdr = f.read(8)
            if len(hdr) < 8:
                break
            cid = hdr[:4]
            size = struct.unpack("<I", hdr[4:8])[0]
            pos = f.tell()
            if cid == b"fmt ":
                fmt = f.read(min(size, 40))
            elif cid == b"data":
                data = (pos, size)
            f.seek(pos + size + (size & 1))
    if fmt is None or data is None:
        raise ValueError(f"{path}: missing fmt/data chunk")
    tag, channels, rate, _bps, block_align, bits = struct.unpack("<HHIIHH", fmt[:16])
    if tag == 0xFFFE and len(fmt) >= 40:        # WAVE_FORMAT_EXTENSIBLE
        tag = struct.unpack("<H", fmt[24:26])[0]
    if tag != 1:
        raise ValueError(f"{path}: unsupported format tag {tag} (want PCM)")
    off, size = data
    size = min(size, os.path.getsize(path) - off)
    return WavInfo(path, channels, rate, bits, block_align, off, size)


def read_frames(info, start_frame, n_frames):
    """Raw interleaved bytes for `n_frames` frames starting at `start_frame`."""
    start_frame = max(0, min(start_frame, info.frames))
    n_frames = max(0, min(n_frames, info.frames - start_frame))
    with open(info.path, "rb") as f:
        f.seek(info.data_offset + start_frame * info.block_align)
        return f.read(n_frames * info.block_align)


def channel_bytes(raw, info, channel):
    """Deinterleave ONE channel, keeping the sample bytes untouched.

    Slice assignment on a bytearray is a C-level strided copy, so this is both
    fast and exactly lossless — the emitted slice is the recorder's own bits.
    """
    w = info.bits // 8
    stride = info.block_align
    base = channel * w
    n = len(raw) // stride
    out = bytearray(n * w)
    src = raw[:n * stride]
    for k in range(w):
        out[k::w] = src[base + k::stride]
    return bytes(out)


def decode_pcm(buf, bits):
    """Mono PCM bytes -> array('f') of floats in [-1, 1).

    24-bit is assembled as the TOP three bytes of a 32-bit little-endian word,
    so the sign bit lands where the machine expects it and sign extension is
    free; the resulting integers are 256x the sample value.
    """
    if bits == 24:
        n = len(buf) // 3
        wide = bytearray(4 * n)
        wide[1::4] = buf[0:3 * n:3]
        wide[2::4] = buf[1:3 * n:3]
        wide[3::4] = buf[2:3 * n:3]
        ints = array("i")
        ints.frombytes(bytes(wide))
        if sys.byteorder != "little":
            ints.byteswap()
        scale = 1.0 / (1 << 31)
    elif bits == 16:
        n = len(buf) // 2
        ints = array("h")
        ints.frombytes(buf[:2 * n])
        if sys.byteorder != "little":
            ints.byteswap()
        scale = 1.0 / (1 << 15)
    else:
        raise ValueError(f"unsupported sample width {bits} bits")
    out = array("f")
    step = 1 << 20
    for i in range(0, len(ints), step):
        out.extend(array("f", [v * scale for v in ints[i:i + step]]))
    return out


def load_channel(info, channel=0):
    """Whole file, one channel, as floats. Raw bytes are re-read per slice."""
    raw = read_frames(info, 0, info.frames)
    return decode_pcm(channel_bytes(raw, info, channel), info.bits)


def write_wav_mono(path, pcm, bits, sample_rate):
    """Write mono PCM bytes as a minimal canonical WAV (no bext, no LIST)."""
    byte_rate = sample_rate * bits // 8
    align = bits // 8
    fmt = struct.pack("<4sIHHIIHH", b"fmt ", 16, 1, 1, sample_rate,
                      byte_rate, align, bits)
    pad = len(pcm) & 1
    riff = 4 + len(fmt) + 8 + len(pcm) + pad
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sI4s", b"RIFF", riff, b"WAVE"))
        f.write(fmt)
        f.write(struct.pack("<4sI", b"data", len(pcm)))
        f.write(pcm)
        if pad:
            f.write(b"\x00")


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


# ===========================================================================
# DSP primitives
# ===========================================================================

def decimate_boxcar(x, factor):
    """Average non-overlapping groups of `factor` samples.

    Built from strided slices summed with `map(operator.add, ...)` so the work
    happens at C speed; a per-sample Python loop over 25 M samples does not.
    """
    from operator import add
    n = len(x) // factor
    if n == 0:
        return array("f")
    cols = [x[k:k + n * factor:factor] for k in range(factor)]
    acc = list(cols[0])
    for c in cols[1:]:
        acc = list(map(add, acc, c))
    inv = 1.0 / factor
    return array("f", [v * inv for v in acc])


def biquad_highpass(x, fs, fc, q=0.70710678):
    """RBJ 2nd-order highpass, applied forward (phase is irrelevant here —
    the output only feeds a short-time energy envelope)."""
    w0 = 2.0 * math.pi * fc / fs
    c, s = math.cos(w0), math.sin(w0)
    al = s / (2.0 * q)
    b0, b1, b2 = (1 + c) / 2, -(1 + c), (1 + c) / 2
    a0, a1, a2 = 1 + al, -2 * c, 1 - al
    b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
    out = array("f", bytes(4 * len(x)))
    x1 = x2 = y1 = y2 = 0.0
    for i, v in enumerate(x):
        y = b0 * v + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1 = x1, v
        y2, y1 = y1, y
        out[i] = y
    return out


def band_envelope(x, sr):
    """Short-time energy of the 300 Hz-3 kHz band, in dB.

    Returns (frames, frame_rate, hop_seconds).
    """
    from operator import mul
    y = decimate_boxcar(x, DECIM)
    fs = sr / float(DECIM)
    z = biquad_highpass(y, fs, ONSET_HP_HZ)
    frames = []
    n = len(z)
    for s in range(0, n - ONSET_WIN, ONSET_HOP):
        blk = z[s:s + ONSET_WIN]
        e = sum(map(mul, blk, blk)) / ONSET_WIN
        frames.append(10.0 * math.log10(e + 1e-22))
    return frames, fs, ONSET_HOP / fs


def percentile(vals, pct):
    if not vals:
        return 0.0
    s = sorted(vals)
    k = (len(s) - 1) * pct / 100.0
    lo = int(math.floor(k))
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def detect_onsets(env, hop_s, flux_db=ONSET_FLUX_DB, lag=ONSET_LAG,
                  refractory_s=ONSET_REFRACTORY_S, gate_db=ONSET_GATE_DB):
    """Attack times (seconds) from an energy envelope, by spectral-flux peaks.

    Peaks are taken STRONGEST-FIRST with a refractory exclusion. Scanning
    left-to-right and suppressing everything for `refractory_s` after the first
    frame over threshold looks equivalent and is not: during a ring-out the
    envelope jitters enough to keep the flux above threshold continuously, so
    the left-to-right form swallows every following note.
    """
    n = len(env)
    if n < lag + 4:
        return []
    sm = [env[0]] * n
    for i in range(n):
        a = env[max(0, i - 1)]
        b = env[i]
        c = env[min(n - 1, i + 1)]
        sm[i] = (a + b + c) / 3.0
    flux = [0.0] * n
    for i in range(lag, n):
        flux[i] = sm[i] - sm[i - lag]
    floor = percentile(env, 5.0)
    cand = []
    for i in range(1, n - 1):
        if (flux[i] > flux_db and sm[i] > floor + gate_db
                and flux[i] >= flux[i - 1] and flux[i] > flux[i + 1]):
            cand.append(i)
    cand.sort(key=lambda i: -flux[i])
    refr = refractory_s / hop_s
    keep = []
    for i in cand:
        if all(abs(i - j) > refr for j in keep):
            keep.append(i)
    keep.sort()
    post_n = max(1, int(ONSET_RISE_POST_S / hop_s))
    pre_hi = max(1, int(ONSET_RISE_PRE_S[0] / hop_s))
    pre_lo = max(1, int(ONSET_RISE_PRE_S[1] / hop_s))
    out = []
    for i in keep:
        # walk back to the foot of the rise so the pre-roll lands in silence
        pre = max(0, i - lag - 6)
        base = min(sm[pre:i]) if i > pre else sm[i]
        j = i
        while j > pre and sm[j] > base + 3.0:
            j -= 1
        a = sm[j:min(n, j + post_n)]
        lo, hi = max(0, j - pre_hi), max(0, j - pre_lo)
        b = sm[lo:hi]
        if a and b and (sum(a) / len(a)) - (sum(b) / len(b)) < ONSET_RISE_DB:
            continue
        out.append(j * hop_s)
    return out


def onset_levels(onsets, x, sr, window_s=0.15):
    """Peak dBFS in the first `window_s` after each onset."""
    lv = []
    for t in onsets:
        s = int(t * sr)
        seg = x[s:s + int(window_s * sr)]
        pk = max((abs(v) for v in seg), default=0.0)
        lv.append(20.0 * math.log10(pk + 1e-12))
    return lv


def suppress_shadowed(onsets, levels, shadow_s=SHADOW_S, shadow_db=SHADOW_DB,
                      level_gate_db=LEVEL_GATE_DB, local_s=LEVEL_LOCAL_S):
    """Drop key/action noise and stray low-level transients.

    Returns the indices of the surviving events (indices into `onsets`).
    """
    keep = []
    for i, t in enumerate(onsets):
        shadowed = any(abs(onsets[j] - t) < shadow_s and levels[j] > levels[i] + shadow_db
                       for j in range(len(onsets)) if j != i)
        if not shadowed:
            keep.append(i)
    out = []
    for i in keep:
        near = [levels[j] for j in keep if abs(onsets[j] - onsets[i]) <= local_s]
        if levels[i] > percentile(near, 75.0) - level_gate_db:
            out.append(i)
    return out


# ===========================================================================
# FFT
# ===========================================================================

_TWIDDLE = {}


def _twiddles(n):
    tw = _TWIDDLE.get(n)
    if tw is None:
        tw = [complex(math.cos(-2.0 * math.pi * k / n),
                      math.sin(-2.0 * math.pi * k / n)) for k in range(n // 2)]
        _TWIDDLE[n] = tw
    return tw


def fft(a):
    """In-place iterative radix-2 FFT of a power-of-two complex list.

    Twiddles come from a precomputed table rather than a running product, so
    the last stage of a 16384-point transform does not accumulate 8192
    successive rounding errors.
    """
    n = len(a)
    if n & (n - 1):
        raise ValueError("fft length must be a power of two")
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            a[i], a[j] = a[j], a[i]
    tw = _twiddles(n)
    length = 2
    while length <= n:
        half = length >> 1
        step = n // length
        for i in range(0, n, length):
            k = 0
            for m in range(i, i + half):
                u = a[m]
                v = a[m + half] * tw[k]
                a[m] = u + v
                a[m + half] = u - v
                k += step
        length <<= 1
    return a


def rfft_mag(x):
    """Magnitude spectrum (bins 0..N/2) of a real, power-of-two-length signal.

    Uses the standard real-input packing: an N-point real transform is done as
    an N/2-point complex one plus an untangle, halving the work.
    """
    n = len(x)
    if n & (n - 1) or n < 4:
        raise ValueError("rfft_mag length must be a power of two >= 4")
    m = n // 2
    z = [complex(x[2 * i], x[2 * i + 1]) for i in range(m)]
    fft(z)
    tw = _twiddles(n)
    out = [0.0] * (m + 1)
    for k in range(m + 1):
        zk = z[k % m]
        zc = z[(m - k) % m].conjugate()
        even = (zk + zc) * 0.5
        odd = (zk - zc) * complex(0.0, -0.5)
        w = tw[k] if k < m else complex(-1.0, 0.0)
        val = even + w * odd
        out[k] = abs(val)
    return out


def hann(n):
    return [0.5 - 0.5 * math.cos(2.0 * math.pi * i / n) for i in range(n)]


_HANN = {}


def hann_cached(n):
    w = _HANN.get(n)
    if w is None:
        w = hann(n)
        _HANN[n] = w
    return w


def spectrum(x, start, n):
    """Hann-windowed magnitude spectrum of x[start:start+n], zero-padded."""
    w = hann_cached(n)
    seg = [0.0] * n
    avail = min(n, max(0, len(x) - start))
    for i in range(avail):
        seg[i] = x[start + i] * w[i]
    return rfft_mag(seg)


# ===========================================================================
# Spectral peaks
# ===========================================================================

def find_peaks(mag, df, rel_db=PEAK_REL_DB, top=PEAK_TOP, merge=PEAK_MERGE):
    """Local maxima with parabolic (log-magnitude) interpolation.

    The amplitude reference is the maximum WITHIN [FMIN, FMAX]. Referencing the
    whole spectrum instead lets the 2-5 Hz infrasonic rumble set the threshold,
    which on quiet notes rejects every real partial.
    """
    lo = max(1, int(FMIN / df))
    hi = min(len(mag) - 2, int(FMAX / df))
    if hi <= lo:
        return []
    ref = max(mag[lo:hi])
    thr = ref * (10.0 ** (rel_db / 20.0))
    found = []
    for i in range(lo, hi):
        v = mag[i]
        if v > mag[i - 1] and v >= mag[i + 1] and v > thr:
            a = math.log(mag[i - 1] + 1e-30)
            b = math.log(v + 1e-30)
            c = math.log(mag[i + 1] + 1e-30)
            den = a - 2 * b + c
            d = 0.5 * (a - c) / den if den != 0 else 0.0
            if abs(d) < 1.0:
                found.append(((i + d) * df, v))
    found.sort(key=lambda p: -p[1])
    kept = []
    for f, a in found:
        # a piano unison rings as several peaks a few tenths of a percent
        # apart; keeping all of them would let a hypothesis "explain" one
        # partial many times over
        if all(abs(f - g) > merge * max(f, g) for g, _ in kept):
            kept.append((f, a))
        if len(kept) >= top:
            break
    return kept


class PeakSet:
    """Frequency-sorted peaks with a bisect lookup and a 'strong' subset."""

    def __init__(self, peaks):
        peaks = sorted(peaks)
        self.f = [p[0] for p in peaks]
        self.a = [p[1] for p in peaks]
        self.amax = max(self.a) if self.a else 0.0
        self.strong_thr = self.amax * (10.0 ** (-STRONG_DB / 20.0))
        self.strong = [(f, a) for f, a in peaks if a >= self.strong_thr]
        self.strong_top = self.strong[-1][0] if self.strong else 0.0
        self.strong_energy = sum(a * a for _, a in self.strong)
        self.dominant = set(f for f, _ in sorted(peaks, key=lambda p: -p[1])[:3])

    def __len__(self):
        return len(self.f)

    def near(self, freq, tol):
        """Strongest peak within +/- tol of `freq`, or None."""
        i = bisect.bisect_left(self.f, freq - tol)
        best = None
        while i < len(self.f) and self.f[i] <= freq + tol:
            if best is None or self.a[i] > best[1]:
                best = (self.f[i], self.a[i])
            i += 1
        return best


# ===========================================================================
# Inharmonic pitch fit
# ===========================================================================

def partial_hz(k, f0, b):
    return k * f0 * math.sqrt(1.0 + b * k * k)


def n_partials(f0, b, hi):
    n = 0
    while n < MAXPART and partial_hz(n + 1, f0, b) <= hi:
        n += 1
    return max(n, 1)


def _tolerance(f0, fk, df):
    """Half-width for accepting a peak as partial k.

    Never wider than 0.35*f0 (or a neighbouring partial could be grabbed) and
    never narrower than two FFT bins.
    """
    return min(0.35 * f0, max(0.007 * fk, 2.0 * df))


def refine(ps, f0, b, df, hi, iterations=6):
    """Assign partials, then re-fit (f0, B) by weighted linear regression.

    The regression is the standard linearisation: with y = (f_k/k)^2 and
    x = k^2, the stiff-string law becomes y = f0^2 + f0^2*B*x, so an ordinary
    weighted least-squares line recovers both parameters at once. Two partials
    already determine the line exactly, so the fit runs from two — refusing to
    fit below three leaves such a hypothesis stuck at its seed, which then
    loses on residual to a one-partial rival whose residual is zero by
    construction.
    """
    for _ in range(iterations):
        xs, ys, ws = [], [], []
        for k in range(1, n_partials(f0, b, hi) + 1):
            fk = partial_hz(k, f0, b)
            m = ps.near(fk, _tolerance(f0, fk, df))
            if m:
                xs.append(float(k * k))
                ys.append((m[0] / k) ** 2)
                ws.append(m[1])
        if len(xs) < 2:
            return f0, b
        sw = sum(ws)
        mx = sum(w * v for w, v in zip(ws, xs)) / sw
        my = sum(w * v for w, v in zip(ws, ys)) / sw
        var = sum(w * (v - mx) ** 2 for w, v in zip(ws, xs)) / sw
        cov = sum(w * (u - mx) * (v - my) for w, u, v in zip(ws, xs, ys)) / sw
        slope = cov / var if var > 1e-9 else 0.0
        icpt = my - slope * mx
        if icpt <= 0:
            return f0, b
        nf0 = math.sqrt(icpt)
        nb = min(0.08, max(0.0, slope / icpt))
        done = abs(nf0 - f0) < 1e-6 * f0 and abs(nb - b) < 1e-10
        f0, b = nf0, nb
        if done:
            break
    return f0, b


def evaluate(ps, f0, b, df):
    """Score a hypothesis. Returns (score, explained, residual, assignments).

    The score is a two-way mismatch, which is what makes it octave-safe:

      explained  - share of STRONG peak energy the comb accounts for. Kills
                   hypotheses that are too high (a note read as its own 4th
                   partial leaves every other partial unexplained).
      coverage   - share of the comb's first 12 partials that a STRONG peak
                   actually lands on. Kills subharmonics, which explain
                   everything by being a denser sieve.
      residual   - weighted relative partial-position error. A real stiff
                   string fits to well under 0.4%; an accidental fit does not.

    A hypothesis must also account for one of the three loudest peaks: in a
    struck piano note the dominant spectral peak IS a partial of that note.
    """
    if f0 <= 0 or ps.strong_energy <= 0:
        return 0.0, 0.0, 1.0, {}
    hi = min(FMAX, ps.strong_top * 1.05)
    npred = n_partials(f0, b, hi)
    pred = [partial_hz(k, f0, b) for k in range(1, npred + 1)]
    em = un = res = odd = 0.0
    n_matched = 0
    dominant_ok = False
    for f, a in ps.strong:
        tol = _tolerance(f0, f, df)
        hit = None
        for j, fk in enumerate(pred):
            if abs(f - fk) < tol and (hit is None or abs(f - fk) < abs(f - pred[hit])):
                hit = j
        if hit is None:
            un += a * a
        else:
            em += a * a
            n_matched += 1
            res += abs(f - pred[hit]) / pred[hit] * a * a
            if (hit + 1) % 2 == 1:
                odd += a * a
            if f in ps.dominant:
                dominant_ok = True
    if em <= 0 or not dominant_ok:
        return 0.0, 0.0, 1.0, {}
    assigned = {}
    n_strong_hits = 0
    for k in range(1, npred + 1):
        m = ps.near(pred[k - 1], _tolerance(f0, pred[k - 1], df))
        if m:
            assigned[k] = m
            if m[1] >= ps.strong_thr and k <= COVER_PARTIALS:
                n_strong_hits += 1
    rel = res / em
    explained = em / (em + un)
    coverage = min(1.0, n_strong_hits / float(min(npred, COVER_PARTIALS)))
    # With one or two partials the fit passes exactly through them, so the
    # residual measures nothing; charging for it would hand every sparse
    # treble note to whichever rival claims the fewest partials.
    quality = math.exp(-rel / RESIDUAL_SCALE) if n_matched >= 3 else 1.0
    score = explained * math.sqrt(coverage) * quality
    if 1 not in assigned:
        score *= 0.85                     # weak bass fundamentals are normal,
                                          # a wholly absent one is weaker proof
    # A comb sitting an octave below the note matches only even partials, so
    # its odd ones carry essentially nothing (order 1e-4 of the energy). The
    # thresholds are deliberately far below that: a genuinely 2f-dominant piano
    # note still puts a few percent of its energy in partial 1, and penalising
    # THAT would swap a real note for its own octave.
    if odd < 0.005 * em:
        score *= 0.15
    elif odd < 0.03 * em:
        score *= 0.5
    return score, explained, rel, assigned


def repair_octave(ps, f0, b, df):
    """Fold a hypothesis to the octave (or twelfth) the evidence supports.

    Halving is taken only when it explains materially MORE strong energy (the
    note was read as its own 2nd/3rd partial); doubling is taken when it
    explains the same energy with fewer partials, which is Occam's razor
    applied to a comb that was acting as a sieve. B transforms with the index
    change: re-indexing k -> m*k turns (f0, B) into (f0/m, B/m^2).
    """
    hi = min(FMAX, ps.strong_top * 1.05)
    _, explained, _, _ = evaluate(ps, f0, b, df)
    for _ in range(4):
        moved = False
        for m in (2, 3):
            g0, gb = refine(ps, f0 / m, b / (m * m), df, hi)
            gs, ge, _, _ = evaluate(ps, g0, gb, df)
            if gs > 0 and ge > explained + 0.05:
                f0, b, explained = g0, gb, ge
                moved = True
                break
        if not moved:
            break
    for _ in range(4):
        moved = False
        for m in (2, 3):
            g0, gb = refine(ps, f0 * m, b * m * m, df, hi)
            gs, ge, _, _ = evaluate(ps, g0, gb, df)
            if gs > 0 and ge >= explained - 0.02:
                f0, b, explained = g0, gb, ge
                moved = True
                break
        if not moved:
            break
    return f0, b


def fit_pitch(ps, df):
    """Best (f0, B) for one spectrum, or None.

    One peak is enough: in the top octave a note often shows a single partial
    above the strike knock, and refusing to identify it would be worse than
    identifying it with low confidence.
    """
    if len(ps) < 1:
        return None
    hi = min(FMAX, ps.strong_top * 1.05)
    anchors = sorted(range(len(ps)), key=lambda i: -ps.a[i])[:ANCHORS]
    cands = []
    for i in anchors:
        for k in range(1, KMAX + 1):
            c = ps.f[i] / k
            if F0_LO <= c <= F0_HI:
                cands.append(c)
    cands.sort()
    seeds = []
    for c in cands:
        if not seeds or c / seeds[-1] > 1.004:
            seeds.append(c)
    best = None
    for c0 in seeds:
        for bs in B_SEEDS:
            f0, b = refine(ps, c0, bs, df, hi)
            if not (F0_LO <= f0 <= F0_HI):
                continue
            score, _, _, _ = evaluate(ps, f0, b, df)
            if score > 0 and (best is None or score > best[0]):
                best = (score, f0, b)
    if best is None:
        return None
    f0, b = repair_octave(ps, best[1], best[2], df)
    if not (F0_LO <= f0 <= F0_HI):
        return None
    score, explained, rel, assigned = evaluate(ps, f0, b, df)
    if score <= 0:
        return None
    return {"score": score, "f0": f0, "b": b, "assigned": assigned,
            "residual": rel, "explained": explained}


def estimate_pitch(x, sr, onset_sample):
    """Fit the inharmonic series at several analysis scales; keep the best.

    Reports the MODELLED first partial f0*sqrt(1+B) as `f1`, not the observed
    k=1 peak: in the bass the fundamental is often 20 dB below partial 11 and
    the nearest peak to it can be noise, while the fitted value is constrained
    by the whole series. The observed peak is reported separately.
    """
    best = None
    for n, skip in SCALES:
        start = onset_sample + int(skip * sr)
        mag = spectrum(x, start, n)
        df = sr / float(n)
        ps = PeakSet(find_peaks(mag, df))
        r = fit_pitch(ps, df)
        if r and (best is None or r["score"] > best["score"]):
            r = dict(r)
            r["fft_size"] = n
            r["skip_s"] = skip
            best = r
    if best is None:
        return None
    f0, b = best["f0"], best["b"]
    assigned = best["assigned"]
    f1 = f0 * math.sqrt(1.0 + b)
    return {
        "f0_hz": f0,
        "f1_hz": f1,
        "f1_measured_hz": assigned[1][0] if 1 in assigned else None,
        "inharmonicity_b": b,
        # B is a two-parameter fit; with fewer than 3 partials it is not
        # measurable and `refine` leaves it at its seed. Say so rather than
        # letting prepare.py trust a number that carries no information.
        "b_is_fitted": len(assigned) >= 3,
        "partials_used": len(assigned),
        "confidence": best["score"],
        "residual_rel": best["residual"],
        "fft_size": best["fft_size"],
        "skip_s": best["skip_s"],
        "detected_midi_float": hz_to_midi(f1),
    }


# ===========================================================================
# Ladder matching
# ===========================================================================

MATCH_WINDOW = 3.0      # semitones; beyond this a pair is not a plausible match
FLAG_WINDOW = 1.0       # semitones; beyond this a matched pair is FLAGGED
GAP_COST = 1.6          # cost of leaving a ladder rung or an event unmatched


def align_to_ladder(detected_midi, ladder_midi):
    """Needleman-Wunsch alignment of detected pitches to the expected ladder.

    Returns a list of (detected_index | None, ladder_index | None) in order.
    A global alignment rather than a positional zip, because a take can carry
    both extra events (false starts, re-strikes, damper noise that survived
    suppression) and missing rungs, and a positional zip would shift every
    later note by one and mislabel the whole tail.
    """
    n, m = len(detected_midi), len(ladder_midi)
    inf = float("inf")
    cost = [[0.0] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        cost[i][0] = cost[i - 1][0] + GAP_COST
        back[i][0] = "d"
    for j in range(1, m + 1):
        cost[0][j] = cost[0][j - 1] + GAP_COST
        back[0][j] = "l"
    for i in range(1, n + 1):
        di = detected_midi[i - 1]
        for j in range(1, m + 1):
            d = abs(di - ladder_midi[j - 1]) if di is not None else MATCH_WINDOW
            diag = cost[i - 1][j - 1] + (d if d <= MATCH_WINDOW else inf)
            up = cost[i - 1][j] + GAP_COST
            left = cost[i][j - 1] + GAP_COST
            bestc = min(diag, up, left)
            cost[i][j] = bestc
            back[i][j] = "m" if bestc == diag else ("d" if bestc == up else "l")
    out = []
    i, j = n, m
    while i > 0 or j > 0:
        step = back[i][j]
        if step == "m":
            out.append((i - 1, j - 1))
            i -= 1
            j -= 1
        elif step == "d":
            out.append((i - 1, None))
            i -= 1
        else:
            out.append((None, j - 1))
            j -= 1
    out.reverse()
    return out


# ===========================================================================
# Driver
# ===========================================================================

def parse_overrides(args, flag):
    """--assign=PASS:IDX:NOTE / --drop=PASS:IDX, repeatable."""
    out = {}
    for a in args:
        if not a.startswith(flag + "="):
            continue
        body = a.split("=", 1)[1]
        parts = body.split(":")
        if flag == "--drop":
            if len(parts) != 2:
                raise SystemExit(f"bad {flag} (want PASS:IDX): {a}")
            out.setdefault(parts[0], set()).add(int(parts[1]))
        else:
            if len(parts) != 3:
                raise SystemExit(f"bad {flag} (want PASS:IDX:NOTE): {a}")
            note_to_midi(parts[2])          # validate now, not at write time
            out.setdefault(parts[0], {})[int(parts[1])] = parts[2]
    return out


def slugify(name):
    return name.replace("#", "s")


def analyse_take(path, spec, out_dir, opts):
    """Detect, identify, align, and emit every slice of one take."""
    info = read_wav_info(path)
    base = os.path.basename(path)
    print(f"\n=== {base}")
    print(f"    {info.channels} ch / {info.bits}-bit / {info.sample_rate} Hz / "
          f"{info.duration_s:.2f} s / data at byte {info.data_offset}")
    if info.bits != 24:
        print(f"    WARNING: expected 24-bit source, got {info.bits}-bit")

    x = load_channel(info, opts["channel"])
    sr = info.sample_rate
    env, _fs, hop_s = band_envelope(x, sr)
    raw_onsets = detect_onsets(env, hop_s)
    levels = onset_levels(raw_onsets, x, sr)
    kept = suppress_shadowed(raw_onsets, levels)
    print(f"    onsets: {len(raw_onsets)} transients -> {len(kept)} struck notes")

    digest = sha256_file(path) if not opts["no_hash"] else None
    manifest = {
        "tool": "b1-slice",
        "tool_version": TOOL_VERSION,
        "source": {
            "file": base,
            "path": os.path.abspath(path),
            "sha256": digest,
            "channels": info.channels,
            "channel_used": opts["channel"],
            "bits": info.bits,
            "sample_rate": sr,
            "frames": info.frames,
            "duration_s": round(info.duration_s, 6),
            "data_offset": info.data_offset,
            "gain_group": spec.get("gain_group"),
            "note": spec.get("note"),
        },
        "params": {
            "onset_band_hz": [ONSET_HP_HZ, sr / DECIM / 2.0],
            "onset_flux_db": ONSET_FLUX_DB,
            "onset_refractory_s": ONSET_REFRACTORY_S,
            "shadow_s": SHADOW_S,
            "shadow_db": SHADOW_DB,
            "level_gate_db": LEVEL_GATE_DB,
            "pre_roll_s": opts["pre_roll"],
            "slice_s": opts["slice_s"],
            "next_guard_s": opts["guard"],
            "fft_scales": [list(s) for s in SCALES],
            "flag_window_semitones": FLAG_WINDOW,
        },
        "passes": [],
        "slices": [],
    }

    all_times = [raw_onsets[i] for i in kept]
    for pass_name, t0, t1, ladder_name in spec["passes"]:
        ladder = opts["ladder"].get(pass_name) or LADDERS[ladder_name]
        ladder_midi = [note_to_midi(n) for n in ladder]
        idx = [i for i, t in enumerate(all_times) if t0 <= t < t1]
        drops = opts["drops"].get(pass_name, set())
        assigns = opts["assigns"].get(pass_name, {})

        events = []
        for local, gi in enumerate(idx):
            if local in drops:
                continue
            t = all_times[gi]
            onset_sample = int(round(t * sr))
            pitch = estimate_pitch(x, sr, onset_sample)
            forced = assigns.get(local)
            ev = {
                "event_index": local,
                "onset_s": t,
                "onset_sample": onset_sample,
                "pitch": pitch,
                "forced_note": forced,
            }
            if forced is not None:
                ev["midi"] = float(note_to_midi(forced))
            elif pitch is not None:
                ev["midi"] = pitch["detected_midi_float"]
            else:
                ev["midi"] = None
            events.append(ev)

        pairs = align_to_ladder([e["midi"] for e in events], ladder_midi)
        by_event = {}
        matched_rungs = set()
        for ei, li in pairs:
            if ei is not None and li is not None:
                by_event[ei] = li
                matched_rungs.add(li)

        rows = []
        flagged, extras = [], []
        for ei, ev in enumerate(events):
            li = by_event.get(ei)
            status = "extra"
            assigned_midi = None
            ladder_note = None
            if ev["forced_note"] is not None:
                status = "assigned"
                assigned_midi = note_to_midi(ev["forced_note"])
                ladder_note = ev["forced_note"]
            elif li is not None:
                ladder_note = ladder[li]
                delta = abs(ev["midi"] - ladder_midi[li]) if ev["midi"] is not None else 99
                if delta <= FLAG_WINDOW:
                    status = "assigned"
                    assigned_midi = ladder_midi[li]
                else:
                    status = "flagged"
                    matched_rungs.discard(li)
            if status == "flagged":
                flagged.append((ei, ladder_note, ev))
            elif status == "extra":
                extras.append((ei, ev))
            rows.append((ei, ev, li, status, assigned_midi, ladder_note))

        missing = [ladder[j] for j in range(len(ladder)) if j not in matched_rungs]

        print(f"    pass '{pass_name}' [{t0:.0f}-{t1:.0f} s]: {len(events)} events, "
              f"{len(ladder)} rungs, "
              f"{sum(1 for r in rows if r[3] == 'assigned')} assigned, "
              f"{len(flagged)} flagged, {len(extras)} extra, {len(missing)} missing")
        if missing:
            print(f"      missing: {' '.join(missing)}")
        for ei, ln, ev in flagged:
            got = midi_to_note(ev['midi']) if ev['midi'] is not None else "?"
            conf = ev["pitch"]["confidence"] if ev["pitch"] else 0.0
            print(f"      FLAG event {ei} @ {ev['onset_s']:8.3f}s: ladder says {ln}, "
                  f"pitch reads {got} (conf {conf:.2f})")

        manifest["passes"].append({
            "name": pass_name,
            "start_s": t0,
            "end_s": t1,
            "ladder_name": ladder_name,
            "ladder": ladder,
            "events": len(events),
            "assigned": sum(1 for r in rows if r[3] == "assigned"),
            "flagged": [{"event_index": ei, "ladder_note": ln,
                         "detected_note": (midi_to_note(ev["midi"])
                                           if ev["midi"] is not None else None)}
                        for ei, ln, ev in flagged],
            "missing": missing,
            "extras": len(extras),
        })

        emit_slices(rows, events, x, info, sr, out_dir, pass_name, manifest, opts)

    mpath = os.path.join(out_dir, os.path.splitext(base)[0] + ".manifest.json")
    os.makedirs(out_dir, exist_ok=True)
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print(f"    manifest: {mpath}")
    return manifest


def emit_slices(rows, events, x, info, sr, out_dir, pass_name, manifest, opts):
    """Cut and write one archival WAV per surviving event."""
    onsets = [e["onset_sample"] for e in events]
    for n, (ei, ev, li, status, assigned_midi, ladder_note) in enumerate(rows):
        if status == "extra" and not opts["extras"]:
            manifest["slices"].append(slice_record(
                None, ev, info, sr, pass_name, li, status, assigned_midi,
                ladder_note, 0, 0, None, None, None))
            continue
        onset = ev["onset_sample"]
        start = max(0, onset - int(opts["pre_roll"] * sr))
        end = start + int((opts["pre_roll"] + opts["slice_s"]) * sr)
        if n + 1 < len(onsets):
            end = min(end, max(start + 1, onsets[n + 1] - int(opts["guard"] * sr)))
        end = min(end, info.frames)
        nframes = max(0, end - start)
        raw = read_frames(info, start, nframes)
        pcm = channel_bytes(raw, info, opts["channel"])
        floats = decode_pcm(pcm, info.bits)
        peak = max((abs(v) for v in floats), default=0.0)
        head = floats[:int(0.2 * sr)]
        rms = math.sqrt(sum(v * v for v in head) / len(head)) if head else 0.0

        if status == "assigned":
            label = f"{ladder_note}"
        elif status == "flagged":
            label = f"FLAG-{ladder_note or 'none'}"
        else:
            label = "extra"
        name = f"{pass_name}_{ei:02d}_{slugify(label)}.wav"
        path = os.path.join(out_dir, name)
        write_wav_mono(path, pcm, info.bits, sr)

        opus = None
        if opts["opus"]:
            opus = encode_opus(path, opts)

        manifest["slices"].append(slice_record(
            name, ev, info, sr, pass_name, li, status, assigned_midi,
            ladder_note, start, nframes, peak, rms, opus))


def slice_record(name, ev, info, sr, pass_name, li, status, assigned_midi,
                 ladder_note, start, nframes, peak, rms, opus):
    p = ev["pitch"]
    ref_midi = assigned_midi
    if ref_midi is None and ev["midi"] is not None:
        ref_midi = int(round(ev["midi"]))
    cents = None
    if p is not None and ref_midi is not None:
        cents = round(cents_vs(p["f1_hz"], ref_midi), 2)
    return {
        "file": name,
        "source_file": os.path.basename(info.path),
        "source_channel": 0,
        "source_sample_rate": sr,
        "source_offset": start,
        "onset_sample": ev["onset_sample"],
        "onset_s": round(ev["onset_s"], 6),
        "pass": pass_name,
        "event_index": ev["event_index"],
        "ladder_index": li,
        "ladder_note": ladder_note,
        "assigned_midi": assigned_midi,
        "assigned_note": midi_to_note(assigned_midi) if assigned_midi is not None else None,
        "status": status,
        "pitch_source": "override" if ev["forced_note"] is not None else "auto",
        "detected_midi": int(round(ev["midi"])) if ev["midi"] is not None else None,
        "detected_note": midi_to_note(ev["midi"]) if ev["midi"] is not None else None,
        "f1_hz": round(p["f1_hz"], 4) if p else None,
        "f1_measured_hz": (round(p["f1_measured_hz"], 4)
                           if p and p["f1_measured_hz"] else None),
        "f0_hz": round(p["f0_hz"], 4) if p else None,
        "inharmonicity_b": float(f"{p['inharmonicity_b']:.6g}") if p else None,
        "b_is_fitted": p["b_is_fitted"] if p else None,
        "partials_used": p["partials_used"] if p else 0,
        "pitch_confidence": round(p["confidence"], 4) if p else 0.0,
        "pitch_residual_rel": round(p["residual_rel"], 6) if p else None,
        "pitch_fft_size": p["fft_size"] if p else None,
        "cents_vs_et": cents,
        "peak_dbfs": round(20.0 * math.log10(peak + 1e-12), 3) if peak else None,
        "rms200_dbfs": round(20.0 * math.log10(rms + 1e-12), 3) if rms else None,
        "frames": nframes,
        "duration_s": round(nframes / float(sr), 6) if nframes else 0.0,
        "opus": opus,
    }


def encode_opus(wav_path, opts):
    """Encode an archival .opus next to the slice; record the exact argv."""
    out = os.path.splitext(wav_path)[0] + ".opus"
    argv = [opts["ropusenc"], "--bitrate", str(opts["opus_bitrate"]),
            "--vbr", wav_path, out]
    try:
        subprocess.run(argv, check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"      ropusenc failed for {os.path.basename(wav_path)}: {exc}")
        return None
    return {"file": os.path.basename(out), "argv": argv}


USAGE = """\
usage: slice.py [--all | --take=FILE ...] [options]

  --all                  process every take in the built-in TAKES table
  --take=FILE            process one take (bare name resolves under --src)
  --src=DIR              where the raw takes live (default: Downloads)
  --out=DIR              output directory (required)
  --channel=N            source channel to take (default 0 = L; never sum)
  --pre-roll=S           silence kept before the attack (default 0.005)
  --length=S             slice length (default 8.0)
  --guard=S              gap kept before the next attack (default 0.15)
  --ladder=PASS:N1,N2,.. override the expected ladder for a pass
  --assign=PASS:IDX:NOTE force one event's pitch (repeatable)
  --drop=PASS:IDX        discard one detected event (repeatable)
  --no-extras            do not write WAVs for unmatched events
  --opus                 also encode each slice with ropusenc
  --ropusenc=PATH        ropusenc binary (default: ropusenc)
  --opus-bitrate=N       ropusenc bitrate in bps (default 128000)
  --no-hash              skip the source sha256 (faster on repeated runs)
"""


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or "--help" in args or "-h" in args:
        print(USAGE)
        return 0

    def flag(name, default=None, cast=str):
        for a in args:
            if a.startswith(name + "="):
                return cast(a.split("=", 1)[1])
        return default

    src = flag("--src", os.path.join(os.path.expanduser("~"), "Downloads"))
    out_dir = flag("--out")
    if not out_dir:
        print("error: --out=DIR is required\n")
        print(USAGE)
        return 2

    ladders = {}
    for a in args:
        if a.startswith("--ladder="):
            body = a.split("=", 1)[1]
            name, _, notes = body.partition(":")
            ladders[name] = [n for n in notes.replace(",", " ").split() if n]

    opts = {
        "channel": flag("--channel", 0, int),
        "pre_roll": flag("--pre-roll", PRE_ROLL_S, float),
        "slice_s": flag("--length", SLICE_S, float),
        "guard": flag("--guard", NEXT_GUARD_S, float),
        "extras": "--no-extras" not in args,
        "opus": "--opus" in args,
        "ropusenc": flag("--ropusenc", "ropusenc"),
        "opus_bitrate": flag("--opus-bitrate", 128000, int),
        "no_hash": "--no-hash" in args,
        "assigns": parse_overrides(args, "--assign"),
        "drops": parse_overrides(args, "--drop"),
        "ladder": ladders,
    }
    if opts["opus"] and shutil.which(opts["ropusenc"]) is None:
        print(f"error: ropusenc not found on PATH ({opts['ropusenc']})")
        return 2

    takes = []
    if "--all" in args:
        takes = [os.path.join(src, n) for n in TAKES]
    for a in args:
        if a.startswith("--take="):
            p = a.split("=", 1)[1]
            takes.append(p if os.path.isabs(p) or os.path.exists(p)
                         else os.path.join(src, p))
    if not takes:
        print("error: nothing to do (pass --all or --take=FILE)\n")
        print(USAGE)
        return 2

    os.makedirs(out_dir, exist_ok=True)
    for path in takes:
        if not os.path.exists(path):
            print(f"error: no such take: {path}")
            return 2
        spec = TAKES.get(os.path.basename(path))
        if spec is None:
            # an unknown take is still sliceable: treat the whole file as one
            # pass against the standard ladder, and say so
            print(f"note: {os.path.basename(path)} is not in the TAKES table; "
                  f"treating the whole file as one 'unknown' pass")
            info = read_wav_info(path)
            spec = {"gain_group": None, "note": "not in TAKES table",
                    "passes": [("unknown", 0.0, info.duration_s + 1.0, "thirds_a0")]}
        analyse_take(path, spec, out_dir, opts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
