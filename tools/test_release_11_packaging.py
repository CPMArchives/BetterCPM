"""Check the new platform boundary and prevent unqualified image substitution."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
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

    def test_release_binding_rejects_substituted_on_media_carrier(self):
        from release_media_binding import bind
        with tempfile.TemporaryDirectory() as tmp:
            image=Path(tmp)/'system.imd';image.write_bytes(b'image')
            report={'image':image.name,'sha256':sha(b'image'),'target':'trs80m2',
                    'source':{'revision':'a'*40}}
            (image.parent/'report.json').write_text(json.dumps(report))
            with patch('package_integrated_tcap.native_files',return_value={'ANSI.RSX':b'new'.ljust(128,b'\x1a')}):
                with self.assertRaisesRegex(ValueError,'differs'):
                    bind(image,'model2',{'ANSI.RSX':b'old'})
            with patch('package_integrated_tcap.native_files',return_value={'ANSI.RSX':b'old'.ljust(128,b'\x1a')}):
                receipt=bind(image,'model2',{'ANSI.RSX':b'old'})
                self.assertEqual(receipt['image_sha256'],report['sha256'])
            with patch('package_integrated_tcap.native_files',return_value={'ANSI.RSX':b'old'}):
                receipt=bind(image,'model2',{'ANSI.RSX':b'old'})
                self.assertEqual(receipt['image_sha256'],report['sha256'])
            for invalid in (b'old\x1a', b'old'.ljust(128,b'x')):
                with patch('package_integrated_tcap.native_files',return_value={'ANSI.RSX':invalid}):
                    with self.assertRaisesRegex(ValueError,'differs'):
                        bind(image,'model2',{'ANSI.RSX':b'old'})

    def test_three_systems_select_existing_commands_and_own_install_package(self):
        manifest=json.loads((ROOT/'metadata/distribution.json').read_text())['system_disk']
        for target in ('z80pack','trs80gp','trs80m2'):
            rows=[r for r in manifest if target in r['targets'] and r['status']=='implemented']
            names=[r['name'] for r in rows]
            self.assertEqual(len(names),len(set(names)))
            self.assertTrue({'PIP.COM','TYPE.COM','VER.COM','ED.COM','PATH.COM','SYSTEM.SYS'} <= set(names))

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
