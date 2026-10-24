#!/usr/bin/env python3
"""Checked cache and publication isolation failure gates."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
import build_checked_distribution as checked
from build_distribution import digest,publish_named,publish_generation


class CheckedDistribution(unittest.TestCase):
    def test_checked_cache_rejects_drift(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'build').mkdir();artifact=root/'build/item';artifact.write_bytes(b'good')
            source={'revision':'test'};(root/'profile-state.json').write_text(json.dumps({'source':source}))
            state={'source':source,'artifacts':{'build/item':digest(b'good')}}
            stamp=root/'build-state.json';stamp.write_text(json.dumps(state))
            with patch.object(checked,'ROOT',root),patch.object(checked,'selected_contract',return_value={'test':True}):
                self.assertEqual(checked.components(True),{'test':True})
                artifact.write_bytes(b'bad')
                with self.assertRaisesRegex(ValueError,'artifact'):checked.components(True)
                artifact.write_bytes(b'good');state['artifacts']={};stamp.write_text(json.dumps(state))
                with self.assertRaisesRegex(ValueError,'inventory'):checked.components(True)
                state['source']={'revision':'foreign'};stamp.write_text(json.dumps(state))
                with self.assertRaisesRegex(ValueError,'source'):checked.components(True)

    def test_repeat_rejects_corrupt_published_package(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);candidate=root/'candidate';out=candidate/'z80pack';out.mkdir(parents=True)
            image=out/'image.dsk';image.write_bytes(b'image');(out/'SYSTEM.SYS').write_bytes(b'package')
            report={'target':'z80pack','sha256':digest(b'image'),'package_sha256':digest(b'package')}
            (out/'report.json').write_text(json.dumps(report));generation=root/'release'
            reports=[(out,image,report)];publish_generation(candidate,generation,reports)
            (generation/'z80pack/SYSTEM.SYS').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'integrity'):publish_generation(candidate,generation,reports)

    def test_named_profiles_are_separate(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);generation=root/'release';out=generation/'z80pack';out.mkdir(parents=True)
            image=out/'image.dsk';image.write_bytes(b'checked')
            paths=[]
            for profile in ('cpmsim-fullram','cpmsim-legacy-checked'):
                report={'target':'z80pack','profile':profile,'sha256':digest(b'checked')}
                paths+=publish_named(generation,[(out,image,report)],root)
            self.assertNotEqual(paths[0],paths[1])
            self.assertTrue(all(p.read_bytes()==b'checked' for p in paths))
            self.assertFalse((root/'build/z80pack/disks/library/image.dsk').exists())


if __name__=='__main__':unittest.main()
