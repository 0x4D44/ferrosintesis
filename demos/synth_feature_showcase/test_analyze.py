from __future__ import annotations

import unittest

import analyze
import engine as en
import verify


class DynamicArcTests(unittest.TestCase):
    def test_accepts_third_quarter_climax_and_final_drop(self) -> None:
        self.assertEqual([], analyze.dynamic_arc_failures([0.10, 0.06, 0.11, 0.08]))

    def test_rejects_flat_audio_even_with_third_quarter_peak(self) -> None:
        failures = analyze.dynamic_arc_failures([0.100, 0.101, 0.102, 0.100])
        self.assertTrue(any("span is too flat" in failure for failure in failures))

    def test_rejects_missing_final_drop(self) -> None:
        failures = analyze.dynamic_arc_failures([0.08, 0.09, 0.10, 0.10])
        self.assertTrue(any("final drop" in failure for failure in failures))


class MatchedAudioWindowTests(unittest.TestCase):
    def test_rejects_comparing_different_programs(self) -> None:
        score = en.Score(seed=1, title="test", tempo=120, beats=16)
        score.channel(0, "keys", program=0)
        score.program(0, 4, 8)
        score.audio_check(
            en.AudioCheck("cross-program", "rms_up", 8, 12, 0, 4, 1.0, channel=0)
        )

        failures = verify.check_audio_windows(score)

        self.assertTrue(any("compares programs 0 and 4" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
