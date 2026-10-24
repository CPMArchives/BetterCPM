"""Visible development selection is isolated by component and variant."""
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from component_inputs import ROOT, capture
from component_development import select


class DevelopmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'repo'
        plan = json.loads((ROOT/'metadata/component-inputs.json').read_text())
        paths = plan['components']['utility:BYE']['files'] + ['metadata/component-inputs.json','metadata/component-registry.json']
        for name in paths:
            path = self.root/name
            path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,path)
        self.assembler = Path(self.temp.name)/'assembler'
        self.assembler.write_bytes(b'tool fixture')
        env = patch.dict(os.environ,{},clear=True)
        env.start();self.addCleanup(env.stop)
        self.baseline = capture('utility:BYE',self.assembler,root=self.root)

    def install(self):
        (self.root/'metadata/component-baselines.json').write_text(json.dumps({
            'schema':1,'records':{'utility:BYE|z80pack|default|cross':self.baseline}}))

    def select(self, **kwargs):
        return select('utility:BYE',self.assembler,root=self.root,**kwargs)

    def test_missing_baseline_is_development(self):
        self.assertTrue(self.select()['development'])

    def test_matching_baseline(self):
        self.install()
        self.assertFalse(self.select()['development'])

    def test_relevant_edits(self):
        self.install()
        path=self.root/'src/platform/z80pack/bye.mac'
        path.write_bytes(path.read_bytes()+b'\n; changed relevant source\n')
        self.assertTrue(self.select()['development'])

    def test_unrelated_edits(self):
        self.install()
        (self.root/'tools/unrelated_test.py').write_text('unrelated')
        path=self.root/'metadata/component-registry.json';data=json.loads(path.read_text())
        data['components']['utility:PIP']['revision']+=1;path.write_text(json.dumps(data))
        self.assertFalse(self.select()['development'])

    def test_toolchain_mismatch(self):
        self.install();self.assembler.write_bytes(b'changed toolchain')
        self.assertTrue(self.select()['development'])

    def test_bad_baseline(self):
        self.install();(self.root/'metadata/component-baselines.json').write_text('invalid json')
        self.assertTrue(self.select()['development'])

    def test_explicit_comparison_modes(self):
        self.assertFalse(self.select(mode='assigned')['development'])
        self.assertTrue(self.select(mode='development')['development'])
        with self.assertRaises(ValueError):self.select(mode='invalid')

    def test_unsupported_variant(self):
        self.install();self.assertTrue(self.select(target='trs80gp')['development'])


if __name__=='__main__':unittest.main()
