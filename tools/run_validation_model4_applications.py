#!/usr/bin/env python3
"""Smoke-test shipped file utilities and ED on a qualified private Model 4 disk."""
import argparse,json,shutil,tempfile,subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw,add_file
from build_source_disk import install_files
from build_montezuma_extended_790k import build
from run_validation_model4 import sha,audit_files
from test_model4_copy import files
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run
from test_sysgen_install import screen


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();report=json.loads((a.baseline/'report.json').read_text())
    original=a.baseline/report['image'];assert report['target']=='trs80gp' and sha(original)==report['sha256']
    a.output.mkdir(parents=True,exist_ok=True);w=Path(tempfile.mkdtemp(prefix='applications-',dir=a.output.resolve()))
    shutil.copy2(__file__,w/'executed-runner.py')
    raw=extract_raw(original.read_bytes())
    script=[':PIP B1:PCOPY.TXT=B1:SOURCE.TXT',':COPY /V /B B1:SOURCE.TXT B3:CCOPY.TXT',
            ':REN B1:PCOPY.TXT RCOPY.TXT /Y',':TYPE B1:RCOPY.TXT',':ERA B1:RCOPY.TXT /Y',
            'AREGCL','COPY B1:SOURCE.TXT B3:RESCOPY.TXT','REN B3:RESCOPY.TXT FINAL.TXT',
            'TYPE B3:FINAL.TXT','ERA B3:FINAL.TXT',':DIR B[1,3]:*.TXT','AREGDONE']
    add_file(raw,'AREG.SUB',('\r\n'.join(script)+'\r\n\x1a').encode())
    marker='APPLICATION FILE WORKFLOW FINISHED'
    add_file(raw,'AREGDONE.COM',bytes.fromhex('110b010e09cd0500c30000')+('\x1a'+marker+'\r\n$').encode())
    add_file(raw,'AREGCL.COM',bytes.fromhex('110b010e09cd0500c30000')+b'\x1aRESIDENT WORKFLOW START\r\n$')
    edmarker='ED SAVE REGRESSION FINISHED'
    add_file(raw,'EDREGEND.COM',bytes.fromhex('110b010e09cd0500c30000')+('\x1a'+edmarker+'\r\n$').encode())
    image=w/'a.dmk';image.write_bytes(build(bytes(raw)))
    source=b'ALPHA\r\nBETA\r\n\x1a';old=b'OLD\r\n\x1a';sentinel=b'USER ZERO\r\n\x1a'
    braw=install_files([(1,'SOURCE.TXT',source),(7,'CASE.TXT',old),(0,'CASE.TXT',sentinel)])
    (w/'b-before.raw').write_bytes(braw);secondary=w/'b.dmk';secondary.write_bytes(build(braw))
    cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-d1',str(secondary),'-itime','15000',
         '-iw','Type TYPE README.TXT for more','-id','6000']+key_args('SUBMIT AREG\r')
    cmd+=['-iw','ALPHA','-id','120','-it','-iw','RESIDENT WORKFLOW START',
          '-iw','ALPHA','-id','120','-it','-iw',marker,'-id','120','-it']
    # ED reads real keyboard input; save into user 7 while user 0 is a sentinel.
    cmd+=['-id','6000']+key_args(':ED B7:CASE.TXT\r')+['-iw','*']
    cmd+=key_args('INEW\x1a\r',delay=60)+['-iw','*']+key_args('E\r',delay=60)+['-id','6000']
    cmd+=key_args('EDREGEND\r')+['-iw',edmarker,'-id','120','-it','-ix']
    (w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n');run(cmd,cwd=w,timeout=1800)
    captures=sorted(w.glob('trs80-text-*.bin'));assert len(captures)==4
    texts=[screen(path) for path in captures]
    for i,text in enumerate(texts):(w/f'case-{i}.txt').write_text(text+'\n')
    assert all('ALPHA' in text and 'BETA' in text for text in texts[:2])
    assert marker in texts[2] and edmarker in texts[3]
    after=extract_raw(secondary.read_bytes());(w/'b-after.raw').write_bytes(after);current=files(after)
    def key(user,name):stem,ext=name.split('.');return user,(stem.ljust(8)+ext.ljust(3)).encode()
    def content(user,name):return current[key(user,name)][0].split(b'\x1a')[0]
    assert content(1,'SOURCE.TXT')==source[:-1] and content(3,'CCOPY.TXT')==source[:-1]
    for user,name in [(1,'PCOPY.TXT'),(1,'RCOPY.TXT'),(3,'RESCOPY.TXT'),(3,'FINAL.TXT'),(7,'CASE.$$$')]:assert key(user,name) not in current,(user,name)
    assert content(7,'CASE.TXT')==b'NEW'+old[:-1]
    assert content(7,'CASE.BAK')==old[:-1] and content(0,'CASE.TXT')==sentinel[:-1]
    assert set(current)=={key(1,'SOURCE.TXT'),key(3,'CCOPY.TXT'),key(7,'CASE.TXT'),key(7,'CASE.BAK'),key(0,'CASE.TXT')}
    audit=audit_files(original,image,report,w)
    (w/'diskdefs').write_text('diskdef native-data\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 0\n os 2.2\nend\n')
    checks=[]
    for path,folder,fmt in [(w/'b-after.raw',w,'native-data'),(w/'file-audit/after.raw',w/'file-audit','bettercpm-default')]:
        c=subprocess.run(['fsck.cpm','-T','raw,pcw800','-f',fmt,'-n',str(path)],cwd=folder,capture_output=True,text=True)
        (folder/'filesystem.txt').write_text(c.stdout+c.stderr);assert c.returncode==0;checks.append(c.returncode)
    assert sha(original)==report['sha256']
    (w/'result.json').write_text(json.dumps({'status':'PASS','baseline_sha256':report['sha256'],'emulator_sha256':sha(DEFAULT_EMULATOR),
        'script':script,'system_file_audit':audit,'filesystem_status':checks,
        'scope':'shipped PIP/COPY/REN/TYPE/ERA resident/transient chain and ED B7 save/backup with user-0 sentinel; representative smoke checks, not exhaustive utility qualification'},indent=2)+'\n')
    print(w,flush=True)


if __name__=='__main__':main()
