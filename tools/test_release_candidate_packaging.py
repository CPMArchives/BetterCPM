"""Release integrity boundaries and extracted-source identity regression checks."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile
from build_qualified_cpmsim import project_revision
from build_qualified_cpmsim import source_archive, verified_sources
from package_release_candidates import checked_name, encoded, read_report, sha, write_package, utilities_members, project_license_files


class ReleaseCandidateTests(unittest.TestCase):
    def test_utilities_platform_archives_keep_only_matching_media_and_receipts(self):
        images={'primary.dsk':'cpmsim','companion.dsk':'cpmsim',
                'primary.dmk':'Model4','companion.dmk':'Model4'}
        sums={name:name.encode() for name in images}
        sums.update({name+'.json':encoded({'image':name}) for name in images})
        sums['shared-source.tar.gz']=b'corresponding source'
        sums['NOTICE.txt']=b'notice'
        reports={name:{'image':name} for name in images}
        inventory={'status':'PASS','platforms':{'z80pack':{'files':26},'trs80gp':{'files':26}}}
        for platform,target in [('cpmsim','z80pack'),('Model4','trs80gp')]:
            with self.subTest(platform=platform),tempfile.TemporaryDirectory() as tmp:
                files,evidence=utilities_members(platform,sums,images,reports,inventory)
                selected={name for name,owner in images.items() if owner==platform}
                self.assertEqual({n.split('/')[-1] for n in files if n.startswith('images/')},selected)
                for name in images:
                    self.assertEqual('evidence/'+name+'.json' in files,name in selected)
                self.assertEqual(files['source/shared-source.tar.gz'],sums['shared-source.tar.gz'])
                self.assertEqual(files['source/NOTICE.txt'],sums['NOTICE.txt'])
                self.assertEqual(set(evidence['images']),selected)
                self.assertEqual(set(evidence['independent_inventory']['platforms']),{target})
                path=Path(tmp)/'utilities.zip';write_package(path,'utilities',files,{'platform':platform})
                with zipfile.ZipFile(path) as z:
                    actual={n.rsplit('/',1)[-1] for n in z.namelist() if '/images/' in n}
                    self.assertEqual(actual,selected)

    def test_utilities_requires_both_primary_and_companion(self):
        with self.assertRaises(ValueError):
            utilities_members('cpmsim',{'one.dsk':b'x'},{'one.dsk':'cpmsim'},
                              {'one.dsk':{}},{'platforms':{'z80pack':{}}})

    def test_offline_archive_uses_pinned_files_and_checks_membership(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo=root/'upstream';repo.mkdir()
            subprocess.run(['git','init','-q',str(repo)],check=True)
            (repo/'source.c').write_text('pinned source\n')
            (repo/'historical.dsk').write_bytes(b'unrelated media')
            subprocess.run(['git','-C',str(repo),'add','.'],check=True)
            subprocess.run(['git','-C',str(repo),'-c','user.name=Test','-c',
                            'user.email=test@example.com','commit','-qm','pin'],check=True)
            pin=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD']).decode().strip()
            (repo/'source.c').write_text('later source\n')
            subprocess.run(['git','-C',str(repo),'-c','user.name=Test','-c',
                            'user.email=test@example.com','commit','-qam','later'],check=True)
            refs=subprocess.check_output(['git','-C',str(repo),'show-ref'])
            expected = {'source.c': sha(b'pinned source\n')}
            payload = source_archive(repo, pin, expected)
            self.assertEqual(verified_sources(payload, expected), {'source.c': b'pinned source\n'})
            self.assertEqual(refs, subprocess.check_output(['git', '-C', str(repo), 'show-ref']))
            for wrong in ({}, {'source.c': sha(b'changed')}, {**expected, 'missing': sha(b'x')}):
                with self.assertRaises(ValueError):
                    verified_sources(payload, wrong)

    def test_rejects_image_drift_and_wrong_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'system.dsk').write_bytes(b'original')
            report={'target':'z80pack','source':{'revision':'a'*40},'image':'system.dsk','sha256':sha(b'original'),
                    'validation':dict.fromkeys(('filesystem','file_integrity','config_fingerprint'),'PASS')}
            (root/'report.json').write_bytes(encoded(report))
            read_report(root,'a'*40)
            with self.assertRaises(ValueError):read_report(root,'b'*40)
            (root/'system.dsk').write_bytes(b'changed')
            with self.assertRaises(ValueError):read_report(root,'a'*40)

    def test_rejects_missing_construction_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'system.dsk').write_bytes(b'x')
            report={'target':'z80pack','source':{'revision':'a'*40},'image':'system.dsk','sha256':sha(b'x'),
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

    def test_project_terms_survive_independent_archive_readback(self):
        root=Path(__file__).resolve().parents[1]
        tracked={n:(root/n).read_bytes() for n in ('LICENSE','COPYING','NOTICE','LICENSES/CC-BY-4.0.txt','docs/LICENSING.md')}
        files=project_license_files(tracked)
        for asset in json.loads((root/'metadata/release-assets.json').read_text())['assets']:
            with self.subTest(asset=asset['id']),tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'candidate.zip'
                write_package(path,'candidate',files,{'status':'CANDIDATE'})
                with zipfile.ZipFile(path) as z:
                    for name,data in tracked.items():
                        target={'LICENSES/CC-BY-4.0.txt':'licenses/BetterCPM/CC-BY-4.0.txt',
                                'docs/LICENSING.md':'docs/LICENSING.md'}.get(name,'licenses/BetterCPM/'+name)
                        self.assertEqual(z.read('candidate/'+target),data)
        self.assertIn(b'CC-BY-4.0',tracked['LICENSE'])
        self.assertIn(b'GPL-2.0-or-later',tracked['docs/LICENSING.md'])
        with self.assertRaises(KeyError):project_license_files({'LICENSE':b'incomplete'})

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
