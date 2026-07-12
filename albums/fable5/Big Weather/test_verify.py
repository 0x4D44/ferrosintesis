"""Focused regression tests for Big Weather's shared event/verifier seams."""

import types
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

    def test_meter_guard_uses_strict_interior_boundaries(self):
        part = types.SimpleNamespace(TIME_SIGNATURES=[
            (0.0, 4, 4), (8.0, 4, 4), (16.0, 3, 4), (32.0, 4, 4)])
        self.assertEqual([16.0], verify._meter_changes_in_span(part, 0.0, 32.0))
        self.assertEqual([], verify._meter_changes_in_span(part, 16.0, 32.0))
        self.assertEqual([], verify._meter_changes_in_span(part, 0.0, 16.0))

    def test_energy_and_drum_windows_fail_clearly_on_meter_crossing(self):
        part = types.SimpleNamespace(
            TIME_SIGNATURES=[(0.0, 4, 4), (8.0, 3, 4)],
            MOVEMENTS=[("section", 0.0, 16.0)],
        )
        module = types.SimpleNamespace(
            PART=part,
            ENERGY_RULES=[("section", ">=", "section", 1.0)],
            DRUM_SOLO_SPEC={"windows": [(0.0, 16.0)], "accompanists": set()},
        )
        score = en.Score(7)
        energy = verify.check_song_energy(module, score)
        drums = verify.check_drum_solo(module, score)
        self.assertTrue(any("variable-meter energy math is unsupported" in f
                            for f in energy), energy)
        self.assertTrue(any("variable-meter drum-solo math is unsupported" in f
                            for f in drums), drums)


if __name__ == "__main__":
    unittest.main()
