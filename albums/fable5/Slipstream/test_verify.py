"""Focused regression test for Slipstream bank-select ordering."""

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


if __name__ == "__main__":
    unittest.main()
