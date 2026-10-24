"""Direct coverage/independence and immutable-manifest checks only."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from component_registry import ROOT, load
from component_inputs import capture, digest
from checked_build_contract import compatibility_inputs
from release_metadata import disk_record, immutable_write, package_record


class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name)
        self.tool=self.work/'assembler';self.tool.write_bytes(b'assembler fixture')
        env=patch.dict(os.environ,{},clear=True);env.start();self.addCleanup(env.stop)

    def test_all_51_components_have_valid_cross_maps(self):
        plans=json.loads((ROOT/'metadata/component-inputs.json').read_text())['components']
        self.assertEqual(set(plans),set(load()['components']))
        for component,plan in plans.items():
            record=capture(component,self.tool,target=plan['target'])
            self.assertEqual(record['inputs']['component'],component)
            self.assertTrue(record['inputs']['files'])

    def test_native_requires_and_records_linker_and_flags(self):
        with self.assertRaisesRegex(ValueError,'linker'):
            capture('utility:BYE',self.tool,build_mode='native')
        linker=self.work/'linker';linker.write_bytes(b'linker fixture')
        a=capture('utility:BYE',self.tool,build_mode='native',toolchain={'linker':linker},configuration={'flags':['A']})
        b=capture('utility:BYE',self.tool,build_mode='native',toolchain={'linker':linker},configuration={'flags':['B']})
        self.assertNotEqual(a['fingerprint'],b['fingerprint'])
        linker.write_bytes(b'changed linker')
        c=capture('utility:BYE',self.tool,build_mode='native',toolchain={'linker':linker},configuration={'flags':['A']})
        self.assertNotEqual(a['fingerprint'],c['fingerprint'])

    def test_checked_identity_excludes_unrelated_utilities_tests_and_counters(self):
        original={'src/system/extens.mac':'a','src/bios/bios.mac':'b','tools/checked_carriers.py':'c',
                  'src/utilities/pip.mac':'d','tools/test_anything.py':'e','metadata/utility-versions.tsv':'f'}
        changed=dict(original);changed.update({'src/utilities/pip.mac':'D','tools/test_anything.py':'E','metadata/utility-versions.tsv':'F'})
        self.assertEqual(compatibility_inputs(original),compatibility_inputs(changed))
        changed['src/system/extens.mac']='different ABI code'
        self.assertNotEqual(compatibility_inputs(original),compatibility_inputs(changed))

    def test_disk_and_package_checksums_no_self_reference(self):
        image=b'fixture final disk bytes'
        report={'target':'z80pack','image':'fixture.dsk','sha256':digest(image),
                'source':{'revision':'a'*40,'inputs':{'src/fixture':'b'}},
                'included':[{'name':'README.TXT','sha256':digest(b'readme'),'bytes':6}]}
        record=disk_record(report,image,require_commit=True)
        path=self.work/'disk.json';immutable_write(path,record);immutable_write(path,record)
        package=package_record('1.0','001',[path])
        self.assertEqual(package['disks'][0]['sha256'],digest(path.read_bytes()))
        changed=copy.deepcopy(record);changed['target']='trs80gp'
        with self.assertRaisesRegex(ValueError,'redefine'):immutable_write(path,changed)
        with self.assertRaisesRegex(ValueError,'checksum'):disk_record(report,b'different image')

    def test_unknown_provenance_cannot_be_frozen(self):
        image=b'disk';report={'target':'z80pack','image':'disk','sha256':digest(image),'included':[]}
        with self.assertRaisesRegex(ValueError,'source commit'):disk_record(report,image,require_commit=True)
        path=self.work/'provisional.json';immutable_write(path,disk_record(report,image))
        with self.assertRaises(ValueError):package_record('1.0','001',[path])

    def test_cached_identity_is_preserved(self):
        data=b'cached executable'
        root=self.work/'repo';(root/'metadata').mkdir(parents=True);(root/'build/z80pack-tools').mkdir(parents=True)
        (root/'metadata/component-registry.json').write_bytes((ROOT/'metadata/component-registry.json').read_bytes())
        (root/'build/z80pack-tools/BYE.COM').write_bytes(data)
        old={'component':'utility:BYE','identity':{'version':'1.0','revision':1},
             'artifact':{'sha256':digest(data),'bytes':len(data)},'provenance':{'repository_commit':'b'*40}}
        (root/'build/z80pack-tools/build-report.json').write_text(json.dumps(old))
        image=b'disk';report={'target':'z80pack','image':'disk','sha256':digest(image),
                            'source':{'revision':'a'*40},'included':[{'name':'BYE.COM','sha256':digest(data),'bytes':len(data)}]}
        record=disk_record(report,image,root=root)
        self.assertEqual(record['included'][0]['identity']['revision'],1)
        self.assertEqual(record['included'][0]['build_provenance']['repository_commit'],'b'*40)


if __name__=='__main__':unittest.main()
