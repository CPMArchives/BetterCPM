"""Bind real BYE output to input records; refuse stale or raced receipts."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build_z80pack_bye as builder


class BuildRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.assembler = Path.home()/'bin/z80asm'
        if not self.assembler.is_file():
            self.skipTest('real z80asm unavailable')
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def build(self, **kwargs):
        return builder.build(self.assembler, self.output, **kwargs)

    def report(self):
        return json.loads((self.output/'build-report.json').read_text())

    def test_rebuild_and_explicit_reference(self):
        first = self.build()
        report = self.report()
        self.assertEqual(report['artifact']['sha256'], hashlib.sha256(first).hexdigest())
        self.assertEqual(report['comparison']['state'], 'unknown')
        baseline = self.output/'baseline.json'
        baseline.write_text(json.dumps(report['input_record']))
        second = self.build(baseline=baseline)
        self.assertEqual(first, second)
        self.assertEqual(self.report()['comparison']['state'], 'unchanged')

    def test_failed_assembler_removes_old_receipt(self):
        self.build()
        with patch.object(builder, 'assemble', side_effect=RuntimeError('assembler failed')):
            with self.assertRaises(RuntimeError):
                self.build()
        self.assertFalse((self.output/'build-report.json').exists())

    def test_source_race_refuses_receipt(self):
        original = builder.capture
        count = 0
        def racing(*args, **kwargs):
            nonlocal count
            result = original(*args, **kwargs)
            count += 1
            if count == 2:
                result['fingerprint'] = 'changed-during-build'
            return result
        with patch.object(builder, 'capture', side_effect=racing):
            with self.assertRaisesRegex(RuntimeError, 'inputs changed'):
                self.build()
        self.assertFalse((self.output/'build-report.json').exists())

    def test_unsupported_capture_does_not_disable_builder(self):
        with patch.object(builder, 'capture', side_effect=ValueError('unsupported profile')):
            image = self.build()
        self.assertTrue(image)
        self.assertIsNone(self.report()['input_record'])
        self.assertEqual(self.report()['comparison']['state'], 'unknown')


if __name__ == '__main__':
    unittest.main()
