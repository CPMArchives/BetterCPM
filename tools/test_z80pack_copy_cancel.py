#!/usr/bin/env python3
"""Deliver actual Ctrl-C at deterministic native COPY record boundaries."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from test_disk_utilities import ROOT
from test_z80pack_sysgen_install import session


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--image-dir',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args()
    report=args.report.resolve(); report.mkdir(parents=True,exist_ok=False)
    shutil.copytree(args.image_dir/'disks',report/'disks')
    shutil.copy2(args.image_dir/'diskdefs',report/'diskdefs')
    a,b=[report/'disks'/f'drive{x}.dsk' for x in 'ab']
    b.write_bytes(bytes([229])*len(b.read_bytes()))
    def cpm(tool,disk,*values):
        subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,values)],cwd=report,check=True)
    values={'A.DAT':b'A'*128,'B.DAT':bytes(range(256))*130}
    for name,data in values.items():
        f=report/name; f.write_bytes(data); cpm('cpmcp',b,f,'1:'+name)
    original=(ROOT/'build/utilities/COPY.COM').read_bytes()
    listing=(ROOT/'build/utilities/copy-transient.lst').read_text()
    def addr(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
    def word(n): return n.to_bytes(2,'little')
    results=[]
    for user,phase in [(3,'BC_CLOOP'),(4,'CTVLOOP')]:
        image=bytearray(original)
        entry=256+len(image)
        # Test-only wrapper pauses at the fourth poll, then calls the real
        # nonblocking keyboard checker until the harness supplies Ctrl-C.
        # All production abort/cleanup paths remain unchanged.
        flag=entry+29; message=entry+30
        code=b'\x21'+word(flag)+b'\x7e\xb7\xc8\x35\xca'+word(entry+13)+b'\xb7\xc9\x00'
        assert len(code)==13
        code+=b'\x11'+word(message)+b'\x0e\x09\xcd\x05\x00'
        code+=b'\xcd'+word(addr('CTCHECK'))+b'\x30\xfb\xc9\x00\x00\x04READY$'
        assert code[29]==4
        call=addr(phase)-256
        assert image[call:call+3]==b'\xcd'+word(addr('CTCHECK'))
        image[call+1:call+3]=word(entry); image+=code
        proof=report/'COPY.COM'; proof.write_bytes(image)
        subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(a),'0:COPY.COM'],cwd=report,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        cpm('cpmcp',a,proof,'0:COPY.COM')
        simulator=Path.home()/'projects/git/z80pack/cpmsim/cpmsim'
        command=f'COPY B1:*.DAT B{user}: /B'+(' /V' if phase=='CTVLOOP' else '')
        text=session(simulator,report/'disks',[(b'CPX UNLOAD RCP\r',b'A0>_ ',30),
            (command.encode()+b'\r',b'READY',60),(b'\x03',b'A0>_ ',60)],report/(phase+'.txt'))
        assert b'COPY ABORTED' in text and b'VERIFY ERROR' not in text
        for name in values:
            f=report/f'{user}-{name}'
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(b),f'{user}:{name}',str(f)],cwd=report,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            assert f.exists()==(name=='A.DAT'),(phase,name)
            if f.exists(): assert f.read_bytes()==values[name]
        proof.write_bytes(original)
        cpm('cpmrm',a,'0:COPY.COM'); cpm('cpmcp',a,proof,'0:COPY.COM')
        session(simulator,report/'disks',[(b'CPX UNLOAD RCP\r',b'A0>_ ',30),
            (b'COPY B1:B.DAT B5: /B\r',b'A0>_ ',60)],report/f'{phase}-reuse.txt')
        f=report/f'{user}-reuse.dat'; cpm('cpmcp',b,'5:B.DAT',f)
        assert f.read_bytes()==values['B.DAT']
        for name,data in values.items():
            f=report/f'{user}-source-{name}'; cpm('cpmcp',b,'1:'+name,f)
            assert f.read_bytes()==data
        # Remove the allocation-reuse result before the next test.
        cpm('cpmrm',b,'5:B.DAT')
        results.append(phase)
    (report/'evidence.json').write_text(json.dumps({'result':'PASS','phases':results,
        'real_ctrl_c':True,'prior_file_preserved':True,'incomplete_destination_removed':True,
        'subsequent_copy_succeeds':True,'copy_sha256':hashlib.sha256(original).hexdigest()},indent=2)+'\n')
    print('Native COPY transfer/verification Ctrl-C cleanup and completed-file preservation pass')


if __name__=='__main__': main()
