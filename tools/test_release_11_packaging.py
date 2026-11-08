"""Check the new platform boundary and prevent unqualified image substitution."""
import json
from pathlib import Path
import tempfile
import unittest
from package_release_candidates import ROOT, read_report, sha, package_license_files, documentation_members
from release_source import source_files


class Release11(unittest.TestCase):
    def test_eight_assets_have_readmes_and_notices(self):
        layout=json.loads((ROOT/'metadata/release-assets-1.1.json').read_text())
        self.assertEqual({a['id'] for a in layout['assets']},
                         {kind+'-'+target for kind in ('system','utilities')
                          for target in ('cpmsim','model4','model2')}|{'source','documentation'})
        tracked=source_files(ROOT)
        for asset in layout['assets']:
            self.assertIn(asset['readme_template'],tracked)
            self.assertIn('THIRD-PARTY-NOTICES.txt',package_license_files(tracked,asset['id'],'1.1'))
        files,evidence=documentation_members(tracked,'a'*40,'1.1')
        self.assertEqual(len(evidence['manuals']),4)
        self.assertTrue(any('TCAP-Direct-ABI' in n for n in files))

    def test_model2_requires_native_gates_and_exact_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);data=b'image';(folder/'system.imd').write_bytes(data)
            report={'target':'trs80m2','source':{'revision':'a'*40},'image':'system.imd',
                    'sha256':sha(data),'validation':{'boot':{'status':'PASS'},'inventory':{
                        key:'PASS' for key in ('exact_membership','independent_record_readback','allocation')}}}
            def save():(folder/'report.json').write_text(json.dumps(report))
            save();self.assertEqual(read_report(folder,'a'*40)[1],data)
            report['validation']['boot']['status']='UNVERIFIED';save()
            with self.assertRaisesRegex(ValueError,'gates'):read_report(folder,'a'*40)
            report['validation']['boot']['status']='PASS';save()
            (folder/'system.imd').write_bytes(b'substituted')
            with self.assertRaisesRegex(ValueError,'receipt'):read_report(folder,'a'*40)


if __name__=='__main__':unittest.main()
