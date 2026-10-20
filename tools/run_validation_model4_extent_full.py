#!/usr/bin/env python3
"""Native public sequential/random directory-full checks with raw media audit."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
from add_cpm_file_to_dmk import add_file, extract_raw
from build_montezuma_extended_790k import build
from build_ccp import assemble
from run_validation_sequential_directory_full import SOURCE
from run_validation_model4 import sha, audit_files
from run_trs80_command import DEFAULT_EMULATOR, key_args
from test_sysgen_install import screen
from trs80gp_launch import run


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False)
    shutil.copy2(__file__,w/'executed-runner.py')
    shutil.copy2(Path(__file__).with_name('run_validation_sequential_directory_full.py'),w/'executed-probe-source.py')
    report=json.loads((a.baseline/'report.json').read_text());source=a.baseline/report['image']
    assert report['target']=='trs80gp' and sha(source)==report['sha256']
    system=extract_raw(source.read_bytes())
    for function,name in ((21,'FDSEQ'),(34,'FDRAND')):
        code=SOURCE.replace('@EXT@','0').replace('@RECORD@','128').replace('@FUNCTION@',str(function))
        if function==34:code=code.replace('SEQ STATUS','RAND STATUS')
        (w/(name+'.asm')).write_text(code)
        program=w/(name+'.COM');assemble(Path.home()/'bin/z80asm',code,program,w/(name+'.lst'),0x100)
        add_file(system,name+'.COM',program.read_bytes())
    (w/'a.dmk').write_bytes(build(system))
    raw=bytearray(b'\xe5'*len(system));directory=bytearray(4096)
    for n in range(128):
        offset=32*n
        directory[offset+1:offset+12]=b'SOURCE  DAT' if not n else (f'F{n:07d}'+'DAT').encode()
    directory[15]=128
    for n in range(8):directory[16+2*n:18+2*n]=(n+2).to_bytes(2,'little')
    raw[:4096]=directory
    payload=bytes((n*29+7)&255 for n in range(16384));raw[4096:20480]=payload
    assert len({int.from_bytes(directory[n:n+2],'little') for n in range(16,32,2)})==8
    (w/'b-before.raw').write_bytes(raw);(w/'b.dmk').write_bytes(build(raw))
    (w/'diskdefs').write_text('diskdef native-data\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 0\n os 2.2\nend\n')
    def fsck(path):
        q=subprocess.run(['fsck.cpm','-T','raw,pcw800','-f','native-data','-n',str(path)],cwd=w,capture_output=True)
        (w/(path.stem+'-filesystem.txt')).write_bytes(q.stdout+q.stderr)
        assert q.returncode==0,q.stdout
    fsck(w/'b-before.raw')
    command=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(w/'a.dmk'),'-d1',str(w/'b.dmk'),'-itime','15000','-iw','Type TYPE README.TXT for more','-id','6000']
    command+=key_args('B:\r')+['-id','6000']
    for name in ('FDSEQ','FDRAND'):
        command+=key_args('A0:'+name+'\r')+['-iw','SEQ STATUS' if name=='FDSEQ' else 'RAND STATUS','-id','6000','-it']
    command+=['-ix'];run(command,cwd=w,timeout=600)
    results={}
    for n,expected in ((0,1),(1,5)):
        text=screen(w/f'trs80-text-{n}.bin');(w/f'screen-{n}.txt').write_text(text)
        marker=('SEQ' if not n else 'RAND')+' STATUS '
        tail=text[text.rfind(marker):]
        status=re.search(re.escape(marker)+r'([0-9A-F]{2})',tail)
        before=re.search(r'BEFORE ([0-9A-F]{72})',tail);after=re.search(r'AFTER ([0-9A-F]{72})',tail)
        assert status and before and after,text
        assert int(status[1],16)==expected,text
        if not n:assert before[1]==after[1],'sequential FCB changed'
        results[str(21 if not n else 34)]={'status_code':expected,'fcb_before_hex':before[1],'fcb_after_hex':after[1]}
    after=extract_raw((w/'b.dmk').read_bytes());assert after==raw,'failed growth changed data disk'
    (w/'b-after.raw').write_bytes(after);fsck(w/'b-after.raw')
    files=audit_files(source,w/'a.dmk',report,w)
    assert sha(source)==report['sha256']
    result={'status':'PASS','baseline_sha256':report['sha256'],'emulator_sha256':sha(DEFAULT_EMULATOR),'results':results,'whole_data_disk_unchanged':True,'allocated_blocks':10,'free_data_blocks':390,'directory_entries':128,'system_file_audit':files,'scope':'Actual native Model 4 public Functions 21/34 with directory full and free data blocks; sequential FCB and independent whole-data-disk preservation.'}
    (w/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
