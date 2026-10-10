#!/usr/bin/env python3
"""Distribution failure gates: no silent omissions, overfill, or stale cache."""
import json
from pathlib import Path
import tempfile
import unittest
from build_distribution import capacity, selected_files, current_build, digest, publish_named


class DistributionGates(unittest.TestCase):
    def test_planned_missing_is_reported(self):
        m={'system_disk':[{'name':'WHEREIS.COM','targets':['z80pack'],
                           'status':'planned','reason':'not implemented'}]}
        selected,omitted=selected_files(m,'z80pack',Path('/nonexistent'))
        self.assertEqual(selected,[])
        self.assertEqual(omitted[0]['status'],'planned')

    def test_implemented_missing_fails(self):
        m={'system_disk':[{'name':'DIR.COM','targets':['z80pack'],
                           'status':'implemented','artifact':'missing','user':0}]}
        with self.assertRaises(FileNotFoundError):
            selected_files(m,'z80pack',Path('/nonexistent'))

    def test_capacity_accounts_for_directory_and_extents(self):
        geometry={'block':1024,'blocks':5,'directory_blocks':2,'entries':1}
        with self.assertRaises(ValueError):
            capacity([({'name':'BIG.COM'},bytes(3073))],geometry)
        with self.assertRaises(ValueError):
            capacity([({'name':'A.COM'},b'a'),({'name':'B.COM'},b'b')],geometry)

    def test_named_publication_preserves_previous_image_on_bad_copy(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);generation=root/'generation';target=generation/'trs80gp'
            target.mkdir(parents=True)
            name='BetterCPM-Distribution-trs80gp-80T-DS-System.dmk'
            source=target/name;source.write_bytes(b'new')
            destination=root/'build/trs80'/name
            destination.parent.mkdir(parents=True);destination.write_bytes(b'previous')
            report={'target':'trs80gp','sha256':digest(b'expected')}
            with self.assertRaises(ValueError):
                publish_named(generation,[(target,source,report)],root)
            self.assertEqual(destination.read_bytes(),b'previous')
            report['sha256']=digest(b'new')
            publish_named(generation,[(target,source,report)],root)
            self.assertEqual(destination.read_bytes(),b'new')

    def test_cache_rejects_source_and_artifact_drift(self):
        with tempfile.TemporaryDirectory() as t:
            work=Path(t);root=work/'z80pack';root.mkdir()
            (root/'artifact').write_bytes(b'good')
            stamp={'source':{'revision':'x'},'artifacts':{'artifact':digest(b'good')}}
            (root/'build-state.json').write_text(json.dumps(stamp))
            self.assertEqual(current_build(work,'z80pack',stamp['source'],True),root)
            with self.assertRaises(ValueError):
                current_build(work,'z80pack',{'revision':'y'},True)
            (root/'artifact').write_bytes(b'old')
            with self.assertRaises(ValueError):
                current_build(work,'z80pack',stamp['source'],True)


if __name__=='__main__':
    unittest.main()
