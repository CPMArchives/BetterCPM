"""Ensure final naming cannot bypass acceptance or rewrite historical source."""
import json
import io
import tarfile
from pathlib import Path
import tempfile
import unittest
import zipfile
from package_release_candidates import write_package,encoded,sha
from finalize_release_11 import prepare,REQUIRED


class FinalizeTests(unittest.TestCase):
    def setup_inputs(self,root):
        candidates=root/'candidates';candidates.mkdir();assets=[];images={}
        for index,name in enumerate(('system-cpmsim','system-model4','utilities-cpmsim','utilities-model4','system-model2','utilities-model2','source','documentation')):
            filename='BetterCPM-1.1-'+name+'.zip';archive=filename[:-4]
            asset={'id':name,'filename':filename,'archive_root':archive};assets.append(asset)
            files={'README.txt':b'CANDIDATE \xe2\x80\x94 assembled for review; NOT ACCEPTED FOR RELEASE.\nCANDIDATE \xe2\x80\x94 NOT ACCEPTED FOR RELEASE.',
                   'SOURCE-IDENTITY.json':encoded({'source_commit':'a'*40,'status':'CANDIDATE'}),
                   'source/BetterCPM/docs/history/SOURCE-IDENTITY.json':encoded({'source_commit':'b'*40,'status':'historical'})}
            count=0 if name in ('source','documentation') else 1 if name=='system-model2' else 2
            for number in range(count):
                member=f'images/disk{number}.imd'
                files[member]=(name+str(number)).encode()
                images[name+'/'+member]=sha(files[member])
            record={'package':name,'version':'1.1','source_commit':'a'*40,'files':{n:sha(d) for n,d in files.items()}}
            write_package(candidates/(filename[:-4]+'-candidate.zip'),archive+'-candidate',files,record)
        evidence=root/'evidence.tar.gz'
        with tarfile.open(evidence,'w:gz') as archive:
            info=tarfile.TarInfo('run.json');data=b'{"status":"PASS"}'
            info.size=len(data);archive.addfile(info,io.BytesIO(data))
        acceptance=root/'acceptance.json';acceptance.write_bytes(encoded({'version':'1.1','status':'PASS','source_commit':'a'*40,'images':images,'evidence_sha256':sha(evidence.read_bytes()),'checks':[{'name':n,'status':'PASS','evidence':['run.json']} for n in sorted(REQUIRED)]}))
        return candidates,acceptance,evidence,{'version':'1.1','assets':assets}

    def test_final_archives_keep_historical_source_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c,a,e,layout=self.setup_inputs(root);out=root/'final'
            result=prepare(c,a,e,out,layout);self.assertEqual(len(result['assets']),8)
            with zipfile.ZipFile(out/layout['assets'][6]['filename']) as z:
                prefix=layout['assets'][6]['archive_root']+'/'
                old=json.loads(z.read(prefix+'source/BetterCPM/docs/history/SOURCE-IDENTITY.json'))
                self.assertEqual(old['source_commit'],'b'*40);self.assertEqual(old['status'],'historical')
                current=json.loads(z.read(prefix+'SOURCE-IDENTITY.json'));self.assertEqual(current['release_version'],'1.1')
                self.assertIn(prefix+'source/release-evidence-1.1.tar.gz',z.namelist())
                self.assertNotIn(b'CANDIDATE',z.read(prefix+'README.txt'))
            with self.assertRaises(FileExistsError):prepare(c,a,e,out,layout)

    def test_missing_or_duplicate_checks_fail_before_output(self):
        for duplicate in (False,True):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);c,a,e,layout=self.setup_inputs(root);d=json.loads(a.read_text())
                if duplicate:d['checks'].append(d['checks'][0])
                else:d['checks'].pop()
                a.write_bytes(encoded(d));out=root/'final'
                with self.assertRaises(ValueError):prepare(c,a,e,out,layout)
                self.assertFalse(out.exists())

    def test_evidence_and_image_drift_fail_before_output(self):
        for kind in ('evidence','image'):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);c,a,e,layout=self.setup_inputs(root)
                if kind=='evidence':e.write_bytes(b'changed')
                else:
                    d=json.loads(a.read_text());d['images']={'missing.dsk':'0'*64};a.write_bytes(encoded(d))
                out=root/'final'
                with self.assertRaises(ValueError):prepare(c,a,e,out,layout)
                self.assertFalse(out.exists())

    def test_unverified_status_and_missing_evidence_reject_promotion(self):
        for field,value in [('status','UNVERIFIED'),('evidence',[]),('evidence',['absent.json'])]:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);c,a,e,layout=self.setup_inputs(root)
                data=json.loads(a.read_text());data['checks'][0][field]=value
                a.write_bytes(encoded(data));out=root/'final'
                with self.assertRaises(ValueError):prepare(c,a,e,out,layout)
                self.assertFalse(out.exists())


if __name__=='__main__':unittest.main()
