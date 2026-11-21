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

    def test_model4_install_package_keeps_distribution_startup(self):
        from prepare_release_13 import align_model4_install_startup
        from startup_record import build, parse
        from system_layout import LAYOUT
        package=bytearray(20608);package[:6]=b'BCSY\x01\x01'
        package[256:512]=build(system_base=LAYOUT['SYSTEM'])
        # Non-BCST package content must remain byte-identical.
        package[512:]=bytes((i*7&255 for i in range(len(package)-512)))
        component={'name':'SYSTEM.SYS','user':0,'artifact':'native-reference'}
        files=[(component,bytes(package)),({'name':'OTHER.COM','user':0},b'unchanged')]
        changed=align_model4_install_startup(files,'SUBMIT STARTUP')
        actual=changed[0][1]
        self.assertEqual(parse(actual[256:512],system_base=LAYOUT['SYSTEM']),'SUBMIT STARTUP')
        self.assertEqual(actual[:256],package[:256]);self.assertEqual(actual[512:],package[512:])
        self.assertEqual(changed[1],files[1])
        self.assertEqual(package[256:512],build(system_base=LAYOUT['SYSTEM']))
        self.assertEqual(changed[0][0]['source_artifact_sha256'],sha(bytes(package)))
        self.assertEqual(parse(align_model4_install_startup(files,'')[0][1][256:512],
                               system_base=LAYOUT['SYSTEM']),'')
        with self.assertRaises(ValueError):align_model4_install_startup([],'')
        with self.assertRaises(ValueError):align_model4_install_startup([(component,b'bad')],'')

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
