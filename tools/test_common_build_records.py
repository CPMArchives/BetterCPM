"""Shared utility identification executes without initializing command work."""
import importlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from component_build import DISPLAY
from component_inputs import digest
from component_identity import identification
from test_utility_versions import runner, output


class CommonRecords(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name);self.assembler=Path.home()/'bin/z80asm'
        if not self.assembler.is_file():self.skipTest('z80asm unavailable')

    def test_common_query_blocks_and_artifact_records(self):
        for name,description in [('TIME','Clock Display and Setting'),('STAT','File, Disk and System Information')]:
            with self.subTest(command=name):
                builder=importlib.import_module('build_'+name.lower())
                image=builder.build(self.assembler,self.work)
                report=json.loads((self.work/(name+'-build-report.json')).read_text())
                self.assertEqual(report['identity'],{'version':'1.0','revision':4})
                self.assertFalse(report['display_selection']['development'])
                self.assertEqual(report['artifact']['sha256'],digest(image))
                for tail in ['/VER',' /ver ','X /VER Y','/VER /VER','\t/VeR']:
                    cpu=runner(image);text=tail.encode();cpu.mem[128]=len(text);cpu.mem[129:129+len(text)]=text
                    before=bytes(cpu.mem[:128]);cpu.run(256,limit=100000)
                    self.assertEqual(output(cpu),identification(name,'1.0',4,description))
                    self.assertEqual(bytes(cpu.mem[:128]),before)
                self.assertIsNone(DISPLAY.get())

    def test_explicit_development_query(self):
        from build_time import build
        image=build(self.assembler,self.work,identity_state='development')
        cpu=runner(image);cpu.mem[128]=4;cpu.mem[129:133]=b'/VER';cpu.run(256,limit=100000)
        self.assertIn('TIME 1.0 (004-dev)',output(cpu))

    def test_failure_removes_receipt_and_restores_context(self):
        from build_time import build
        build(self.assembler,self.work)
        with patch('build_time.subprocess.run',side_effect=RuntimeError('assembler failed')):
            with self.assertRaises(RuntimeError):build(self.assembler,self.work)
        self.assertFalse((self.work/'TIME-build-report.json').exists())
        self.assertIsNone(DISPLAY.get())


if __name__=='__main__':unittest.main()
