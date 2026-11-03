"""Reject incomplete or substituted corresponding-source companions."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from cpm_tools_source import ROOT, verify


class SourceCompanionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root/'third_party/cpm-tools'
        shutil.copytree(ROOT/'third_party/cpm-tools', self.base)

    def test_complete_pin_and_all_seven_binary_mappings(self):
        paths = verify(self.root)
        self.assertIn('third_party/cpm-tools/source/cominfo/src/COMINFO.MAC', paths)
        self.assertIn('third_party/cpm-tools/source/sysinfo/src/SYSINFO.ASM', paths)
        self.assertIn('third_party/cpm-tools/source/BUILD.SUB', paths)

    def test_source_substitution_rejects(self):
        (self.base/'source/cominfo/src/COMINFO.MAC').write_text('changed source')
        with self.assertRaisesRegex(ValueError, 'source differs'):
            verify(self.root)

    def test_binary_substitution_rejects(self):
        (self.base/'COMINFO.COM').write_bytes(b'wrong executable')
        with self.assertRaisesRegex(ValueError, 'binary differs'):
            verify(self.root)

    def test_missing_source_rejects(self):
        (self.base/'source/cominfo/src/COMINFO.MAC').unlink()
        with self.assertRaises(FileNotFoundError):
            verify(self.root)

    def test_pin_drift_rejects(self):
        path = self.base/'source-manifest.json'
        record = json.loads(path.read_text());record['commit'] = '0'*40
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, 'pin differs'):
            verify(self.root)

    def test_omitted_binary_mapping_rejects(self):
        path = self.base/'source-manifest.json'
        record = json.loads(path.read_text());del record['binaries']['COMINFO.COM']
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, 'mapping incomplete'):
            verify(self.root)


if __name__ == '__main__':
    unittest.main()
