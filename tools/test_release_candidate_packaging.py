"""Release integrity boundaries and extracted-source identity regression checks."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile
from build_qualified_cpmsim import project_revision
from package_release_candidates import checked_name, encoded, read_report, sha, write_package


class ReleaseCandidateTests(unittest.TestCase):
    def test_rejects_image_drift_and_wrong_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'system.dsk').write_bytes(b'original')
            report={'source':{'revision':'a'*40},'image':'system.dsk','sha256':sha(b'original'),
                    'validation':dict.fromkeys(('filesystem','file_integrity','config_fingerprint'),'PASS')}
            (root/'report.json').write_bytes(encoded(report))
            read_report(root,'a'*40)
            with self.assertRaises(ValueError):read_report(root,'b'*40)
            (root/'system.dsk').write_bytes(b'changed')
            with self.assertRaises(ValueError):read_report(root,'a'*40)

    def test_rejects_missing_construction_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'system.dsk').write_bytes(b'x')
            report={'source':{'revision':'a'*40},'image':'system.dsk','sha256':sha(b'x'),
                    'validation':{'filesystem':'PASS'}}
            (root/'report.json').write_bytes(encoded(report))
            with self.assertRaises(ValueError):read_report(root,'a'*40)

    def test_archive_checksums_readback_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'candidate.zip';record={'status':'CANDIDATE'}
            result=write_package(p,'candidate',{'a.txt':b'payload'},record)
            self.assertEqual(result['sha256'],sha(p.read_bytes()))
            with zipfile.ZipFile(p) as z:
                self.assertEqual(z.read('candidate/a.txt'),b'payload')
                self.assertIn(sha(b'payload').encode(),z.read('candidate/SHA256SUMS.txt'))
                self.assertNotIn(b'SHA256SUMS.txt',z.read('candidate/SHA256SUMS.txt'))
            with self.assertRaises(ValueError):write_package(p,'candidate',{},record)

    def test_rejects_escaping_names(self):
        for name in ('../outside','/absolute','nested/../../outside','a\\b'):
            with self.subTest(name=name),self.assertRaises(ValueError):checked_name(name)

    def test_extracted_source_ignores_parent_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent=Path(tmp);subprocess.run(['git','init','-q',str(parent)],check=True)
            root=parent/'extracted';root.mkdir()
            (root/'SOURCE-IDENTITY.json').write_text(json.dumps({'source_commit':'a'*40}))
            self.assertEqual(project_revision(root),'a'*40)
            (root/'SOURCE-IDENTITY.json').write_text(json.dumps({'source_commit':'invalid'}))
            with self.assertRaises(ValueError):project_revision(root)


if __name__=='__main__':unittest.main()
