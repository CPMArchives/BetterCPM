#!/usr/bin/env python3
"""Reject tool/source/license substitutions before Utilities publication."""
from pathlib import Path
import shutil
import tempfile
import unittest
import copy
import hashlib
from toolchain_distribution import companions, validate_acceptance

ROOT = Path(__file__).resolve().parents[1]


class ToolchainGuards(unittest.TestCase):
    def test_acceptance_binding(self):
        sha = lambda b: hashlib.sha256(b).hexdigest()
        files = {'ZSM4.COM':b'assembler', 'LINK.COM':b'linker'}
        accompanying = {'source':b'complete source'}
        image = b'exact disk'
        receipt = {'status':'PASS','tools_sha256':{n:sha(d) for n,d in files.items()},
                   'companions_sha256':{n:sha(d) for n,d in accompanying.items()},
                   'platforms':{'z80pack':{'status':'PASS','system_audit_status':'PASS',
                     'utilities_sha256':sha(image),'cases':{n:{'status':'PASS'} for n in
                     ('PROBE','SQ','USQ','CR','UNCR','LZH','UNLZH')}}}}
        validate_acceptance(receipt,files,'z80pack',image,accompanying)
        for field in ('status','audit','case','media','tool','source'):
            damaged = copy.deepcopy(receipt)
            if field == 'status': damaged['status']='IN_PROGRESS'
            if field == 'audit': damaged['platforms']['z80pack']['system_audit_status']='FAIL'
            if field == 'case': del damaged['platforms']['z80pack']['cases']['SQ']
            if field == 'media': damaged['platforms']['z80pack']['utilities_sha256']='wrong'
            if field == 'tool': damaged['tools_sha256']['LINK.COM']='wrong'
            if field == 'source': damaged['companions_sha256']['source']='wrong'
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_acceptance(damaged,files,'z80pack',image,accompanying)

    def test_complete_package(self):
        self.assertIn('ZSM4-SOURCE.tar.gz', companions(ROOT))

    def test_substitutions(self):
        for name in ('third_party/zsm4/ZSM4.COM',
                     'third_party/zsm4/source.tar.gz',
                     'third_party/dri-link/LINK.COM',
                     'third_party/dri-link/permission.html',
                     'src/distribution/ZSM4COPY.TXT',
                     'src/distribution/LINKCOPY.TXT'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                for folder in ('third_party/zsm4', 'third_party/dri-link', 'src/distribution'):
                    shutil.copytree(ROOT / folder, root / folder)
                path = root / name
                path.write_bytes(b'changed' + path.read_bytes()[7:])
                with self.assertRaises(ValueError):
                    companions(root)

    def test_missing_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / 'third_party/zsm4', root / 'third_party/zsm4')
            (root / 'third_party/zsm4/source.tar.gz').unlink()
            with self.assertRaises(FileNotFoundError):
                companions(root)


if __name__ == '__main__':
    unittest.main()
