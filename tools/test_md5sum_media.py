#!/usr/bin/env python3
"""Run exact packaged MD5SUM and native tools on disposable BetterCP/M cpmsim disks."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
from test_z80pack_sysgen_install import session
from build_md5sum import ROOT


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image-dir',type=Path,required=True)
    p.add_argument('--utilities',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();w=a.report.resolve();w.mkdir(parents=True,exist_ok=False)
    shutil.copytree(a.image_dir/'disks',w/'disks')
    shutil.copy2(a.image_dir/'diskdefs',w/'diskdefs')
    original=(a.utilities/'BetterCPM-Utilities-z80pack-332K.dsk').read_bytes()
    (w/'disks/driveb.dsk').write_bytes(original)
    def cpm(tool,*args,disk='a'):
        return subprocess.run([tool,'-T','raw','-f','bettercpm-default',
                               str(w/f'disks/drive{disk}.dsk'),*map(str,args)],
                              cwd=w,check=True,capture_output=True)
    baseline=(a.image_dir/'disks/drivea.dsk').read_bytes()
    for letter in 'acd':
        (w/f'disks/drive{letter}.dsk').write_bytes(baseline)
        cpm('cpmrm','0:*.*',disk=letter)
    fixture=b'123456789'+b'\x1a'*119;large=bytes(range(256))*257
    inputs=[('FIX.DAT',fixture,'31:FIX.DAT'),('LARGE.DAT',large,'3:LARGE.DAT')]
    for name,payload,dest in inputs:
        (w/name).write_bytes(payload);cpm('cpmcp',w/name,dest)
    (w/'BAD.LST').write_bytes(b'0'*32+b' *FIX.DAT\r\n')
    cpm('cpmcp',w/'BAD.LST','31:BAD.LST')
    source=(a.utilities/'MD5SUM-NATIVE.MAC').read_bytes()
    assert source==(ROOT/'build/utilities/MD5SUM-NATIVE.MAC').read_bytes()
    (w/'MD5SUM.MAC').write_bytes(source)
    cpm('cpmcp',w/'MD5SUM.MAC','0:MD5SUM.MAC',disk='c')
    commands=[(b'D:\r',b'D0>_ ',30),
              (b'B:ZSM4 MD5SUM=C:MD5SUM\r',b'D0>_ ',60),
              (b'B:LINK MD5SUM[A]\r',b'D0>_ ',30),(b'A:\r',b'A0>_ ',30)]
    for command in (
        'B:MD5SUM /VER', 'B:MD5SUM /HELP /VER',
        'B:MD5SUM A31:FIX.DAT /LOCAL=MD5SUM.LST',
        'B:MD5SUM /CHECK A31:FIX.DAT',
        'B:MD5SUM A3:LARGE.DAT /LOCAL=MD5SUM.LST',
        'B:MD5SUM /CHECK A3:LARGE.DAT',
        'B:MD5SUM A31:FIX.DAT A3:LARGE.DAT /FILE=D:MASTER.LST /LOCAL=DU.LST',
        'B:MD5SUM /CHECK=DU.LST A31:FIX.DAT A3:LARGE.DAT',
        'B:MD5SUM /CHECK=BAD.LST A31:FIX.DAT',
        'B:MD5SUM A31:FIX.DAT /40'):
        commands.append(((command+'\r').encode(),b'A0>_ ',60))
    text=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',w/'disks',commands,w/'transcript.txt').decode('ascii',errors='replace')
    assert text.count('1 verified.')==2 and '2 verified.' in text,text[-5000:]
    assert 'MD5 MISMATCH' in text and '1 failed; incomplete.' in text,text[-3000:]
    assert 'Errors: 0' in text and 'CODE SIZE' in text,text[:3000]
    for name,payload,dest in inputs:
        out=w/('READ-'+name);cpm('cpmcp',dest,out);assert out.read_bytes()==payload
        out=w/(name+'.LST');cpm('cpmcp',dest.split(':')[0]+':MD5SUM.LST',out)
        assert out.read_bytes().split(b'\x1a')[0]==(hashlib.md5(payload).hexdigest()+' *'+name+'\r\n').encode()
    binary=(ROOT/'build/utilities/MD5SUM.COM').read_bytes()
    cpm('cpmcp','0:MD5SUM.COM',w/'NATIVE.COM',disk='d')
    assert (w/'NATIVE.COM').read_bytes()[:len(binary)]==binary
    cpm('cpmcp','0:MASTER.LST',w/'MASTER.LST',disk='d')
    expected=b''.join((hashlib.md5(payload).hexdigest()+' *'+name+'\r\n').encode() for name,payload,dest in inputs)
    assert (w/'MASTER.LST').read_bytes().split(b'\x1a')[0]==expected
    host=shutil.which('md5sum') or shutil.which('gmd5sum')
    host_check='not run (host md5sum unavailable)'
    if host:
        # The local Darwin checker accepts the conventional two-space/LF form.
        # Change list presentation only; checked target bytes remain exact.
        (w/'HOST.LST').write_bytes(expected.replace(b' *',b'  ').replace(b'\r\n',b'\n'))
        result=subprocess.run([host,'--check','HOST.LST'],cwd=w,check=True,capture_output=True)
        assert b'FIX.DAT: OK' in result.stdout and b'LARGE.DAT: OK' in result.stdout
        (w/'host-md5sum.txt').write_bytes(result.stdout)
        host_check='PASS: host md5sum --check (two-space/LF list, exact stored target bytes)'
    assert (w/'disks/driveb.dsk').read_bytes()==original
    evidence={'scope':'focused cpmsim candidate execution; Model 4 not qualified',
              'host_interoperability':host_check,
              'binary':{'bytes':len(binary),'sha256':sha(binary)},'native_source_sha256':sha(source),
              'platforms':{'z80pack':{'status':'PASS','system_sha256':sha(baseline),
                'utilities_sha256':sha(original),'utilities_unchanged':True,
                'fixtures_unchanged':True,'native_cross_parity':True}}}
    (w/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print('MD5SUM packaged cpmsim: native parity, >64K, user31, lists, negative check and unchanged inputs/B: PASS')


if __name__=='__main__':main()
