"""Check licence scope and notice delivery in each independent package."""
import gzip
import io
import json
import tarfile
from pathlib import Path
import tempfile
import unittest
import zipfile

from package_release_candidates import ROOT, package_license_files, write_package


from release_source import forbidden_digests, source_files, verify_members


class PackageNotices(unittest.TestCase):
    def test_release_selection_retains_catalogue_inputs_and_own_implementations(self):
        selected = source_files(ROOT)
        refs = {name.split('/')[-1] for name in selected if name.startswith('third_party/montezuma/')}
        self.assertEqual(refs, {'README.md', 'DISK.FDF', 'DISK-INT.FDF', 'CONFIG-extraction-manifest.json'})
        self.assertNotIn('docs/engineering/DISK-FORMAT-MM-CONFIG-ANALYSIS.md', selected)
        for name in ('metadata/DISK.FDF', 'src/utilities/config.mac', 'src/utilities/dup.mac'):
            self.assertIn(name, selected)

    def test_stale_nested_companion_rejected_even_with_renamed_binary(self):
        forbidden = forbidden_digests(ROOT)
        data = (ROOT/'third_party/montezuma/MDIR.COM').read_bytes()
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode='w') as archive:
            member = tarfile.TarInfo('renamed.bin')
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
        outer = io.BytesIO()
        with zipfile.ZipFile(outer, 'w') as archive:
            archive.writestr('old-source.tar.gz', gzip.compress(buf.getvalue()))
        with self.assertRaisesRegex(ValueError, 'old-source.tar.gz.*renamed.bin'):
            verify_members({'nested.zip': outer.getvalue()}, forbidden)
        with self.assertRaisesRegex(ValueError, 'new.lst'):
            verify_members({'clean.txt': b'x', 'src/third_party/montezuma/new.lst': b'x'}, forbidden)

    def test_independent_downloads_carry_matching_terms_and_notices(self):
        assets = json.loads((ROOT/'metadata/release-assets.json').read_text())['assets']
        inputs = ('LICENSE', 'LICENSES/CC-BY-4.0.txt', 'packaging/1.0/third-party-notices.json', 'COPYING', 'NOTICE', 'docs/LICENSING.md')
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
                        self.assertEqual(archive.read(package+'/licenses/BetterCPM/LICENSE'), tracked['LICENSE'])
                        self.assertEqual(archive.read(package+'/licenses/BetterCPM/CC-BY-4.0.txt'), tracked[inputs[1]])
                        notice = archive.read(package+'/THIRD-PARTY-NOTICES.txt').decode()
                        self.assertIn('CC BY 4.0', notice)
                        self.assertIn('GPL-2.0-or-later', notice)
                        self.assertNotIn('MIT (LICENSE)', notice)
                        for name in ('COPYING', 'NOTICE'):
                            self.assertEqual(archive.read(package+'/licenses/BetterCPM/'+name), tracked[name])
                        self.assertEqual(archive.read(package+'/docs/LICENSING.md'), tracked['docs/LICENSING.md'])
                        self.assertEqual('Montezuma Micro disk-format data' in notice,
                                         package != 'documentation')
                        self.assertEqual('Hector Peraza TED adaptation' in notice,
                                         package.startswith('utilities-') or package == 'source')
                        self.assertEqual('z80pack and the cpmsim support kit' in notice,
                                         package in ('system-cpmsim', 'source'))


if __name__ == '__main__':
    unittest.main()
