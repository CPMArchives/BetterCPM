"""GPL-2.0-or-later. Reader layout, link migration and actual-source provenance regression tests."""
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from release_documentation import (MANUALS, MANIFEST, IDENTITY, SUMS, ROOT_NAME, FINAL_NAME,
                                  SELECTION_PATH, SOFTWARE_PATH, assemble, encoded, sha,
                                  verify_documentation, verify_software)


class DocumentationRelease(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        self.packages = self.root / 'packages'
        self.packages.mkdir()
        rows = []
        for name in ('source', 'system-model4', 'system-cpmsim', 'utilities-model4', 'utilities-cpmsim', 'evidence'):
            data = name.encode()
            (self.packages / (name + '.zip')).write_bytes(data)
            rows.append({'package': name, 'filename': name + '.zip', 'size_bytes': len(data), 'sha256': sha(data)})
        self.baseline = {'software_source_revision': '1' * 40, 'qualification_merge_revision': '2' * 40, 'packages': rows}
        manuals = ['docs/manuals/' + n for n in MANUALS]
        files = {SELECTION_PATH: encoded({'manuals': manuals, 'references': ['docs/programmers/API.md'], 'license_records': []}),
                 SOFTWARE_PATH: encoded(self.baseline), 'docs/programmers/API.md': b'# API\n[User](../manuals/Users-Guide.md#guide)\n',
                 'packaging/1.0/README-Documentation.md': b'# Start\n[User](../../docs/manuals/Users-Guide.md#guide)\n',
                 'LICENSE': b'fixture license\n', 'COPYING': b'fixture GPL\n', 'NOTICE': b'fixture credit\n', 'LICENSES/CC-BY-4.0.txt': b'fixture CC\n'}
        for n in manuals:
            files[n] = b'# Guide\n[API](../programmers/API.md#api)\n[Commands](Command-and-Utilities-Reference.md#guide)\n[Source](../../src/example.mac)\n'
        for n, d in files.items():
            p = self.repo / n
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(d)
        self.commit()

    def commit(self):
        for args in (['add', '.'], ['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Fixture', '--allow-empty']):
            subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True)
        self.rev = subprocess.check_output(['git', '-C', str(self.repo), 'rev-parse', 'HEAD']).decode().strip()

    def build(self, folder='first', preview=False):
        path = self.root / folder / ('layout-review.zip' if preview else FINAL_NAME)
        result = assemble(self.repo, path, preview=preview, revision=None if preview else self.rev)
        return path, result

    def mutate(self, path, change, restamp=False):
        with zipfile.ZipFile(path) as z:
            files = {n.split('/', 1)[1]: z.read(n) for n in z.namelist()}
        change(files)
        if restamp:
            files[SUMS] = ''.join(sha(d) + '  ' + n + '\n' for n, d in sorted(files.items()) if n != SUMS).encode()
        new = self.root / 'changed.zip'
        with zipfile.ZipFile(new, 'w') as z:
            for n, d in files.items():
                z.writestr(ROOT_NAME + '/' + n, d)
        return new

    def test_four_manual_layout_and_remapped_links(self):
        path, result = self.build()
        self.assertEqual(result['documentation_revision'], self.rev)
        with zipfile.ZipFile(path) as z:
            files = {n.split('/', 1)[1]: z.read(n) for n in z.namelist()}
        self.assertEqual({n for n in files if '/' not in n}, {'README.md', *MANUALS})
        self.assertIn(b'(Supporting-Reference/programmers/API.md#api)', files['Users-Guide.md'])
        self.assertIn(b'(../../Users-Guide.md#guide)', files['Supporting-Reference/programmers/API.md'])
        self.assertIn(b'/blob/' + b'1' * 40 + b'/src/example.mac', files['Users-Guide.md'])
        self.assertEqual(files['Licenses/BetterCPM/NOTICE'], b'fixture credit\n')
        self.assertFalse(any('locator' in n or 'utilities_manual' in n for n in files))

    def test_reproducible_and_ignores_uncommitted_changes(self):
        first, _ = self.build()
        (self.repo / 'docs/manuals/Users-Guide.md').write_text('uncommitted')
        second, _ = self.build('second')
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_preview_not_final(self):
        path, _ = self.build(preview=True)
        with self.assertRaisesRegex(ValueError, 'Preview'):
            verify_documentation(path, repo=self.repo)

    def test_restamped_prose_cannot_forge_commit(self):
        path, _ = self.build()
        new = self.mutate(path, lambda f: f.update({'Users-Guide.md': b'false prose'}), restamp=True)
        with self.assertRaisesRegex(ValueError, 'actual documentation source'):
            verify_documentation(new, repo=self.repo)

    def test_unsafe_path(self):
        path, _ = self.build()
        new = self.mutate(path, lambda f: f.update({'../escape': b'x'}))
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            verify_documentation(new, repo=self.repo)

    def test_missing_notice(self):
        path, _ = self.build()
        new = self.mutate(path, lambda f: f.pop('Licenses/BetterCPM/NOTICE'), restamp=True)
        with self.assertRaisesRegex(ValueError, 'actual documentation source'):
            verify_documentation(new, repo=self.repo)

    def test_broken_local_anchor(self):
        p = self.repo / 'docs/manuals/Users-Guide.md'
        p.write_text('# Guide\n[Broken](../programmers/API.md#absent)\n')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'anchor'):
            self.build()

    def test_no_overwrite(self):
        path, _ = self.build()
        with self.assertRaisesRegex(ValueError, 'already exists'):
            assemble(self.repo, path, revision=self.rev)

    def test_changed_same_size_software_rejected(self):
        verify_software(self.packages, self.baseline)
        p = self.packages / 'source.zip'
        p.write_bytes(b'X' * p.stat().st_size)
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            verify_software(self.packages, self.baseline)

    def test_missing_software_rejected(self):
        (self.packages / 'source.zip').unlink()
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            verify_software(self.packages, self.baseline)


if __name__ == '__main__':
    unittest.main()
