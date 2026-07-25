#![no_main]

use libfuzzer_sys::fuzz_target;

// `offline::parse` is the crate's only untrusted-input surface: everything else takes a
// `Song` this function produced. Its contract is TOTAL — for any byte string at all it
// returns `Ok` or a `MidiError`. Never a panic (the caller wrote `match`, not
// `catch_unwind`), never a hang, never an unbounded allocation.
//
// This target does NOT render. Rendering is orders of magnitude slower than parsing and
// would starve the fuzzer of iterations; the allocation hazard it would probe is already
// answered at parse time by `MidiError::TooLong`, and that answer is asserted below.
fuzz_target!(|data: &[u8]| {
    if let Ok(song) = ferrosintesis::offline::parse(data) {
        // The invariant `TooLong` exists to uphold, restated as an assertion so the
        // fuzzer can try to break it: `render` allocates
        // `(seconds + tail) * rate * 8` bytes up front, so a song that parsed must
        // carry a length that is finite, non-negative and inside the cap. A tempo map
        // is entirely attacker-controlled — a few dozen bytes can declare 16 s per
        // quarter and a near-`u32::MAX` tick delta — and a NaN or an inf slipping
        // through here becomes an allocator abort downstream, which no caller can
        // catch.
        let seconds = song.seconds();
        assert!(
            seconds.is_finite()
                && (0.0..=ferrosintesis::offline::MAX_SONG_SECONDS).contains(&seconds),
            "parse() accepted a song of {seconds} s"
        );

        // Touch the rest of the accessors so their code paths are covered too: the
        // marker times run through the same tempo map as the events but are computed
        // AFTER the length guard, and the title is `from_utf8_lossy` over
        // attacker-chosen bytes.
        //
        // `initial_bpm()` is deliberately NOT asserted finite. A Set-Tempo of 0 us per
        // quarter — `00 FF 51 03 00 00 00` — parses cleanly (every tick maps to 0 s, so
        // the length guard is happy) and yields `60_000_000 / 0` = +inf. That is a
        // cosmetic wart in a reporting accessor, not a crash and not an allocation
        // hazard, and asserting on it here would fail the fuzz run on iteration one for
        // a non-defect.
        let _ = (
            song.events_len(),
            song.markers_len(),
            song.title().len(),
            song.initial_bpm(),
        );
    }
});
