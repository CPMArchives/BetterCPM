#!/usr/bin/env python3
"""Qualify /D zeroing, shared-block preservation and E5/zero directory scrub."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from run_validation_cpmsim_monitors import audit
from run_validation_returning import sha
from test_z80pack_sysgen_install import session

SKEW=[0,4,8,12,16,2,6,10,14,1,5,9,13,17,3,7,11,15]

def record_offset(record):
    track,sector=divmod(record,36)
    physical,quarter=divmod(sector,2)
    return (track+6)*18*256+SKEW[physical]*256+quarter*128

def entries(image):
    directory=b''.join(image[record_offset(n):record_offset(n)+128] for n in range(16))
    return [directory[n:n+32] for n in range(0,len(directory),32)]

def blocks(rows,user,name):
    result=set()
    for row in rows:
        if row[0]==user and bytes(v&127 for v in row[1:12])==name:
            result.update(row[16:32])
    return result-{0}

def main():
    p=argparse.ArgumentParser();p.add_argument('--image-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    w=a.report.resolve();w.mkdir(parents=True,exist_ok=False)
    baseline=a.image_dir.resolve();manifest=json.loads((baseline/'report.json').read_text())
    (w/'disks').mkdir()
    for letter in 'ab':shutil.copy2(baseline/manifest['image'],w/'disks'/('drive'+letter+'.dsk'))
    shutil.copy2(a.image_dir/'diskdefs',w/'diskdefs');shutil.copy2(__file__,w/'executed-runner.py')
    disk=w/'disks/driveb.dsk';system=w/'disks/drivea.dsk'
    def cpm(tool,image,*args):
        return subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(image),*map(str,args)],cwd=w,check=True,capture_output=True)
    cpm('cpmrm',disk,'0:*.*')
    for user,name,size in ((1,'WIPE.DAT',33024),(2,'SHARED.DAT',4096),(3,'KEEP.DAT',2048),(4,'READONLY.DAT',128),(5,'EMPTY.DAT',0),(6,'SAFE.DAT',128),(7,'N1.DAT',128),(7,'N2.DAT',128),(8,'ASK.DAT',128),(9,'ROASK.DAT',128)):
        f=w/(str(user)+'-'+name);f.write_bytes(name.encode().ljust(size,b'X') if size else b'')
        cpm('cpmcp',disk,f,str(user)+':'+name)
    cpm('cpmchattr',disk,'r','4:READONLY.DAT')
    cpm('cpmchattr',disk,'r','9:ROASK.DAT')
    image=bytearray(disk.read_bytes());before=entries(image)
    keepblock=next(iter(blocks(before,3,b'KEEP    DAT')))
    shared_index=next(n for n,row in enumerate(before) if row[0]==2)
    offset=record_offset(shared_index//4)+(shared_index%4)*32
    image[offset+17]=keepblock
    disk.write_bytes(image);before=entries(image);original=bytes(image)
    def execute(command,label):
        text=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',w/'disks',[(command.encode()+b'\r',b'A0>_ ',90)],w/(label+'.txt'))
        return text
    def scrubbed(user):
        after=entries(disk.read_bytes())
        for n,row in enumerate(before):
            if row[0]==user:assert after[n]==bytes([229])+bytes(31),(user,n,after[n])
    def zeroed(numbers):
        actual=disk.read_bytes()
        for block in numbers:
            for record in range(block*16,(block+1)*16):
                offset=record_offset(record)
                assert actual[offset:offset+128]==bytes(128),(block,record)
    text=execute(':ERA /D /Y B1:WIPE.DAT','multi-extent')
    assert b'1 FILES DESTRUCTIVELY ERASED' in text,text[-1000:]
    scrubbed(1);zeroed(blocks(before,1,b'WIPE    DAT'))
    text=execute(':ERA /D /Y B2:SHARED.DAT','shared-other-user')
    assert b'erased; shared blocks retained' in text,text[-1000:]
    assert b'1 ERASED WITH SHARED BLOCKS RETAINED, 2K FREED' in text,text[-1000:]
    scrubbed(2);zeroed(blocks(before,2,b'SHARED  DAT')-{keepblock})
    for record in range(keepblock*16,(keepblock+1)*16):
        off=record_offset(record);assert disk.read_bytes()[off:off+128]==original[off:off+128]
    text=execute(':ERA /D /Y /R B4:READONLY.DAT[$RO]','ro-authorized')
    assert b'1 FILES DESTRUCTIVELY ERASED' in text,text[-1000:]
    scrubbed(4);zeroed(blocks(before,4,b'READONLYDAT'))
    execute(':ERA /D /Y B5:EMPTY.DAT','empty-file');scrubbed(5)
    text=execute(':ERA /D /Y B7:*.DAT','two-files-one-invocation')
    assert b'2 FILES DESTRUCTIVELY ERASED' in text
    scrubbed(7);zeroed(blocks(before,7,b'N1      DAT')|blocks(before,7,b'N2      DAT'))
    saved_cancel=disk.read_bytes()
    text=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',w/'disks',
        [(b':ERA /D B8:ASK.DAT\r',b'This is unrecoverable. Y/N ',30),(b'N',b'A0>_ ',30)],w/'destructive-no.txt')
    assert disk.read_bytes()==saved_cancel and b'ERA cancelled.' in text
    text=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',w/'disks',
        [(b':ERA /D /C B9:ROASK.DAT[$RO]\r',b'Read only. Destructively erase? This is unrecoverable. Y/N ',30),(b'Y',b'A0>_ ',60)],w/'destructive-ro-prompt.txt')
    assert text.count(b'This is unrecoverable. Y/N ')==1
    scrubbed(9);zeroed(blocks(before,9,b'ROASK   DAT'))
    shipped=audit(baseline,manifest,w,system)
    check=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(disk)],cwd=w,capture_output=True,check=True)
    (w/'secondary-filesystem.txt').write_bytes(check.stdout+check.stderr)
    (w/'result.json').write_text(json.dumps({'status':'PASS','unchanged_shipped_files':shipped,'baseline_sha256':manifest['sha256'],'runner_sha256':sha(Path(__file__)),'scope':'multi-extent zero/scrub, cross-user shared block retention, admitted RO override, empty and batch erase, cancellation and single RO authorization'},indent=2)+'\n')
    print('PASS shipped destructive ERA',w)

if __name__=='__main__':main()
