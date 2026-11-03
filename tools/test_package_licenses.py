"""Check licence scope and notice delivery in each independent package."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from package_release_candidates import ROOT, package_license_files, write_package


class PackageNotices(unittest.TestCase):
    def test_independent_downloads_carry_matching_terms_and_notices(self):
        assets = json.loads((ROOT/'metadata/release-assets.json').read_text())['assets']
        inputs = ('LICENSE', 'LICENSES/CC-BY-4.0.txt', 'packaging/1.0/third-party-notices.json')
        tracked = {path: (ROOT/path).read_bytes() for path in inputs}
        package_ids = {asset['id'] for asset in assets}
        for row in json.loads(tracked[inputs[2]]):
            self.assertTrue(set(row['packages']) <= package_ids)
        with tempfile.TemporaryDirectory() as tmp:
            for asset in assets:
                package = asset['id']
                with self.subTest(package=package):
                    files = package_license_files(tracked, package)
                    path = Path(tmp)/asset['filename']
                    write_package(path, package, files, {'package': package})
                    with zipfile.ZipFile(path) as archive:
                        self.assertEqual(archive.read(package+'/LICENSE'), tracked['LICENSE'])
                        self.assertEqual(archive.read(package+'/licenses/CC-BY-4.0.txt'), tracked[inputs[1]])
                        notice = archive.read(package+'/THIRD-PARTY-NOTICES.txt').decode()
                        self.assertIn('CC BY 4.0', notice)
                        self.assertEqual('Montezuma Micro disk-format data' in notice,
                                         package != 'documentation')
                        self.assertEqual('Hector Peraza TED adaptation' in notice,
                                         package.startswith('utilities-') or package == 'source')
                        self.assertEqual('z80pack and the cpmsim support kit' in notice,
                                         package in ('system-cpmsim', 'source'))


if __name__ == '__main__':
    unittest.main()
