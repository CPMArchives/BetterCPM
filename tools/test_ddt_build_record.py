"""DDT source closure, cross-target records and artifact binding."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import build_ddt as builder
from component_inputs import ROOT, capture, classify, digest


class DDTRecordTests(unittest.TestCase):
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

    def build(self, *arguments):
        argv = ['build_ddt.py', '--output', str(self.output), '--no-install', *arguments]
        with patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()):
            builder.main()
        return json.loads((self.output/'build-report.json').read_text())

    def test_real_artifact_and_reference(self):
        report = self.build()
        image = (self.output/'DDT.COM').read_bytes()
        self.assertEqual(report['artifact']['sha256'], digest(image))
        self.assertEqual(report['comparison']['state'], 'unknown')
        baseline = self.output/'baseline.json'
        baseline.write_text(json.dumps(report['input_record']))
        report = self.build('--baseline', str(baseline))
        self.assertEqual(report['comparison']['state'], 'unchanged')
        self.assertEqual((self.output/'DDT.COM').read_bytes(), image)

    def test_target_bound_record_same_binary(self):
        first = self.build()
        image = (self.output/'DDT.COM').read_bytes()
        second = self.build('--target', 'trs80gp')
        self.assertEqual((self.output/'DDT.COM').read_bytes(), image)
        self.assertEqual(classify(second['input_record'], first['input_record'])['state'], 'unknown')

    def test_race_removes_report(self):
        self.build()
        original = builder.capture
        calls = 0
        def racing(*args, **kwargs):
            nonlocal calls
            record = original(*args, **kwargs)
            calls += 1
            if calls == 2:
                record['fingerprint'] = 'raced-input'
            return record
        with patch.object(builder, 'capture', side_effect=racing):
            with self.assertRaisesRegex(RuntimeError, 'inputs changed'):
                self.build()
        self.assertFalse((self.output/'build-report.json').exists())

    def test_original_assembler_and_selected_ui_inputs(self):
        root = self.output/'repo'
        plan = json.loads((ROOT/'metadata/component-inputs.json').read_text())
        paths = plan['components']['utility:DDT']['files'] + [
            'metadata/component-inputs.json', 'metadata/component-registry.json']
        for name in paths:
            destination = root/name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, destination)
        baseline = capture('utility:DDT', self.assembler, root=root)
        for name in ['DDT0MOV.ASM', 'DDT1ASM.ASM', 'DDT2MON.ASM']:
            path = root/'third_party/dri-ddt'/name
            original = path.read_bytes()
            path.write_bytes(original+b'\n; test mutation\n')
            self.assertEqual(classify(capture('utility:DDT', self.assembler, root=root), baseline)['state'], 'development')
            path.write_bytes(original)
        path = root/'src/utilities/common/ui/wordstar.inc'
        path.write_bytes(path.read_bytes()+b'\n; selected UI changed\n')
        self.assertEqual(classify(capture('utility:DDT', self.assembler, root=root), baseline)['state'], 'development')


if __name__ == '__main__':
    unittest.main()
