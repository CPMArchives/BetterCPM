#!/usr/bin/env python3
"""Qualify /V integration and controlled post-close verification failures."""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from test_disk_utilities import ROOT
from test_z80pack_sysgen_install import session


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--image-dir', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    shutil.copytree(args.image_dir / 'disks', report / 'disks')
    shutil.copy2(args.image_dir / 'diskdefs', report / 'diskdefs')
    a, b = [report / 'disks' / f'drive{x}.dsk' for x in 'ab']
    b.write_bytes(bytes([229])*len(b.read_bytes()))
    def cpm(tool, disk, *values):
        subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,values)],cwd=report,check=True)
    data = bytes(range(256))*130
    source = report / 'source.dat'; source.write_bytes(data)
    cpm('cpmcp', b, source, '1:DATA.DAT')
    cpm('cpmchattr', b, 'rs', '1:DATA.DAT')
    base = (ROOT / 'build/utilities/COPY.COM').read_bytes()
    listing = (ROOT / 'build/utilities/copy-transient.lst').read_text()
    def addr(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
    def install(mode):
        image = bytearray(base)
        if mode == 'always':
            off = addr('CTVERIFY')-256
            image[off:off+2] = b'\x37\xc9'  # controlled verification failure
        if mode == 'once':
            # Replace the post-close call with a one-shot failure wrapper.
            off = addr('CTVPOST')-256
            call = image.index(b'\xcd'+addr('CTVERIFY').to_bytes(2,'little'),off)
            entry = 256+len(image)
            flag = entry+16
            image[call+1:call+3] = entry.to_bytes(2,'little')
            shim = b'\xcd'+addr('CTVERIFY').to_bytes(2,'little')+b'\xd8'
            shim += b'\x21'+flag.to_bytes(2,'little')+b'\x7e\xb7\xc8\x36\x00\x37\xc9\x00\x00\x01'
            assert len(shim)==17
            image += shim
        f = report / 'COPY.COM'; f.write_bytes(image)
        subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(a),'0:COPY.COM'],cwd=report,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        cpm('cpmcp',a,f,'0:COPY.COM')
    def execute(command, replies, label):
        steps=[(b'CPX UNLOAD RCP\r',b'A0>_ ',30),(command.encode()+b'\r',b' [VERIFY ERROR] R/S/? ' if replies else b'A0>_ ',60)]
        steps += [(reply,wanted,60) for reply,wanted in replies]
        return session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',report/'disks',steps,report/(label+'.txt'))
    def check(user, exists):
        f=report/f'out-{user}.dat'
        result=subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(b),f'{user}:DATA.DAT',str(f)],cwd=report,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        assert f.exists()==exists,(user,result.stderr)
        if exists: assert f.read_bytes()==data,user
    install('normal')
    for user, options in [(3,'/V'),(4,'/B /V /V'),(5,'/O /V'),(6,'/S /V')]:
        command = f'COPY B1:DATA.DAT B{user}: {options}'
        if user == 3: command = 'COPY /V B1:DATA.DAT B3:'
        if user == 4: command = 'COPY /B /V B4: = B1:DATA.DAT /V'
        text=execute(command,[],f'normal-{user}')
        assert b'VERIFY ERROR' not in text and b'COPY source' not in text
        check(user,True)
    for index, command in enumerate([
        'COPY /O B1:DATA.DAT B13: /S',
        'COPY /S B1:DATA.DAT B13: /O',
        'COPY /BACKUP B1:DATA.DAT B13:',
        'COPY /V B1:DATA.DAT[$ARC] B13:']):
        before = b.read_bytes()
        text=execute(command,[],f'rejected-options-{index}')
        assert b'COPY source destination' in text
        assert b.read_bytes()==before
    install('always')
    text=execute('COPY B1:DATA.DAT B7: /B /V',[],'batch-failure')
    assert b'VERIFY ERROR' in text; check(7,False)
    text=execute('COPY B1:DATA.DAT B8: /V',[(b'?',b' [VERIFY ERROR] R/S/? '),(b'!',b' [VERIFY ERROR] R/S/? '),(b's',b'A0>_ ')],'skip-failure')
    assert b'R - Retry  S - Skip' in text; check(8,False)
    execute('COPY B1:DATA.DAT B9: /V',[(b'\x03',b'A0>_ ')],'abort-failure'); check(9,False)
    # No /V: the injected comparison failure must not affect ordinary copying.
    execute('COPY B1:DATA.DAT B10:',[],'no-verification'); check(10,True)
    cpm('cpmcp', b, source, '1:SECOND.DAT')
    text=execute('COPY B1:*.DAT B12: /B /V',[],'batch-continues')
    assert text.count(b' [VERIFY ERROR]')==2
    check(12,False)
    missing=report/'second-removed.dat'
    subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(b),'12:SECOND.DAT',str(missing)],cwd=report,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert not missing.exists()
    install('once')
    execute('COPY B1:DATA.DAT B11: /V',[(b'r',b'A0>_ ')],'retry-success'); check(11,True)
    # Inspect the actual skewed directory, including attributes applied only
    # after successful verification/retry.
    raw=b.read_bytes()
    directory=b''.join(raw[6*18*256+n*256:6*18*256+(n+1)*256]
                       for n in [0,4,8,12,16,2,6,10])
    for user in (3,11):
        entries=[directory[i:i+32] for i in range(0,len(directory),32)
                 if directory[i]==user and bytes(x & 127 for x in directory[i+1:i+12])==b'DATA    DAT']
        assert entries and all(e[9]&128 and e[10]&128 for e in entries),user
    f=report/'source-after.dat'; cpm('cpmcp',b,'1:DATA.DAT',f)
    assert f.read_bytes()==data
    (report/'evidence.json').write_text(json.dumps({'result':'PASS','cases':['normal','options','batch-failure','help-skip','abort-cleanup','no-V','retry-success','batch-continues'],'fault_injection':'test binary only'},indent=2)+'\n')
    print('Native COPY /V success, retry, skip, batch and abort cleanup pass')


if __name__=='__main__': main()
