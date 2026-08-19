import unittest

from core.routes_public import _JOIN_CHALLENGE_TYPES, _new_join_challenge


class JoinChallengeVariantsTest(unittest.TestCase):
    def test_every_variant_has_a_valid_answer(self):
        for kind in _JOIN_CHALLENGE_TYPES:
            with self.subTest(kind=kind):
                public, answer = _new_join_challenge(kind, 2)
                self.assertEqual(kind, public["type"])
                self.assertEqual(public["required"], len(answer))
                self.assertTrue(all(0 <= index < len(public["grid"]) for index in answer))

    def test_icon_targets_are_exact(self):
        public, answer = _new_join_challenge("icons", 3)
        matches = [index for index, value in enumerate(public["grid"]) if value == public["target"]]
        self.assertEqual(answer, matches)

    def test_math_answer_matches_prompt(self):
        public, answer = _new_join_challenge("math", 3)
        left, operator, right = public["prompt"].split()
        expected = int(left) + int(right) if operator == "+" else int(left) - int(right)
        self.assertEqual(expected, public["grid"][answer[0]])

    def test_sequence_answer_reconstructs_sequence(self):
        public, answer = _new_join_challenge("sequence", 2)
        reconstructed = [public["grid"][index] for index in answer]
        self.assertEqual(public["sequence"], reconstructed)


if __name__ == "__main__":
    unittest.main()
