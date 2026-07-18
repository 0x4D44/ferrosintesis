"""Focused regression tests: bank-select ordering + the guitar idiom
helpers (guitar block two — this engine is the designated seed)."""

import unittest

import engine as en
import verify


class VerifySeamTests(unittest.TestCase):
    def test_bank_select_sorts_before_program_change(self):
        score = en.Score(7)
        score.program(0, 48, 0.0)
        score.cc(0, 0, 1, 0.0)
        events = sorted(score.events[0], key=lambda event: (event[0], event[1]))
        self.assertEqual([event[2][0] & 0xF0 for event in events], [0xB0, 0xC0])
        self.assertEqual([], verify.check_bank_select_order(None, score))


_BW_STROKES = [(0.0, 1.4, 'D', 0), (1.5, 0.9, 'D', -8), (2.5, 0.45, 'U', -12),
               (3.0, 0.9, 'D', -4), (3.5, 0.45, 'U', -10)]
_CHORD = [48, 52, 55, 60, 64]


class StrumSeqTests(unittest.TestCase):
    def test_reproduces_big_weather_gtr_strum_table(self):
        """strum_seq must be a true superset of the hand-rolled stroke
        tables: at rake=1 / vel_up=0 it reproduces Big Weather t10's
        _gtr_strum (five en.strum calls) byte-for-byte."""
        a, b = en.Score(11), en.Score(11)
        for beat, dur, down, dv in ((0.0, 1.4, True, 0), (1.5, 0.9, True, -8),
                                    (2.5, 0.45, False, -12), (3.0, 0.9, True, -4),
                                    (3.5, 0.45, False, -10)):
            en.strum(a, 3, _CHORD, 8.0 + beat, dur, 76 + dv,
                     spread=0.025, down=down)
        en.strum_seq(b, 3, _CHORD, 8.0, _BW_STROKES, 76,
                     sweep_span=0.10, rake=1.0, vel_up=0)
        self.assertEqual(a.events, b.events)

    def test_rake_offsets_concave_and_guarded(self):
        offs = en._rake_offsets(6, 0.10, 1.6)
        self.assertEqual(len(offs), 6)
        self.assertEqual(offs[0], 0.0)
        self.assertAlmostEqual(offs[-1], 0.10)
        gaps = [b - a for a, b in zip(offs, offs[1:])]
        self.assertTrue(all(g > 0 for g in gaps), "offsets must increase")
        self.assertTrue(all(g2 <= g1 + 1e-12 for g1, g2 in zip(gaps, gaps[1:])),
                        "gaps must shrink toward the sweep's end (rake>1)")
        self.assertEqual(en._rake_offsets(1, 0.10, 1.6), [0.0])  # n=1 guard

    def test_directions_and_chuck(self):
        sc = en.Score(11)
        en.strum_seq(sc, 3, _CHORD, 0.5,
                     [(0.0, 1.0, 'D', 0), (1.0, 1.0, 'U', 0),
                      (2.0, 1.0, 'x', 0)],
                     80, sweep_span=0.08, rake=1.0, vel_up=-10)
        ons = [e for e in sc.events[3] if e[2][0] & 0xF0 == 0x90]
        ons.sort(key=lambda e: e[0])
        n = len(_CHORD)
        self.assertEqual(len(ons), 3 * n)
        down, up, chuck = ons[:n], ons[n:2 * n], ons[2 * n:]
        self.assertEqual([e[2][1] for e in down], _CHORD)
        self.assertEqual([e[2][1] for e in up], list(reversed(_CHORD)))
        # vel taper: jv=4 jitter means exact values vary; compare stroke
        # AVERAGES (jitter is zero-mean-ish; use a wide margin)
        avg = lambda evs: sum(e[2][2] for e in evs) / len(evs)
        self.assertLess(avg(up), avg(down) - 4, "vel_up must quieten ups")
        self.assertLess(avg(chuck), avg(down) - 15, "chuck must be quiet")
        # chuck notes are SHORT: off - on well under a tenth of a beat's
        # ticks plus the engine's minimum
        offs = sorted((e for e in sc.events[3] if e[2][0] & 0xF0 == 0x80),
                      key=lambda e: e[0])[2 * n:]
        for on, off in zip(chuck, offs):
            self.assertLessEqual(off[0] - on[0], en.PPQ // 4)

    def test_determinism(self):
        a, b = en.Score(5), en.Score(5)
        for sc in (a, b):
            en.strum_seq(sc, 3, _CHORD, 1.0, _BW_STROKES, 76)
        self.assertEqual(a.events, b.events)


_PC = {"maj": {0, 4, 7}, "min": {0, 3, 7}, "7": {0, 4, 7, 10}}


class VoicingTests(unittest.TestCase):
    def test_open_shapes_pinned_exactly(self):
        self.assertEqual(en.voicing(4, "maj", "E"),
                         [40, 47, 52, 56, 59, 64])   # open E major
        self.assertEqual(en.voicing(9, "min", "A"),
                         [45, 52, 57, 60, 64])       # open A minor
        self.assertEqual(en.voicing(2, "maj", "D"), [50, 57, 62, 66])
        self.assertEqual(en.voicing(7, "maj", "G"),
                         [43, 47, 50, 55, 59, 67])   # open G major
        self.assertEqual(en.voicing(0, "maj", "C"), [48, 52, 55, 60, 64])
        self.assertEqual(en.voicing(4, "7", "E"), [40, 47, 50, 56, 59, 64])

    def test_all_barre_roots_all_qualities(self):
        for quality, want in _PC.items():
            for root in range(12):
                v = en.voicing(root, quality)
                self.assertTrue(4 <= len(v) <= 6, (quality, root, v))
                self.assertEqual(v, sorted(v), "low to high")
                self.assertGreaterEqual(v[0], 40, "E2 floor")
                got = {(p - root) % 12 for p in v}
                self.assertEqual(got, {(x) % 12 for x in want},
                                 f"pitch-class SET equality {quality} {root}: {v}")
                self.assertEqual((v[0] - root) % 12, 0,
                                 "bass note must be the root for these shapes")

    def test_adversarial_root_octaves_pinned(self):
        # Eb: A-shape barre at fret 6 (bass Eb3=51), not an octave surprise
        self.assertEqual(en.voicing(3, "maj")[0], 51)
        # F#: E-shape barre at fret 2 (bass F#2=42)
        self.assertEqual(en.voicing(6, "maj")[0], 42)


class RunPitchesTests(unittest.TestCase):
    def test_chromatic_override_and_cc68_bracket(self):
        sc = en.Score(9)
        line = [64, 67, 66, 69, 68]          # chromatic — no scale spells it
        end = en.run(sc, 2, 4.0, 52, "aeolian", [], 0.25, 90, 60,
                     legato=True, pitches=line)
        self.assertAlmostEqual(end, 4.0 + len(line) * 0.25)
        evs = sorted(sc.events[2], key=lambda e: (e[0], e[1]))
        ccs = [e for e in evs if e[2][0] & 0xF0 == 0xB0 and e[2][1] == 68]
        self.assertEqual([c[2][2] for c in ccs], [127, 0], "CC68 bracket")
        ons = [e[2][1] for e in evs if e[2][0] & 0xF0 == 0x90]
        self.assertEqual(ons, line)

    def test_diatonic_path_unchanged_when_pitches_none(self):
        a, b = en.Score(3), en.Score(3)
        en.run(a, 2, 0.5, 52, "aeolian", [0, 2, 4], 0.25, 90, 70)
        en.run(b, 2, 0.5, 52, "aeolian", [0, 2, 4], 0.25, 90, 70,
               pitches=None)
        self.assertEqual(a.events, b.events)


if __name__ == "__main__":
    unittest.main()
