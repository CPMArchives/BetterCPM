"""Focused 1.2 packaging contract and honest pending-smoke boundaries."""
import json
from pathlib import Path
import tempfile
import unittest
from package_release_candidates import (ROOT, source_files, documentation_members,
    lean_utilities, read_report, sha)


class Release12(unittest.TestCase):
    def test_eight_assets_and_documentation_links(self):
        tracked = source_files()
        layout = json.loads((ROOT/'metadata/release-assets-1.2.json').read_text())
        self.assertEqual(len(layout['assets']), 8)
        for asset in layout['assets']:
            self.assertIn(asset['readme_template'], tracked)
            self.assertIn('1.2', asset['filename'])
        files, evidence = documentation_members(tracked, 'a'*40, '1.2')
        self.assertEqual(len(evidence['manuals']), 4)
        self.assertGreater(evidence['local_links_checked'], 0)
        self.assertTrue(any('NDR-1.2' in n for n in files))

    def test_pending_model2_smoke_requires_explicit_12_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder/'system.imd').write_bytes(b'image')
            row = {'source':{'revision':'a'*40}, 'target':'trs80m2',
                   'image':'system.imd', 'sha256':sha(b'image'),
                   'release_policy':'1.2-focused',
                   'validation':{'boot':{'status':'PENDING_SMOKE'},
                      'inventory':dict.fromkeys(('exact_membership',
                         'independent_record_readback','allocation'),'PASS')}}
            def save():
                (folder/'report.json').write_text(json.dumps(row))
            save()
            with self.assertRaises(ValueError):
                read_report(folder, 'a'*40)
            read_report(folder, 'a'*40, allow_pending_smoke=True)
            del row['release_policy']
            save()
            with self.assertRaises(ValueError):
                read_report(folder, 'a'*40, allow_pending_smoke=True)
            row['release_policy'] = '1.2-focused'
            row['validation']['inventory']['allocation'] = 'FAIL'
            save()
            with self.assertRaises(ValueError):
                read_report(folder, 'a'*40, allow_pending_smoke=True)

    def test_matching_source_offer(self):
        files, evidence = lean_utilities({'THIRD-PARTY-NOTICES.txt':b'notices'},
                                        {'images':{}}, 'a'*40, '1.2')
        offer = json.loads(files['SOURCE-DOWNLOAD.json'])
        self.assertEqual(offer['filename'], 'BetterCPM-1.2-Source.zip')
        self.assertIn('/v1.2/', offer['url'])


if __name__ == '__main__':
    unittest.main()
