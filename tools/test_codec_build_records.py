"""All codec builds bind actual artifacts; selected codecs remain independent."""
import importlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from component_inputs import ROOT, capture, digest
from component_development import select
from codec_version import DESCRIPTIONS, DISPLAY


class CodecRecords(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name);self.assembler=Path.home()/'bin/z80asm'
        env=patch.dict(os.environ,{},clear=True);env.start();self.addCleanup(env.stop)

    def test_artifact_records_for_all_commands(self):
        if not self.assembler.is_file():self.skipTest('z80asm unavailable')
        for name in DESCRIPTIONS:
            with self.subTest(command=name):
                builder=importlib.import_module('build_'+name.lower())
                image=builder.build(self.assembler,self.work)
                report=json.loads((self.work/(name+'-build-report.json')).read_text())
                self.assertEqual(report['identity'],{'version':'1.0','revision':5})
                self.assertEqual(report['artifact']['sha256'],digest(image))
                self.assertFalse(report['display_selection']['development'])
                self.assertIsNone(DISPLAY.get())

    def test_failure_removes_receipt_and_resets_display(self):
        if not self.assembler.is_file():self.skipTest('z80asm unavailable')
        builder=importlib.import_module('build_sq')
        builder.build(self.assembler,self.work)
        with patch('build_sq.subprocess.run',side_effect=RuntimeError('assembler failed')):
            with self.assertRaises(RuntimeError):builder.build(self.assembler,self.work)
        self.assertFalse((self.work/'SQ-build-report.json').exists())
        self.assertIsNone(DISPLAY.get())

    def test_selected_codec_input_isolation(self):
        root=self.work/'repo'
        plans=json.loads((ROOT/'metadata/component-inputs.json').read_text())
        paths={'metadata/component-inputs.json','metadata/component-registry.json'}
        for name in ('SQ','USQ'):paths.update(plans['components']['utility:'+name]['files'])
        for name in paths:
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
        tool=self.work/'fixture-assembler';tool.write_bytes(b'fixture')
        records={}
        for name in ('SQ','USQ'):
            records['utility:'+name+'|z80pack|default|cross']=capture('utility:'+name,tool,root=root)
        (root/'metadata/component-baselines.json').write_text(json.dumps({'schema':1,'records':records}))
        p=root/'src/codec/sq.mac';p.write_bytes(p.read_bytes()+b'\n; selected change\n')
        self.assertTrue(select('utility:SQ',tool,root=root)['development'])
        self.assertFalse(select('utility:USQ',tool,root=root)['development'])


if __name__=='__main__':unittest.main()
