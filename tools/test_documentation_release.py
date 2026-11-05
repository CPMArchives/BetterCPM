"""GPL-2.0-or-later. Synthetic packaging fixtures; no real release writes."""
import copy
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from release_documentation import (LOCK_PATH, SELECTION_PATH, ROOT_NAME, FINAL_NAME,
                                  assemble, encoded, sha, load_lock, locked_files,
                                  verify_documentation)


class DocumentationRelease(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.packages = self.root / 'packages'
        self.packages.mkdir()
        rows = []
        for i, name in enumerate(('source', 'system-model4', 'system-cpmsim', 'utilities-model4', 'utilities-cpmsim')):
            payload = ('synthetic locked fixture ' + str(i)).encode()
            filename = name + '.zip'
            (self.packages / filename).write_bytes(payload)
            rows.append({'package': name, 'filename': filename, 'sha256': sha(payload), 'size_bytes': len(payload)})
        self.lock = {'software_source_revision': '1' * 40, 'qualification_merge_revision': '2' * 40, 'packages': rows}
        files = {
            LOCK_PATH: encoded(self.lock),
            'LICENSE': b'fixture first-party terms\n', 'COPYING': b'fixture GPL text\n',
            'NOTICE': b'fixture attribution\n', 'LICENSES/CC-BY-4.0.txt': b'fixture CC text\n',
            'docs/LICENSING.md': b'# Licensing\n', 'docs/LICENSING-INVENTORY.md': b'# Inventory\n',
            'packaging/1.0/DOCUMENTATION-CONTENTS.md': b'# Contents\n[User](docs/user/users_guide.md)\n',
            'packaging/1.0/README-Documentation.txt': b'Synthetic fixture only\n'}
        manuals = ['docs/user/users_guide.md', 'docs/user/command_reference.md',
                   'docs/programmers/programmers_guide.md', 'docs/porting/practical_porting_guide.md']
        for name in manuals:
            files[name] = b'# Guide\n[Local](#guide)\n[Source](../../src/example.mac)\n'
        selected = manuals + ['docs/LICENSING.md', 'docs/LICENSING-INVENTORY.md', LOCK_PATH]
        files[SELECTION_PATH] = encoded({'files': selected, 'manuals': manuals, 'license_records': [], 'publication_tools': []})
        for n, data in files.items():
            p = self.repo / n
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        for args in (['init', '-q'], ['add', '.'], ['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Synthetic documentation fixture']):
            subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True)
        self.revision = subprocess.check_output(['git', '-C', str(self.repo), 'rev-parse', 'HEAD']).decode().strip()
        self.lock, self.raw = load_lock(self.repo)

    def build(self, preview=False):
        p = self.packages / ('documentation-review.zip' if preview else FINAL_NAME)
        result = assemble(self.repo, p, preview=preview, revision=None if preview else self.revision)
        return p, result

    def mutate(self, path, change, restamp=False):
        with zipfile.ZipFile(path) as z:
            files = {n.split('/', 1)[1]: z.read(n) for n in z.namelist()}
        change(files)
        if restamp:
            rec = json.loads(files['RELEASE.json'])
            rec['files'] = {n: sha(d) for n, d in files.items() if n not in ('RELEASE.json', 'SHA256SUMS.txt')}
            files['RELEASE.json'] = encoded(rec)
            files['SHA256SUMS.txt'] = ''.join(sha(d) + '  ' + n + '\n' for n, d in sorted(files.items()) if n != 'SHA256SUMS.txt').encode()
        new = self.root / 'mutated.zip'
        with zipfile.ZipFile(new, 'w') as z:
            for n, d in files.items():
                z.writestr(ROOT_NAME + '/' + n, d)
        return new

    def test_committed_split_collection_and_cli(self):
        before = {p.name: p.read_bytes() for p in self.packages.iterdir()}
        path, result = self.build()
        self.assertEqual(result['documentation_revision'], self.revision)
        self.assertEqual(len(locked_files(self.packages, self.lock)), 5)
        report = self.root / 'report.json'
        proc = subprocess.run(['python3', str(Path(__file__).with_name('check_release_package_lock.py')),
                               str(self.packages), '--repository', str(self.repo), '--output', str(report)], capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(report.read_text())['status'], 'SPLIT_IDENTITIES_STATIC_CHECKS_PASS')
        self.assertTrue(all((self.packages / n).read_bytes() == d for n, d in before.items()))
        with zipfile.ZipFile(path) as z:
            guide = z.read(ROOT_NAME + '/docs/user/users_guide.md').decode()
            self.assertIn('/blob/' + '1' * 40 + '/src/example.mac', guide)
            self.assertEqual(z.read(ROOT_NAME + '/licenses/BetterCPM/NOTICE'), b'fixture attribution\n')

    def test_preview_cannot_satisfy_final(self):
        path, result = self.build(True)
        self.assertIsNone(result['documentation_revision'])
        with self.assertRaisesRegex(ValueError, 'Preview'):
            verify_documentation(path, self.lock, self.raw, repo=self.repo)
        with self.assertRaisesRegex(ValueError, 'Preview requires'):
            assemble(self.repo, self.root / FINAL_NAME, preview=True)

    def test_missing_and_same_size_changed_locked_file(self):
        p = self.packages / self.lock['packages'][0]['filename']
        data = p.read_bytes()
        p.write_bytes(bytes([data[0] ^ 1]) + data[1:])
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            locked_files(self.packages, self.lock)
        p.unlink()
        with self.assertRaisesRegex(ValueError, 'Missing'):
            locked_files(self.packages, self.lock)

    def test_tampered_member(self):
        path, _ = self.build(True)
        new = self.mutate(path, lambda f: f.update({'docs/user/users_guide.md': b'changed'}))
        with self.assertRaisesRegex(ValueError, 'checksum'):
            verify_documentation(new, self.lock, self.raw, allow_preview=True)

    def test_unsafe_archive_member(self):
        path, _ = self.build(True)
        new = self.mutate(path, lambda f: f.update({'../escape': b'x'}))
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            verify_documentation(new, self.lock, self.raw, allow_preview=True)

    def test_missing_notice_even_with_new_checksums(self):
        path, _ = self.build(True)
        new = self.mutate(path, lambda f: f.pop('licenses/BetterCPM/NOTICE'), restamp=True)
        with self.assertRaisesRegex(ValueError, 'Missing required'):
            verify_documentation(new, self.lock, self.raw, allow_preview=True)

    def test_false_commit_with_self_consistent_checksums(self):
        path, _ = self.build(True)
        def change(files):
            for name in ('RELEASE.json', 'SOURCE-IDENTITY.json'):
                j = json.loads(files[name])
                j['documentation_revision'] = '3' * 40
                j['documentation_source']['kind'] = 'commit'
                j['documentation_source']['revision'] = '3' * 40
                if name == 'RELEASE.json':
                    j['status'] = 'DOCUMENTATION_CANDIDATE_NOT_ACCEPTED'
                files[name] = encoded(j)
        new = self.mutate(path, change, restamp=True)
        with self.assertRaises(subprocess.CalledProcessError):
            verify_documentation(new, self.lock, self.raw, repo=self.repo)

    def test_restamped_prose_must_match_actual_commit(self):
        path, _ = self.build()
        new = self.mutate(path, lambda f: f.update({'docs/user/users_guide.md': b'# Guide\nFalse instructions\n'}), restamp=True)
        with self.assertRaisesRegex(ValueError, 'differs from actual commit'):
            verify_documentation(new, self.lock, self.raw, repo=self.repo)

    def test_output_never_overwritten(self):
        path, _ = self.build(True)
        data = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'already exists'):
            assemble(self.repo, path, preview=True)
        self.assertEqual(path.read_bytes(), data)


if __name__ == '__main__':
    unittest.main()
