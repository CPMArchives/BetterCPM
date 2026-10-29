"""Release integrity boundaries and extracted-source identity regression checks."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile
from build_qualified_cpmsim import project_revision
from package_release_candidates import checked_name, encoded, read_report, sha, write_package, upstream_bundle, utilities_members


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

    def test_offline_bundle_restores_exact_unreferenced_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo=root/'upstream';repo.mkdir()
            subprocess.run(['git','init','-q',str(repo)],check=True)
            (repo/'source.c').write_text('pinned source\n')
            subprocess.run(['git','-C',str(repo),'add','.'],check=True)
            subprocess.run(['git','-C',str(repo),'-c','user.name=Test','-c',
                            'user.email=test@example.com','commit','-qm','pin'],check=True)
            pin=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD']).decode().strip()
            (repo/'source.c').write_text('later source\n')
            subprocess.run(['git','-C',str(repo),'-c','user.name=Test','-c',
                            'user.email=test@example.com','commit','-qam','later'],check=True)
            refs=subprocess.check_output(['git','-C',str(repo),'show-ref'])
            bundle=root/'source.bundle';upstream_bundle(repo,pin,bundle)
            self.assertEqual(refs,subprocess.check_output(['git','-C',str(repo),'show-ref']))
            restored=root/'offline';subprocess.run(['git','init','-q',str(restored)],check=True)
            subprocess.run(['git','-C',str(restored),'fetch',str(bundle),
                            'refs/heads/bettercpm-pinned'],check=True,capture_output=True)
            self.assertEqual(subprocess.check_output(['git','-C',str(restored),'show',
                             pin+':source.c']),b'pinned source\n')

    def test_rejects_image_drift_and_wrong_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'system.dsk').write_bytes(b'original')
            report={'source':{'revision':'a'*40},'image':'system.dsk','sha256':sha(b'original'),
                    'validation':dict.fromkeys(('filesystem','file_integrity','config_fingerprint'),'PASS')}
            (root/'report.json').write_bytes(encoded(report))
            read_report(root,'a'*40)
            with self.assertRaises(ValueError):read_report(root,'b'*40)
            (root/'system.dsk').write_bytes(b'changed')
            with self.assertRaises(ValueError):read_report(root,'a'*40)

    def test_rejects_missing_construction_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'system.dsk').write_bytes(b'x')
            report={'source':{'revision':'a'*40},'image':'system.dsk','sha256':sha(b'x'),
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
