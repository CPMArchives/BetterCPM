#!/usr/bin/env python3
"""Ensure a SEARCH PASS cannot be reused for changed or unqualified media."""
import copy
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from build_utilities_disk import validate_search_acceptance,sha
from search_distribution import companions


class Acceptance(unittest.TestCase):
    def setUp(self):
        self.files={'SEARCH.COM':b'qualified program'}
        self.receipt={'search_acceptance':'PASS','binary':{'sha256':sha(self.files['SEARCH.COM'])},
                      'platforms':{'z80pack':{'status':'PASS','utilities_sha256':sha(b'qualified disk'),
                          'system_sha256':'system identity','utilities_unchanged':True,
                          'fixtures_unchanged':True,'native_cross_parity':True}}}

    def test_exact(self):
        self.assertEqual(validate_search_acceptance(self.receipt,self.files,'z80pack',b'qualified disk')['status'],'PASS')

    def test_fail_closed(self):
        for field in ('search_acceptance','binary','status','utilities_sha256','system_sha256',
                      'utilities_unchanged','fixtures_unchanged','native_cross_parity'):
            with self.subTest(field=field):
                receipt=copy.deepcopy(self.receipt)
                if field=='search_acceptance':receipt[field]='IN_PROGRESS'
                elif field=='binary':receipt[field]['sha256']='different'
                else:receipt['platforms']['z80pack'][field]=False if field.endswith('unchanged') or field=='native_cross_parity' else ''
                with self.assertRaises(ValueError):
                    validate_search_acceptance(receipt,self.files,'z80pack',b'qualified disk')
        with self.assertRaises(ValueError):
            validate_search_acceptance(self.receipt,self.files,'z80pack',b'changed disk')
        with self.assertRaises(KeyError):
            validate_search_acceptance(self.receipt,self.files,'trs80gp',b'qualified disk')

    def test_stale_prepared_and_corresponding_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);out=root/'build/utilities';out.mkdir(parents=True);(root/'src').mkdir()
            (root/'src/source.mac').write_bytes(b'qualified source')
            (out/'SEARCH.COM').write_bytes(b'program')
            (out/'SEARCH-NATIVE.MAC').write_bytes(b'native source')
            (out/'SEARCH-native.json').write_text(json.dumps({'binary_sha256':sha(b'program'),
                'native_source_sha256':sha(b'native source')}))
            (out/'SEARCH-build-report.json').write_text(json.dumps({'artifact':{'sha256':sha(b'program')},
                'input_record':{'inputs':{'files':{'src/source.mac':sha(b'qualified source')}}}}))
            content=io.BytesIO()
            with tarfile.open(fileobj=content,mode='w:gz') as archive:
                entry=tarfile.TarInfo('BetterCPM-source/src/source.mac');entry.size=len(b'qualified source')
                archive.addfile(entry,io.BytesIO(b'qualified source'))
            archive={'BetterCPM-TED-SOURCE.tar.gz':content.getvalue()}
            self.assertEqual(companions(root,archive)['SEARCH-NATIVE.MAC'],b'native source')
            (root/'src/source.mac').write_bytes(b'unqualified source')
            with self.assertRaises(ValueError):companions(root,archive)
            (root/'src/source.mac').write_bytes(b'qualified source')
            (out/'SEARCH-NATIVE.MAC').write_bytes(b'stale native source')
            with self.assertRaises(ValueError):companions(root,archive)


if __name__=='__main__':
    unittest.main()
