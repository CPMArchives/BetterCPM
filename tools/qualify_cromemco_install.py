#!/usr/bin/env python3
"""Qualify native SYSGEN, saved CONFIG/PDS and DUP on private Cromemco media."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from test_cromemco_system import Terminal
from startup_record import choices, parse

ROOT=Path(__file__).resolve().parents[1]
RESERVED=8*26*128


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image-dir',type=Path,required=True)
    p.add_argument('--simulator',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); src=a.image_dir.resolve(); out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    master=(src/'disks/drivea.dsk').read_bytes()
    info=json.loads((src/'candidate.json').read_text())
    def work(name, system=master):
        w=out/name; w.mkdir(); shutil.copytree(src/'disks',w/'disks')
        for n in ('system.conf','diskdefs'):shutil.copy2(src/n,w/n)
        (w/'disks/drivea.dsk').write_bytes(system)
        return w
    def start(w):
        t=Terminal(a.simulator.resolve(),w); t.prompt(); return t
    def interactive(t,command,question,answer,completion):
        t.cursor=len(t.data);t.type_command(command)
        t.expect(question);os.write(t.master,answer);t.expect(completion);t.prompt()
    w=work('install')
    dest=w/'disks/driveb.dsk';dest.write_bytes(b'\xe5'*RESERVED+master[RESERVED:])
    t=start(w)
    try:
        t.send('CONFIG /SHOW','Saved logical-drive bindings:')
        interactive(t,'SYSGEN SYSTEM.SYS B:',r'Proceed \(Y/N\)\?',b'Y','System installed and verified.')
    finally:t.close()
    installed=dest.read_bytes()
    assert installed[RESERVED:]==master[RESERVED:],'installation changed populated filesystem'
    assert installed[:160*128]==master[:160*128],'installation differs from source package'
    c=work('installed-cold',installed); t=start(c)
    try:
        t.send('VER','BetterCP/M 1.3');t.send('STAT MEM','Maximum loadable COM: 57344 bytes')
        interactive(t,'CONFIG /STARTUP="VER"','Save pending cold-boot changes',b'Y','Pending cold-boot changes saved and verified.')
        interactive(t,'CONFIG /IOBYTE=85','Save disk-boot IOBYTE',b'Y','IOBYTE')
    finally:t.close()
    saved=(c/'disks/drivea.dsk').read_bytes()
    assert parse(saved[128:384],system_base=info['layout']['SYSTEM'])=='VER'
    c=work('saved-cold',saved);t=start(c)
    try:
        assert b'BetterCP/M 1.3' in t.data,'saved startup did not execute'
        t.send('CONFIG /SHOW','Live IOBYTE (decimal): 85')
        t.cursor=len(t.data);t.type_command('CONFIG');t.expect('Your choice:')
        os.write(t.master,b'F');t.expect('Pending choices H/M/V: 2 0 0')
        os.write(t.master,b'B');t.expect('Pending choices H/M/V: 2 1 0')
        for value in (1,2,3):
            os.write(t.master,b'C');t.expect('Pending choices H/M/V: 2 1 '+str(value))
        t.expect('Your choice:');t.expect(r'\[ \]\x08\x08')
        time.sleep(0.05)  # let the final BDOS output call return before ^C
        os.write(t.master,b'\x03');t.expect(r'Select \[ A - F or S \]');t.expect('Your choice:')
        os.write(t.master,b'S');t.expect('Save pending cold-boot changes only')
        os.write(t.master,b'A');t.expect(r'\(Y/N\)\?');os.write(t.master,b'Y')
        t.expect('Pending cold-boot changes saved and verified.')
    finally:t.close()
    enabled=(c/'disks/drivea.dsk').read_bytes()
    assert choices(enabled[128:384],system_base=info['layout']['SYSTEM'])==(2,1,3)
    c=work('enabled-cold',enabled)
    from test_submit_xsub import marker
    program=marker(c)
    (c/'MARK.COM').write_bytes(program)
    subprocess.run(['cpmcp','-T','raw','-f','bettercpm-cromemco',str(c/'disks/driveb.dsk'),str(c/'MARK.COM'),'0:MARK.COM'],cwd=c,check=True)
    t=start(c)
    try:
        t.send('STAT MEM','Maximum loadable COM: 56704 bytes')
        t.send('VAR X=One;B:MARK %X%;VAR X=Two;B:MARK %X%','MARK: Two')
        t.send('VAR X','X=Two')
        t.send('B:MARK FIRST;B:MARK %X%','MARK: Two')
        t.send('RSX LOAD NDR')
        t.send('NDR WORK B0:')
        t.send('WORK:MARK NAMED','MARK: NAMED')
        t.send('RSX UNLOAD NDR')
        t.send('PATH B0:')
        t.send('MARK PATH','MARK: PATH')
        t.send('A:PATH /DEFAULT')
        t.cursor=len(t.data);t.type_command('DUP /FORMAT D:');t.expect(r'\[Y/N\]')
        os.write(t.master,b'Y');t.expect('Format complete.',timeout=60);t.prompt()
        t.send('DUP /CHECK D:','Check complete. Unreadable sectors: 0')
        assert (c/'disks/drived.dsk').read_bytes()==b'\xe5'*len(master),'format did not erase every sector'
        interactive(t,'DUP /COPY A: D:',r'\[Y/N\]',b'Y','Copy complete; destination verified.')
    finally:t.close()
    assert (c/'disks/drived.dsk').read_bytes()==(c/'disks/drivea.dsk').read_bytes(),'DUP copy differs from source'
    assert (src/'disks/drivea.dsk').read_bytes()==master,'master changed'
    result={'status':'PASS','system_sha256':hashlib.sha256(master).hexdigest(),
            'checks':['SYSGEN populated destination filesystem preserved','independent installed cold boot',
                      'CONFIG STARTUP and IOBYTE cold persistence','CONFIG saved MCL/VAR/PDS composition',
                      'enabled MCL/VAR substitution across transient warm returns','NDR and PATH',
                      'DUP fixed-format erase, check, full copy and verification','release master unchanged']}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: Cromemco installation, saved configuration, enabled PDS/MCL/VAR, NDR/PATH and DUP')


if __name__=='__main__':main()
