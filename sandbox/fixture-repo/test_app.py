import unittest

from app import label


class FixtureTests(unittest.TestCase):
    def test_label(self) -> None:
        self.assertEqual(label("safe"), "fixture:safe")
