#!/usr/bin/env python3
"""Qualify TYPE file boundaries and final cross-file EOF on real emulator media."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from test_disk_utilities import ROOT,medium,keys
from test_z80pack_sysgen_install import session
from test_sysgen_install import screen
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run
PROMPT='MORE -- ,/^R back; ./Space/^C next; </> files; ^Q quit.'

def main():
    p=argparse.ArgumentParser();p.add_argument('--platform',choices=('z80pack','model4'),required=True);p.add_argument('--image-dir',type=Path);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    work=a.report.resolve();work.mkdir(parents=True,exist_ok=False)
    def rows(letter,n):return b''.join(f'{letter} ROW {i:02d}\r\n'.encode() for i in range(n))+b'\x1a'
    fixtures=[('AFILE.TXT',rows('A',5),3,1),('BFILE.TXT',rows('B',50),3,2),('CFILE.TXT',rows('C',1),3,0),
              ('AFILE.TXT',rows('A',1),5,0),('BFILE.TXT',b'',5,4),('CFILE.TXT',rows('C',1),5,0)]
    binary=(ROOT/'build/utilities/TYPE.COM').read_bytes()
    if a.platform=='z80pack':
        assert a.image_dir
        shutil.copytree(a.image_dir/'disks',work/'disks');shutil.copy2(a.image_dir/'diskdefs',work/'diskdefs')
        disk=work/'disks/drivea.dsk'
        def cpm(tool,*values):
            subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,values)],cwd=work,check=True,stdout=subprocess.DEVNULL)
        cpm('cpmrm','0:*.*')
        (work/'TYPE.COM').write_bytes(binary);cpm('cpmcp',work/'TYPE.COM','0:TYPE.COM');cpm('cpmcp',ROOT/'build/cpx/RCP.CPX','0:RCP.CPX')
        for name,data,user,mask in fixtures:
            f=work/f'{user}-{name}';f.write_bytes(data);cpm('cpmcp',f,f'{user}:{name}')
            if mask:cpm('cpmchattr','r' if mask==1 else 's' if mask==2 else 'a',f'{user}:{name}')
        before=disk.read_bytes();sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim'
        steps=[(b':TYPE A3:*.TXT /P\r',PROMPT.encode(),60)]
        steps += [(key,PROMPT.encode(),60) for key in (b'>',b'<',b'.',b'<',b'>')]
        steps += [(b'>',b'\x07',60),(b'<',PROMPT.encode(),60),(b'\x11',b'A0>_ ',60)]
        text=session(sim,work/'disks',steps,work/'long.txt')
        assert text.count(b'A ROW 00')==2 and text.count(b'B ROW 00')==5 and b'C ROW 00' in text,text[-3000:]
        steps=[(b':TYPE A5:*.TXT /P\r',PROMPT.encode(),60)]
        steps += [(key,PROMPT.encode(),60) for key in (b'>',b'>')]
        steps += [(b'>',b'\x07',60),(b'<',PROMPT.encode(),60),(b'\x11',b'A0>_ ',60)]
        text=session(sim,work/'disks',steps,work/'short.txt')
        assert text.count(b'A5:BFILE.TXT')==3 and text.count(b'C ROW 00')==4,text[-3000:]
        assert disk.read_bytes()==before,'file navigation changed source media'
    else:
        disk=work/'a.dmk';original=medium([('TYPE.COM',binary),*fixtures]);disk.write_bytes(original)
        invocation=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(disk),'-id','3000','-it']
        invocation+=keys(':TYPE A3:*.TXT /P\r')+['-itime','0','-iw',PROMPT,'-it']
        for key,marker in [('>','B ROW 21'),('<','A ROW 00'),('.','B ROW 36'),('<','B ROW 00'),('>','C ROW 00')]:
            invocation+=keys(key)+['-iw',marker,'-iw',PROMPT,'-it']
        invocation+=keys('>')+['-id','1000','-it']
        invocation+=keys('<')+['-iw','B ROW 00','-iw',PROMPT,'-it']
        invocation+=keys('\x11')+['-iw','A0>','-it']
        invocation+=['-id','1000']+keys(':TYPE A5:*.TXT /P\r')+['-id','2000','-it','-iw',PROMPT,'-it']
        for key in ('>','>','>','<'):
            invocation+=keys(key)+['-id','2000','-it']
        invocation+=keys('\x11')+['-iw','A0>','-it','-ix']
        (work/'invocation.json').write_text(json.dumps(invocation,indent=2)+'\n')
        run(invocation,cwd=work,timeout=300,check=True)
        captures=sorted(work.glob('trs80-text-*.bin'),key=lambda f:int(f.stem.rsplit('-',1)[1]));texts=[screen(f) for f in captures]
        for f,text in zip(captures,texts):f.with_suffix('.txt').write_text(text)
        assert len(texts)==17,len(texts)
        for i,name in [(2,'A3:BFILE.TXT'),(3,'A3:AFILE.TXT'),(5,'A3:BFILE.TXT'),(6,'A3:CFILE.TXT'),(8,'A3:BFILE.TXT'),(12,'A5:BFILE.TXT'),(13,'A5:CFILE.TXT'),(14,'A5:CFILE.TXT'),(15,'A5:BFILE.TXT')]:
            assert texts[i].splitlines()[0].startswith('---------- '+name+' ----------'),(i,texts[i])
        assert disk.read_bytes()==original,'file navigation changed Model 4 media'
    (work/'evidence.json').write_text(json.dumps({'result':'PASS','platform':a.platform,'type_sha256':hashlib.sha256(binary).hexdigest(),'whole_disk_unchanged':True,'file_boundaries_at_final_EOF':True},indent=2)+'\n')
    print(f'PASS: {a.platform} TYPE file boundaries, final cross-file EOF, empty files, previous-file behavior and unchanged disk')
if __name__=='__main__':main()
