from unittest import TestCase

import pman

class TestPman(TestCase):
    def test_pman_constructor(self):
        options = {
            'debugFile': '/tmp/debug.file'
        }
        myMan = pman.pman(options)
        # didn't crash
        self.assertTrue(True)