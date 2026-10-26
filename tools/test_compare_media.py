#!/usr/bin/env python3
"""Focused COMPARE execution on disposable BetterCP/M cpmsim and Model 4 media."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from test_z80pack_sysgen_install import session
from test_disk_utilities import keys
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build as make_dmk
from test_sysgen_install import screen
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run
ROOT=Path(__file__).resolve().parents[1]
PROMPT='Space/Enter: next; Ctrl-C/Q/Esc: stop'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image-dir',type=Path,required=True,help='existing cpmsim image directory with disks/ and diskdefs')
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--model4-image',type=Path,default=ROOT/'build/trs80/BetterCPM-Distribution-trs80gp-80T-DS-System.dmk')
    p.add_argument('--target',choices=['both','cpmsim','model4'],default='both')
    a=p.parse_args();work=a.report.resolve();work.mkdir(parents=True,exist_ok=False)
    binary=(ROOT/'build/utilities/COMPARE.COM').read_bytes()
    first=bytes(range(256))*2;second=bytearray(first);second[0]^=1;second[127]^=1;second=bytes(second[:384])
    result={'binary_sha256':hashlib.sha256(binary).hexdigest(),'scope':'focused platform execution; final Utilities Disk acceptance not asserted'}
    if a.target in ('both','cpmsim'):
        w=work/'cpmsim';w.mkdir();shutil.copytree(a.image_dir/'disks',w/'disks');shutil.copy2(a.image_dir/'diskdefs',w/'diskdefs')
        disk=w/'disks/drivea.dsk'
        def cpm(tool,*args):
            subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,args)],cwd=w,check=True,stdout=subprocess.DEVNULL)
        cpm('cpmrm','0:*.*')
        for name,payload,dest in [('COMPARE.COM',binary,'0:COMPARE.COM'),('A.BIN',first,'3:A.BIN'),('B.BIN',second,'7:B.BIN')]:
            (w/name).write_bytes(payload);cpm('cpmcp',w/name,dest)
        before=disk.read_bytes()
        steps=[(b':COMPARE /VER\r',b'A0>_ ',30),
               (b':COMPARE A3:A.BIN A7:B.BIN /SUMMARY\r',b'A0>_ ',30),
               (b':COMPARE A3:A.BIN A7:B.BIN /FROM=7 /FROM2=0 /LEN=5 /SIDE /40\r',b'A0>_ ',30),
               (b':COMPARE A3:A.BIN A7:B.BIN /SIDE /40 /P\r',PROMPT.encode(),30),
               (b'\x03',b'A0>_ ',30)]
        text=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',w/'disks',steps,w/'transcript.txt')
        for marker in (b'COMPARE 1.0 (001-dev)',b'BYTE MISMATCHES: 2',b'ADDITIONAL IN FILE 1: 128',b'00000004        07<>--------        01',b'DISPLAY INTERRUPTED',b'COMPARISON CONTINUING...'):
            assert marker in text,(marker,text[-2000:])
        assert disk.read_bytes()==before,'COMPARE changed cpmsim media'
        result['cpmsim']={'result':'PASS','whole_disk_unchanged':True}
        print('PASS cpmsim: version, cross-user comparison, range/40, Ctrl-C display-stop, immutable media',flush=True)
    if a.target in ('both','model4'):
        w=work/'model4';w.mkdir();disk=w/'a.dmk'
        raw=w/'system.raw';raw.write_bytes(extract_raw(a.model4_image.read_bytes()))
        (w/'diskdefs').write_text('diskdef dasm-system\n libdsk:format pcw800\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n')
        def mtool(tool,*args):
            subprocess.run([tool,'-T','raw','-f','dasm-system',str(raw),*map(str,args)],cwd=w,check=True,stdout=subprocess.DEVNULL)
        mtool('cpmrm','0:STARTUP.SUB')
        for name,payload,dest in [('COMPARE.COM',binary,'0:COMPARE.COM'),('A.BIN',first,'3:A.BIN'),('B.BIN',second,'7:B.BIN'),('STARTUP.SUB',b'\x1a','0:STARTUP.SUB')]:
            (w/name).write_bytes(payload);mtool('cpmcp',w/name,dest)
        original=make_dmk(raw.read_bytes());disk.write_bytes(original)
        emulator=DEFAULT_EMULATOR
        if not emulator.is_file():emulator=Path.home()/'CPM/trs80/trs80gp-2/mac/trs80gp.app/Contents/MacOS/trs80gp'
        command=[str(emulator),'-m4','-batch','-turbo','-sx','-sfmute','-ktx','-d0',str(disk),'-id','3000','-it']
        command+=keys(':COMPARE A3:A.BIN A7:B.BIN /SUMMARY\r')+['-iw','FILES DIFFER','-iw','A0>','-it']
        command+=keys(':COMPARE A3:A.BIN A7:B.BIN /FROM=7 /FROM2=0 /LEN=5 /SIDE /40\r')+['-iw','SELECTED RANGES DIFFER','-iw','A0>','-it']
        command+=keys(':COMPARE A3:A.BIN A7:B.BIN /SIDE /40 /P\r')+['-iw',PROMPT,'-it']
        command+=keys('\x03')+['-iw','COMPARISON CONTINUING...','-iw','FILES DIFFER','-iw','A0>','-it','-ix']
        (w/'invocation.json').write_text(json.dumps(command,indent=2)+'\n')
        run(command,cwd=w,timeout=90,check=True)
        captures=sorted(w.glob('trs80-text-*.bin'),key=lambda f:int(f.stem.rsplit('-',1)[1]))
        texts=[screen(f) for f in captures]
        for f,t in zip(captures,texts):f.with_suffix('.txt').write_text(t)
        assert len(texts)==5,len(texts)
        assert 'BYTE MISMATCHES: 2' in texts[1] and 'ADDITIONAL IN FILE 1: 128' in texts[1],texts[1]
        assert '00000004        07<>--------        01' in texts[2],texts[2]
        assert PROMPT in texts[3],texts[3]
        assert 'DISPLAY INTERRUPTED' in texts[4] and 'ADDITIONAL IN FILE 1: 128' in texts[4],texts[4]
        assert disk.read_bytes()==original,'COMPARE changed Model 4 media'
        result['model4']={'result':'PASS','whole_disk_unchanged':True}
        print('PASS Model 4: cross-user comparison, range/40, Ctrl-C display-stop, immutable media',flush=True)
    (work/'evidence.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
