"""Selected-input isolation, variant binding, and unknown-state refusal."""
import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from component_inputs import ROOT, capture, classify, source_path


class InputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'repo'
        plan = json.loads((ROOT/'metadata/component-inputs.json').read_text())
        files = plan['components']['utility:BYE']['files'] + [
            'metadata/component-inputs.json', 'metadata/component-registry.json']
        for name in files:
            destination = self.root/name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, destination)
        self.assembler = Path(self.temp.name)/'assembler'
        self.assembler.write_bytes(b'fixture toolchain, not an executable')
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.baseline = self.capture()

    def capture(self, **kwargs):
        return capture('utility:BYE', self.assembler, root=self.root, **kwargs)

    def change_json(self, name, mutate):
        path = self.root/name
        data = json.loads(path.read_text())
        mutate(data)
        path.write_text(json.dumps(data))

    def state(self):
        return classify(self.capture(), self.baseline)['state']

    def test_identical_repeated_capture(self):
        self.assertEqual(self.baseline, self.capture())
        self.assertEqual(self.state(), 'unchanged')

    def test_unrelated_source_test_and_registry_edits(self):
        (self.root/'src/elsewhere.mac').write_text('different component')
        (self.root/'tools/test_unrelated.py').write_text('test change')
        self.change_json('metadata/component-registry.json',
            lambda d: d['components']['utility:PIP'].update(revision=30))
        self.assertEqual(self.state(), 'unchanged')

    def test_relevant_source_and_helpers(self):
        for relative in ('src/platform/z80pack/bye.mac', 'src/utilities/common/version.inc',
                         'tools/build_ccp.py'):
            with self.subTest(relative=relative):
                path = self.root/relative
                old = path.read_bytes()
                path.write_bytes(old+b'\n; modified input\n')
                self.assertEqual(self.state(), 'development')
                path.write_bytes(old)

    def test_toolchain_change(self):
        self.assembler.write_bytes(b'another toolchain')
        self.assertEqual(self.state(), 'development')

    def test_configuration_change(self):
        self.change_json('metadata/component-inputs.json',
            lambda d: d['components']['utility:BYE']['configuration'].update(origin=512))
        self.assertEqual(self.state(), 'development')

    def test_unrelated_map_entry(self):
        self.change_json('metadata/component-inputs.json',
            lambda d: d['components'].update({'utility:DDT': {'status': 'pending'}}))
        self.assertEqual(self.state(), 'unchanged')

    def test_revision_does_not_hash_itself(self):
        self.change_json('metadata/component-registry.json',
            lambda d: d['components']['utility:BYE'].update(revision=3))
        candidate = self.capture()
        self.assertEqual(candidate['fingerprint'], self.baseline['fingerprint'])
        self.assertEqual(classify(candidate, self.baseline)['state'], 'unknown')

    def test_missing_invalid_wrong_variant_baselines(self):
        self.assertEqual(classify(self.baseline)['state'], 'unknown')
        bad = copy.deepcopy(self.baseline)
        bad['inputs']['files']['forged'] = 'bad hash'
        self.assertEqual(classify(self.baseline, bad)['state'], 'unknown')
        for options in ({'profile':'cpmsim-fullram'}, {'build_mode':'native'}, {'target':'trs80gp'}):
            with self.assertRaises(ValueError):
                self.capture(**options)

    def test_unsupported_component(self):
        with self.assertRaisesRegex(ValueError, 'pending'):
            capture('utility:STAT', self.assembler, root=self.root)

    def test_missing_files_refused(self):
        (self.root/'src/platform/z80pack/bye.mac').unlink()
        with self.assertRaises(OSError):
            self.capture()

    def test_escape_and_duplicate_paths_refused(self):
        for relative in ('../escape', '/tmp/escape', 'build/output.bin', 'src/../tools/a.py'):
            with self.assertRaises(ValueError):
                source_path(self.root, relative)
        outside = Path(self.temp.name)/'outside'
        outside.write_text('outside')
        (self.root/'src/escape.mac').symlink_to(outside)
        with self.assertRaises(ValueError):
            source_path(self.root, 'src/escape.mac')
        self.change_json('metadata/component-inputs.json',
            lambda d: d['components']['utility:BYE']['files'].append('tools/build_ccp.py'))
        with self.assertRaises(ValueError):
            self.capture()

    def test_checked_environment_refused(self):
        os.environ['BETTERCPM_BUILD_CONTEXT'] = '/unverified/context.json'
        with self.assertRaisesRegex(ValueError, 'checked'):
            self.capture()


if __name__ == '__main__':
    unittest.main()
