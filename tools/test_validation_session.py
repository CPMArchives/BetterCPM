#!/usr/bin/env python3
"""Exercise the live PTY silence oracle used by console validation."""
import tempfile
import unittest
from pathlib import Path
from test_z80pack_sysgen_install import session


class SilenceOracle(unittest.TestCase):
    def run_provider(self, body, commands):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            disks = work/'disks'
            disks.mkdir()
            provider = work/'provider'
            provider.write_text('#!/usr/bin/env python3\nimport os, time\nos.write(1, b"A0>_ ")\n' + body)
            provider.chmod(0o755)
            return session(provider, disks, commands, work/'transcript.bin')

    def test_silence_interval_completes(self):
        transcript = self.run_provider('time.sleep(2)\n', [(b'', None, 0.1)])
        self.assertEqual(transcript, b'A0>_ ')

    def test_output_during_interval_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'expected silence'):
            self.run_provider('time.sleep(0.05)\nos.write(1, b"premature return")\ntime.sleep(2)\n', [(b'', None, 0.3)])


if __name__ == '__main__':
    unittest.main()
