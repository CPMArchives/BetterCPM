#!/usr/bin/env python3
"""Qualify ED development startup and file lifecycle on copied Model 4 media."""
import argparse
import hashlib
import json
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw
from build_source_disk import install_files
from build_montezuma_extended_790k import build
from test_disk_utilities import ROOT,medium,keys
from test_model4_copy import files
from test_sysgen_install import screen
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run


def main():
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    report=a.report.resolve();report.mkdir(parents=True,exist_ok=False)
    binary=(ROOT/'build/ed-development/EDDEV.COM').read_bytes();observations=[]
    old=b'OLD\r\n\x1a';sentinel=b'USER ZERO\r\n\x1a'
    original=build(install_files([(7,'CASE.TXT',old),(0,'CASE.TXT',sentinel)]))
    for label in ('version','save','quit','head'):
        work=report/label;work.mkdir();marker='ED FINISHED '+label.upper()
        finish=b'\x11\x0b\x01\x0e\x09\xcd\x05\x00\xc3\x00\x00'+('\r\n'+marker+'\r\n$').encode()
        (work/'a.dmk').write_bytes(medium([('EDDEV.COM',binary),('FINISH.COM',finish)]))
        (work/'b.dmk').write_bytes(original)
        steps=['EDDEV /VER\r'] if label=='version' else ['EDDEV B7:CASE.TXT\r','INEW\x1a\r']
        if label=='quit':steps+=['Q\r','Y']
        elif label=='head':steps+=['H\r','IAGAIN\x1a\r','E\r']
        elif label=='save':steps+=['E\r']
        steps+=['A0:\r','FINISH\r']
        cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(work/'a.dmk'),'-d1',str(work/'b.dmk'),'-id','3000','-it']
        for text in steps:cmd+=keys(text)+['-id','4000','-it']
        cmd+=['-itime','0','-iw',marker,'-id','1000','-it','-ix']
        (work/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n')
        run(cmd,cwd=work,timeout=180,check=True)
        captures=sorted(work.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
        texts=[screen(p) for p in captures]
        for path,text in zip(captures,texts):path.with_suffix('.txt').write_text(text)
        assert texts and marker in texts[-1],texts
        if label=='version':
            assert any('BetterCP/M ED 1.0 (Build 001)' in t for t in texts),texts
            assert (work/'b.dmk').read_bytes()==original
        else:
            current=files(extract_raw((work/'b.dmk').read_bytes()))
            def get(user,ext):return current.get((user,b'CASE    '+ext))
            assert get(0,b'TXT')[0].split(b'\x1a')[0]==sentinel[:-1]
            expected=old[:-1] if label=='quit' else (b'AGAINNEW'+old[:-1] if label=='head' else b'NEW'+old[:-1])
            assert get(7,b'TXT')[0].split(b'\x1a')[0]==expected,(label,get(7,b'TXT'))
            assert get(7,b'$$$') is None,label
            if label=='quit':assert get(7,b'BAK') is None
            else:assert get(7,b'BAK')[0].split(b'\x1a')[0]==(b'NEW'+old[:-1] if label=='head' else old[:-1])
        observations.append({'case':label,'result':'PASS'})
    (report/'evidence.json').write_text(json.dumps({'ed_sha256':hashlib.sha256(binary).hexdigest(),'observations':observations},indent=2)+'\n')
    print('PASS: Model 4 ED /VER, B7 save, Q discard, H restart and user-0 sentinel preservation')


if __name__=='__main__':main()
