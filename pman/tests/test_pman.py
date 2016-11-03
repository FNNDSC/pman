from unittest import TestCase

from pman import pman

class TestPman(TestCase):
    def test_pman_constructor(self):
        myMan = pman(
            debugFile = '/tmp/debug.file'
            )
        # didn't crash
        self.assertTrue(True)
