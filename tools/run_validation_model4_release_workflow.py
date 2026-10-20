#!/usr/bin/env python3
"""Continuous native release session plus cold boot on fresh System Disk media."""
import argparse,json,shutil,tempfile,subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw,add_file,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
from build_source_disk import install_files
from build_montezuma_extended_790k import build
from run_validation_model4 import sha,audit_files
from test_model4_copy import files
from run_trs80_command import DEFAULT_EMULATOR,key_args as matrix_keys
from trs80gp_launch import run
from test_sysgen_install import screen


def key_args(text,delay=60):return matrix_keys(text,delay=delay)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();report=json.loads((a.baseline/'report.json').read_text())
    original=a.baseline/report['image'];assert report['target']=='trs80gp' and sha(original)==report['sha256']
    a.output.mkdir(parents=True,exist_ok=True);w=Path(tempfile.mkdtemp(prefix='applications-',dir=a.output.resolve()))
    shutil.copy2(__file__,w/'executed-runner.py')
    raw=extract_raw(original.read_bytes())
    script=[':PIP B1:PCOPY.TXT=B1:SOURCE.TXT',':COPY /V /B B1:SOURCE.TXT B3:CCOPY.TXT',
            ':REN B1:PCOPY.TXT RCOPY.TXT /Y',':TYPE B1:RCOPY.TXT','WFGATEA',':ERA B1:RCOPY.TXT /Y',
            'AREGCL','COPY B1:SOURCE.TXT B3:RESCOPY.TXT','REN B3:RESCOPY.TXT FINAL.TXT',
            'TYPE B3:FINAL.TXT','WFGATEB','ERA B3:FINAL.TXT',':DIR B[1,3]:*.TXT','AREGDONE']
    add_file(raw,'AREG.SUB',('\r\n'.join(script)+'\r\n\x1a').encode())
    # SUBMIT expands dollar parameters; double each literal attribute marker.
    script.insert(2,'STAT B3:CCOPY.TXT $$R/O')
    script.insert(3,'STAT B3:CCOPY.TXT $$R/W')
    script.insert(4,':DIR /WHEREIS B[-]:SOURCE.TXT')
    script[-1:-1]=['COPY B1:SOURCE.TXT B3:REPEAT.TXT','ERA B3:REPEAT.TXT','COPY B1:SOURCE.TXT B3:REPEAT.TXT','ERA B3:REPEAT.TXT']
    script += [':ED B7:CASE.TXT','EDREGEND','A0:',
               'RSX UNLOAD ADM3A','RSX LOAD VT52','TYPE B7:CASE.TXT','WFGATEC',
               'RSX UNLOAD VT52','RSX LOAD ANSI','TYPE B7:CASE.TXT','WFGATED',
               'RSX UNLOAD ANSI','RSX UNLOAD M4SCRN','RSX LIST']
    # Keep command dispatch inside SUBMIT; only ED and explicit gates read keys.
    # Regenerate the script after adding the integrated attribute/repeat stages.
    raw=extract_raw(original.read_bytes())
    add_file(raw,'AREG.SUB',('\r\n'.join(script)+'\r\n\x1a').encode())
    for index in range(DIRECTORY_ENTRIES):
        at=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE+index*32
        if raw[at]==0 and raw[at+1:at+12]==b'STARTUP SUB':raw[at]=229
    add_file(raw,'STARTUP.SUB',b':VER /BANNER\r\nRSX LOAD M4SCRN\r\nRSX LOAD ADM3A\r\nTYPE README.TXT\r\nWFREADY\r\nSUBMIT AREG\r\n\x1a')
    add_file(raw,'WFREADY.COM',bytes.fromhex('1112010e09cd05000e01cd05000e00c30500')+b'README PHASE READY\r\n$')
    marker='APPLICATION FILE WORKFLOW FINISHED'
    add_file(raw,'AREGDONE.COM',bytes.fromhex('110b010e09cd0500c30000')+('\x1a'+marker+'\r\n$').encode())
    add_file(raw,'AREGCL.COM',bytes.fromhex('110b010e09cd0500c30000')+b'\x1aRESIDENT WORKFLOW START\r\n$')
    edmarker='ED SAVE REGRESSION FINISHED'
    add_file(raw,'EDREGEND.COM',bytes.fromhex('110b010e09cd0500c30000')+('\x1a'+edmarker+'\r\n$').encode())
    # Hold both TYPE displays until the capture has acknowledged them.
    for name in ('WFGATEA','WFGATEB','WFGATEC','WFGATED'):
        add_file(raw,name+'.COM',bytes.fromhex('1112010e09cd05000e01cd05000e00c30500')+(name+' READY\r\n$').encode())
    image=w/'a.dmk';image.write_bytes(build(bytes(raw)))
    source=b'ALPHA\r\nBETA\r\n\x1a';old=b'OLD\r\n\x1a';sentinel=b'USER ZERO\r\n\x1a'
    braw=install_files([(1,'SOURCE.TXT',source),(7,'CASE.TXT',old),(0,'CASE.TXT',sentinel)])
    (w/'b-before.raw').write_bytes(braw);secondary=w/'b.dmk';secondary.write_bytes(build(braw))
    cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-d1',str(secondary),'-itime','15000',
         '-iw','README PHASE READY','-id','120','-it']+key_args(' ')
    cmd+=['-iw','WFGATEA READY','-id','120','-it']+key_args(' ')
    cmd+=['-iw','WFGATEB READY','-id','120','-it']+key_args(' ')
    cmd+=['-iw',marker,'-id','120','-it']
    # The queued ED command now owns the keyboard; no timed host command prefix.
    cmd+=['-iw','*']+key_args('INEW\x1a\r',delay=60)+['-iw','*']+key_args('E\r',delay=60)
    cmd+=['-iw',edmarker,'-id','120','-it']
    for name in ('WFGATEC','WFGATED'):
        cmd+=['-iw',name+' READY','-id','120','-it']+key_args(' ')
    cmd+=['-iw','No RSXs loaded','-iw','TPA available: 53K','-id','120','-it','-ix']
    (w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n');run(cmd,cwd=w,timeout=1800)
    captures=sorted(w.glob('trs80-text-*.bin'));assert len(captures)==8
    texts=[screen(path) for path in captures]
    for i,text in enumerate(texts):(w/f'case-{i}.txt').write_text(text+'\n')
    assert 'Disk; it is not part of this System Disk.' in texts[0]
    assert all('ALPHA' in text and 'BETA' in text for text in texts[1:3])
    assert marker in texts[3] and edmarker in texts[4]
    assert all('NEWOLD' in t for t in texts[5:7])
    assert 'No RSXs loaded' in texts[-1] and 'TPA available: 53K' in texts[-1]
    after=extract_raw(secondary.read_bytes());(w/'b-after.raw').write_bytes(after);current=files(after)
    def key(user,name):stem,ext=name.split('.');return user,(stem.ljust(8)+ext.ljust(3)).encode()
    def content(user,name):return current[key(user,name)][0].split(b'\x1a')[0]
    assert content(1,'SOURCE.TXT')==source[:-1] and content(3,'CCOPY.TXT')==source[:-1]
    for user,name in [(1,'PCOPY.TXT'),(1,'RCOPY.TXT'),(3,'RESCOPY.TXT'),(3,'FINAL.TXT'),(7,'CASE.$$$')]:assert key(user,name) not in current,(user,name)
    assert content(7,'CASE.TXT')==b'NEW'+old[:-1]
    assert content(7,'CASE.BAK')==old[:-1] and content(0,'CASE.TXT')==sentinel[:-1]
    assert set(current)=={key(1,'SOURCE.TXT'),key(3,'CCOPY.TXT'),key(7,'CASE.TXT'),key(7,'CASE.BAK'),key(0,'CASE.TXT')}
    audit=audit_files(original,image,dict(report,included=[f for f in report['included'] if f['name']!='STARTUP.SUB']),w)
    assert extract_raw(original.read_bytes())[:20480]==extract_raw(image.read_bytes())[:20480]
    (w/'diskdefs').write_text('diskdef native-data\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 0\n os 2.2\nend\n')
    checks=[]
    for path,folder,fmt in [(w/'b-after.raw',w,'native-data'),(w/'file-audit/after.raw',w/'file-audit','bettercpm-default')]:
        c=subprocess.run(['fsck.cpm','-T','raw,pcw800','-f',fmt,'-n',str(path)],cwd=folder,capture_output=True,text=True)
        (folder/'filesystem.txt').write_text(c.stdout+c.stderr);assert c.returncode==0;checks.append(c.returncode)
    reboot=w/'reboot';reboot.mkdir();second=reboot/'a.dmk';second.write_bytes(original.read_bytes());before_second=secondary.read_bytes()
    cmd2=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(second),'-d1',str(secondary),'-itime','15000','-iw','Type TYPE README.TXT for more','-id','6000']+key_args('TYPE B7:CASE.TXT\r')+['-iw','NEWOLD','-id','120','-it','-id','6000']
    cmd2+=key_args('RSX UNLOAD ADM3A\r')+['-id','6000']+key_args('RSX UNLOAD M4SCRN\r')+['-id','6000']+key_args('RSX LIST\r')+['-iw','TPA available: 53K','-id','120','-it','-ix']
    (reboot/'invocation.json').write_text(json.dumps(cmd2,indent=2)+'\n');run(cmd2,cwd=reboot,timeout=900)
    snapshots=[screen(f) for f in sorted(reboot.glob('trs80-text*'))];assert len(snapshots)==2 and 'NEWOLD' in snapshots[0] and 'TPA available: 53K' in snapshots[-1]
    assert secondary.read_bytes()==before_second,'second cold boot changed saved data'
    audit_files(original,second,report,reboot)
    assert sha(original)==report['sha256']
    (w/'result.json').write_text(json.dumps({'status':'PASS','baseline_sha256':report['sha256'],'emulator_sha256':sha(DEFAULT_EMULATOR),
        'script':script,'system_file_audit':audit,'filesystem_status':checks,
        'sessions':2,'scope':'Continuous native README/WHEREIS/PIP/COPY/REN/STAT/TYPE/ERA/SUBMIT, ED save/backup and three monitor personalities; second fresh System Disk cold boot preserves saved data. STARTUP.SUB is a declared first-session queue fixture; no configuration-installation workflow claim.'},indent=2)+'\n')
    print(w,flush=True)


if __name__=='__main__':main()
