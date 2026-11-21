"""1.3 candidate identity, selection and strict pending-policy regression."""
import json
from pathlib import Path
import tempfile
import unittest
from package_release_candidates import ROOT,source_files,documentation_members,read_report,sha


class Release13(unittest.TestCase):
    def test_candidate_identity_and_eight_assets(self):
        package=json.loads((ROOT/'metadata/release-package.json').read_text())
        self.assertEqual(package['version'],'1.3')
        self.assertIn('pending',package['status'])
        layout=json.loads((ROOT/'metadata/release-assets-1.3.json').read_text())
        self.assertIsNone(layout['accepted_commit'])
        self.assertEqual(len(layout['assets']),8)
        tracked=source_files()
        for asset in layout['assets']:
            self.assertIn('1.3',asset['filename'])
            self.assertIn(asset['readme_template'],tracked)
        files,evidence=documentation_members(tracked,'a'*40,'1.3')
        self.assertEqual(len(evidence['manuals']),4)
        self.assertGreater(evidence['local_links_checked'],0)
        self.assertTrue(any('RELEASE-NOTES-1.3' in n for n in files))

    def test_smoke_policy_cannot_reuse_12(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/'system.imd').write_bytes(b'image')
            row={'source':{'revision':'a'*40},'target':'trs80m2','image':'system.imd',
                 'sha256':sha(b'image'),'release_policy':'1.3-focused',
                 'validation':{'boot':{'status':'PENDING_SMOKE'},'inventory':dict.fromkeys(
                    ('exact_membership','independent_record_readback','allocation'),'PASS')}}
            def save():(folder/'report.json').write_text(json.dumps(row))
            save()
            with self.assertRaises(ValueError):read_report(folder,'a'*40)
            with self.assertRaises(ValueError):read_report(folder,'a'*40,allow_pending_smoke=True)
            read_report(folder,'a'*40,allow_pending_smoke=True,pending_policy='1.3-focused')
            row['release_policy']='1.2-focused';save()
            with self.assertRaises(ValueError):read_report(folder,'a'*40,allow_pending_smoke=True,pending_policy='1.3-focused')
            row['release_policy']='1.3-focused';row['validation']['inventory']['allocation']='FAIL';save()
            with self.assertRaises(ValueError):read_report(folder,'a'*40,allow_pending_smoke=True,pending_policy='1.3-focused')


if __name__=='__main__':unittest.main()
