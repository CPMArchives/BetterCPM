#!/usr/bin/env python3
"""Distribution failure gates: no silent omissions, overfill, or stale cache."""
import json
from pathlib import Path
import tempfile
import unittest
from build_distribution import capacity, selected_files, current_build, digest, publish_named, publish_generation


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

    def test_repeat_build_reuses_release_and_restores_named_image(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);candidate=root/'candidate';target=candidate/'trs80gp'
            target.mkdir(parents=True)
            image=target/'disk.dmk';image.write_bytes(b'qualified image')
            report={'target':'trs80gp','sha256':digest(image.read_bytes())}
            (target/'report.json').write_text(json.dumps(report))
            (target/'build.log').write_text('first build')
            reports=[(target,image,report)];generation=root/'release'
            self.assertFalse(publish_generation(candidate,generation,reports))
            (target/'build.log').write_text('repeat build')
            self.assertTrue(publish_generation(candidate,generation,reports))
            self.assertEqual((generation/'trs80gp/build.log').read_text(),'first build')
            named=root/'build/trs80/disk.dmk';named.parent.mkdir(parents=True)
            named.write_bytes(b'changed by emulator')
            publish_named(generation,reports,root)
            self.assertEqual(named.read_bytes(),b'qualified image')

    def test_repeat_build_rejects_damaged_or_different_release(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);candidate=root/'candidate';target=candidate/'trs80gp'
            target.mkdir(parents=True)
            image=target/'disk.dmk';image.write_bytes(b'qualified image')
            report={'target':'trs80gp','sha256':digest(image.read_bytes())}
            (target/'report.json').write_text(json.dumps(report))
            reports=[(target,image,report)];generation=root/'release'
            publish_generation(candidate,generation,reports)
            stored=generation/'trs80gp/disk.dmk';stored.write_bytes(b'damaged')
            with self.assertRaisesRegex(ValueError,'integrity'):
                publish_generation(candidate,generation,reports)
            self.assertEqual(stored.read_bytes(),b'damaged')
            stored.write_bytes(image.read_bytes())
            saved=generation/'trs80gp/report.json'
            saved.write_text(json.dumps(dict(report,source='different')))
            with self.assertRaisesRegex(ValueError,'differs'):
                publish_generation(candidate,generation,reports)
            saved.unlink()
            with self.assertRaisesRegex(ValueError,'incomplete'):
                publish_generation(candidate,generation,reports)

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
