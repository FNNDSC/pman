from unittest import TestCase

import pman

class TestPman(TestCase):
    def test_pman_constructor(self):
        myMan = pman.pman(
            debugFile = '/tmp/debug.file'
            )
        # didn't crash
        self.assertTrue(True)