#!/usr/bin/env python3
"""Exercise VT52-configured WordStar through the portable monitor edit/save on disposable media.

This checks application behavior and captured wire output, not physical display.
"""
import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,default=Path.home()/'CPM/z80pack/mosteksim/disks/CPM/WordStar_VT52.dsk')
    parser.add_argument('--image',type=Path,default=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk')
    parser.add_argument('--diskdefs',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    args=parser.parse_args()
    parent=args.output;parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent))
    disks=work/'disks';disks.mkdir()
    image=disks/'drivea.dsk';shutil.copy2(args.image,image)
    shutil.copy2(args.diskdefs,work/'diskdefs')
    files=[]
    for name in ['WS.COM','WSMSGS.OVR','WSOVLY1.OVR']:
        path=work/name
        subprocess.run(['cpmcp','-f','ibm-3740',str(args.reference),'0:'+name.lower(),str(path)],check=True)
        files.append((name,path))
    document=work/'VT52TEST.TXT';document.write_bytes(b'ORIGINAL VT52 DOCUMENT\r\n\x1a')
    files.append(('VT52TEST.TXT',document))
    for name,path in files:
        existing=subprocess.check_output(['cpmls','-T','raw','-f','bettercpm-default',str(image)],cwd=work,text=True).upper().split()
        if name in existing:
            subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:'+name],cwd=work,check=True)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(path),'0:'+name],cwd=work,check=True)
    prompt=b'A0>'
    monitor_prompt=prompt
    trace=session(args.simulator,disks,[
        (b'RSX LOAD ANSISCRN\r',prompt,30),
        (b'RSX LOAD VT52\r',monitor_prompt,30),
        (b'CLS\r',monitor_prompt,10),
        (b'WS VT52TEST.TXT\r',b'WordStar',30),
        (b'VT52 EDIT CHECK\x0b\x18',monitor_prompt,30),
        (b'RSX UNLOAD VT52\r',prompt,30),
        (b'RSX UNLOAD ANSISCRN\r',prompt,30),
        (b'RSX LIST\r',b'TPA available: 53K',30),
        (b'',prompt,30),
        (b'BYE /Y\r',b'System halted',10)],work/'transcript.bin')
    assert b'No RSXs loaded' in trace and b'TPA available: 53K' in trace
    rendered=trace[trace.index(b'\x1b[1;1H'):trace.index(b'RSX UNLOAD VT52')]
    assert b'\x1b[' in rendered and b'\x1bY' not in rendered
    saved=work/'saved.txt'
    subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),'0:vt52test.txt',str(saved)],cwd=work,check=True)
    assert b'VT52 EDIT CHECK' in saved.read_bytes(),saved.read_bytes()
    import json
    from run_validation_cpmsim_monitors import audit
    manifest=json.loads((args.baseline/'report.json').read_text())
    shipped=audit(args.baseline,manifest,work,image)
    shutil.copy2(__file__,work/'executed-runner.py')
    (work/'result.json').write_text(json.dumps({'status':'PASS','application':'unmodified VT52 WordStar','baseline_sha256':manifest['sha256'],'shipped_files_unchanged':shipped,'application_sha256':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in files if name in ['WS.COM','WSMSGS.OVR','WSOVLY1.OVR']},'saved_sha256':hashlib.sha256(saved.read_bytes()).hexdigest(),'scope':'actual cpmsim edit/save/return through shipped VT52+ANSISCRN; captured wire and saved bytes, not physical terminal'},indent=2)+'\n')
    report=work/'reference.txt'
    report.write_text('\n'.join(f'{name}: {hashlib.sha256(path.read_bytes()).hexdigest()}' for name,path in files if name in ['WS.COM','WSMSGS.OVR','WSOVLY1.OVR'])+'\n')
    print(f'PASS: original VT52 WordStar opens, edits, saves and returns; provider unloads; {work}')


if __name__=='__main__':main()
