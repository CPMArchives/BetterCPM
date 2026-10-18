#!/usr/bin/env python3
"""Qualify shipped TYPE boundary navigation and immutable source media."""
import argparse,json,shutil,subprocess
from pathlib import Path
from run_validation_cpmsim_ren import audit
from run_validation_returning import sha
from test_z80pack_sysgen_install import session
MORE=b'MORE -- ,/^R back; ./Space/^C next; </> files; ^Q quit.'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();base=a.baseline.resolve();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False)
    report=json.loads((base/'report.json').read_text());(w/'disks').mkdir()
    for letter in 'ab':shutil.copy2(base/report['image'],w/'disks'/f'drive{letter}.dsk')
    shutil.copy2(base/'diskdefs',w/'diskdefs');shutil.copy2(__file__,w/'executed-runner.py')
    disk=w/'disks/driveb.dsk'
    def cpm(tool,*v):return subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,v)],cwd=w,check=True,capture_output=True)
    cpm('cpmrm','0:*.*')
    def rows(letter,n):return b''.join(f'{letter} ROW {i:02d}\r\n'.encode() for i in range(n))+b'\x1a'
    fixtures=[('AFILE.TXT',rows('A',5),3,'r'),('BFILE.TXT',rows('B',50),3,'s'),('CFILE.TXT',rows('C',1),3,''),
              ('AFILE.TXT',rows('A',1),5,''),('BFILE.TXT',b'',5,'a'),('CFILE.TXT',rows('C',1),5,''),('TABS.TXT',b'\tA\tB\r\n\x1a',7,'')]
    for name,data,user,attrs in fixtures:
        f=w/f'{user}-{name}';f.write_bytes(data);cpm('cpmcp',f,f'{user}:{name}')
        if attrs:cpm('cpmchattr',attrs,f'{user}:{name}')
    before=disk.read_bytes();sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim'
    steps=[(b':TYPE B3:*.TXT /P\r',MORE,60)]
    steps += [(key,MORE,60) for key in (b'>',b'<',b'.',b'<',b'>')]
    steps += [(b'>',b'\x07',60),(b'<',MORE,60),(b'\x11',b'A0>_ ',60)]
    text=session(sim,w/'disks',steps,w/'long.txt')
    assert text.count(b'A ROW 00')==2 and text.count(b'B ROW 00')==5 and b'C ROW 00' in text
    steps=[(b':TYPE B5:*.TXT /P\r',MORE,60)]
    steps += [(key,MORE,60) for key in (b'>',b'>')]
    steps += [(b'>',b'\x07',60),(b'<',MORE,60),(b'\x11',b'A0>_ ',60)]
    text=session(sim,w/'disks',steps,w/'short.txt')
    assert text.count(b'B5:BFILE.TXT')==3 and text.count(b'C ROW 00')==4
    text=session(sim,w/'disks',[(b':TYPE B7:TABS.TXT /P\r',MORE,60),(b'\x11',b'A0>_ ',60)],w/'tabs.txt')
    assert b'        A       B' in text
    text=session(sim,w/'disks',[(b'TYPE B7:TABS.TXT\r',b'A0>_ ',60)],w/'resident.txt')
    assert b'        A       B' in text
    assert disk.read_bytes()==before,'TYPE changed source media'
    shipped=audit(base,report,w,w/'disks/drivea.dsk')
    r=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(disk)],cwd=w,capture_output=True,check=True)
    (w/'filesystem-b.txt').write_bytes(r.stdout+r.stderr)
    (w/'result.json').write_text(json.dumps({'status':'PASS','runner_sha256':sha(Path(__file__)),'baseline_sha256':report['sha256'],'simulator_sha256':sha(sim),'unchanged_shipped_files':shipped,'source_disk_unchanged':True},indent=2)+'\n')
    print('PASS shipped TYPE file boundaries, empty files, paging and tabs',w)

if __name__=='__main__':main()
