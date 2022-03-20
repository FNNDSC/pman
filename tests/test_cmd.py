import unittest

from pman.resources import localize_path_args


class CmdTestCase(unittest.TestCase):
    def test_localize_path_args(self):
        self.assertListEqual(
            [],
            localize_path_args([], [], '/share/incoming')
        )
        self.assertListEqual(
            ['--boolFlag'],
            localize_path_args(['--boolFlag'], [], '/share/incoming')
        )
        self.assertListEqual(
            ['--something', '3'],
            localize_path_args(['--something', '3'], [], '/share/incoming')
        )
        self.assertListEqual(
            ['--something', '/share/incoming'],
            localize_path_args(['--something', 'user/uploads/wow.txt'], ['--something'], '/share/incoming')
        )
        self.assertListEqual(
            ['--boolFlag', '--something', '/share/incoming', '--foo', 'bar'],
            localize_path_args(['--boolFlag', '--something', 'user/uploads/wow.txt', '--foo', 'bar'], ['--something'], '/share/incoming')
        )
        self.assertListEqual(
            ['-foo', '/share/incoming', '-bar', '/share/incoming', '-bam', '5'],
            localize_path_args(['-foo', '3', '-bar', '4', '-bam', '5'], ['-foo', '-bar'], '/share/incoming')
        )


if __name__ == '__main__':
    unittest.main()
