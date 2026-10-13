#!/usr/bin/env python3
"""Qualify TYPE's raw page-key handling on disposable cpmsim media."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]
PROMPT=b'MORE -- ,/^R back; ./Space/^C next; </> files; ^Q quit.'

def main():
    p=argparse.ArgumentParser();p.add_argument('--image-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    work=a.report.resolve();work.mkdir(parents=True,exist_ok=False)
    shutil.copytree(a.image_dir/'disks',work/'disks');shutil.copy2(a.image_dir/'diskdefs',work/'diskdefs')
    disk=work/'disks/drivea.dsk'
    def cpm(tool,*values):
        subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,values)],cwd=work,check=True,stdout=subprocess.DEVNULL)
    cpm('cpmrm','0:*.*')
    binary=(ROOT/'build/utilities/TYPE.COM').read_bytes();(work/'TYPE.COM').write_bytes(binary)
    cpm('cpmcp',work/'TYPE.COM','0:TYPE.COM')
    cpm('cpmcp',ROOT/'build/cpx/RCP.CPX','0:RCP.CPX')
    source=b''.join(f'PAGE ROW {i:02d}\r\n'.encode() for i in range(55))+b'\x1aHIDDEN'
    (work/'LONG.TXT').write_bytes(source);cpm('cpmcp',work/'LONG.TXT','3:LONG.TXT');cpm('cpmchattr','rs','3:LONG.TXT')
    before=disk.read_bytes()
    steps=[(b':TYPE A3:LONG.TXT /P\r',PROMPT,60)]
    # Forward, backward, forward, EOF, EOF no-op, backward, quit.
    steps += [(key,PROMPT,60) for key in (b'\x03',b',',b' ',b'.')]
    steps += [(b'.',b'\x07',60),(b'\x12',PROMPT,60),(b'\x11',b'A0>_ ',60)]
    text=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',work/'disks',steps,work/'transcript.txt')
    assert text.count(b'PAGE ROW 00')==2 and text.count(b'PAGE ROW 54')==1 and b'HIDDEN' not in text,text[-2000:]
    assert disk.read_bytes()==before,'paging changed the source media'
    (work/'evidence.json').write_text(json.dumps({'result':'PASS','type_sha256':hashlib.sha256(binary).hexdigest(),'keys':['Ctrl-C',',','Space','.','.','Ctrl-R','Ctrl-Q'],'source_disk_unchanged':True},indent=2)+'\n')
    print('PASS: cpmsim TYPE page input, Ctrl-C next, backward replay, final EOF, Ctrl-Q quit and unchanged disk')
if __name__=='__main__':main()
