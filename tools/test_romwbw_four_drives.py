#!/usr/bin/env python3
"""Verify four-drive persistence and allocation isolation with unclosed FCBs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import struct
from build_ccp import assemble
from romwbw_media import SIZE,configuration
from test_romwbw_system import Terminal


PROBE="""        ASEG
        ORG 0100H
        LD SP,01F00H
        LD B,0
        LD C,181
        CALL 5
        LD DE,5
        ADD HL,DE
        LD A,(HL)
        CP 4
        JP NZ,BAD
        LD DE,INVALID
        LD B,3
        LD C,181
        CALL 5
        LD A,H
        OR A
        JP NZ,BAD
        LD A,L
        CP 1
        JP NZ,BAD
        LD DE,BFILE
        LD C,22
        CALL 5
        INC A
        JP Z,BAD
        LD DE,CFILE
        LD C,22
        CALL 5
        INC A
        JP Z,BAD
LOOP:
        LD A,(RECORD)
        XOR 0B1H
        LD HL,BUFFER
        LD B,128
FILLB:
        LD (HL),A
        INC HL
        DJNZ FILLB
        LD DE,BUFFER
        LD C,26
        CALL 5
        LD DE,BFILE
        LD C,21
        CALL 5
        OR A
        JP NZ,BAD
        LD A,(RECORD)
        XOR 0C1H
        LD HL,BUFFER
        LD B,128
FILLC:
        LD (HL),A
        INC HL
        DJNZ FILLC
        LD DE,CFILE
        LD C,21
        CALL 5
        OR A
        JP NZ,BAD
        LD A,(RECORD)
        INC A
        LD (RECORD),A
        CP 163
        JR NZ,LOOP
        LD DE,BFILE
        LD C,16
        CALL 5
        INC A
        JP Z,BAD
        LD DE,CFILE
        LD C,16
        CALL 5
        INC A
        JP Z,BAD
        LD DE,PASS
        JR DONE
BAD:    LD DE,FAIL
DONE:   LD C,9
        CALL 5
        JP 0
BFILE: DB 2,'ALVB    BIN'
        DS 24,0
CFILE: DB 3,'ALVC    BIN'
        DS 24,0
INVALID: DB 4
        DS 79,0
RECORD: DB 0
PASS: DB 'FOUR DRIVE ALLOCATION PASS',13,10,'$'
FAIL: DB 'FOUR DRIVE ALLOCATION FAIL',13,10,'$'
BUFFER: DS 128
        END
"""


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('image-dir','simulator','rom','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();image=a.image_dir.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    shutil.copy2(image/'system.img',out/'system.img');shutil.copy2(image/'diskdefs',out/'diskdefs')
    for name in ('b','c','d'):(out/(name+'.img')).write_bytes(b'\xe5'*SIZE)
    assemble(Path.home()/'bin/z80asm',PROBE,out/'ALVTEST.COM',out/'alvtest.lst',0x100)
    subprocess.run(['cpmcp','-T','raw','-f','bettercpm-romwbw',str(out/'system.img'),
                    str(out/'ALVTEST.COM'),'0:ALVTEST.COM'],cwd=out,check=True)
    checks=[]
    def terminal(label,source=None):
        work=out/label;work.mkdir()
        command=[str(a.simulator.resolve()),'--romwbw='+str(a.rom.resolve()),
                 '--disk0='+str(source or out/'system.img'),
                 *['--disk'+str(i+1)+'='+str(out/(letter+'.img')) for i,letter in enumerate('bcd')],
                 '--boot=2','--no-config','--strict-io','--max-instructions=4000000000']
        return Terminal(a.simulator.resolve(),work,command=command)
    t=terminal('mappings')
    try:
        t.prompt()
        for letter,unit in zip('BCD',(3,4,5)):
            t.send('CONFIG /LOGICAL='+letter+' /UNIT='+str(unit),letter+': binding updated.')
        t.type_command('ALVTEST');t.expect('FOUR DRIVE ALLOCATION PASS',timeout=180);t.prompt()
        t.send('CONFIG /LOGICAL=C /UNIT=3','CONFIG failed')
        t.send('CONFIG /SHOW','C: HBIOS unit 4')
        t.send('CONFIG /LOGICAL=B /UNIT=5','CONFIG failed')
        t.send('CONFIG /SHOW','B: HBIOS unit 3')
        t.type_command('CONFIG');t.expect('Select A/B/C/F/S')
        t.expect(r'Your choice: \[ \]\x08\x08');os.write(t.master,b'C')
        t.expect('Selected drive: B');t.expect(r'Your choice: \[ \]\x08\x08')
        os.write(t.master,b'D');t.expect('Selected drive: D')
        t.expect(r'Your choice: \[ \]\x08\x08');os.write(t.master,b'N')
        t.expect('HBIOS unit [(]decimal, 0..254[)]: ');os.write(t.master,b'5\r')
        t.expect('D: binding updated.');t.expect('Push ENTER for menu.');os.write(t.master,b'\r')
        t.expect('Selected drive: D');t.expect(r'Your choice: \[ \]\x08\x08')
        os.write(t.master,b'\x03');t.expect('Select A/B/C/F/S')
        t.expect(r'Your choice: \[ \]\x08\x08');os.write(t.master,b'\x03');t.prompt()
        t.send('CONFIG /SAVE','Block configuration saved and verified.')
        checks+=['all three nonboot mappings configured','descriptor count and invalid index rejection',
                 'interactive block menu selects D and binds the selected drive','163 alternating writes to two unclosed FCBs',
                 'aliases of another writable logical drive rejected without mutation']
    finally:t.close()
    if (out/'system.img').read_bytes()[2048:2560]!=configuration(3,c_unit=4,d_unit=5):
        raise AssertionError('saved mappings differ')
    for letter,seed in (('b',0xb1),('c',0xc1)):
        extracted=out/(letter+'.bin')
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-romwbw',str(out/(letter+'.img')),
                        '0:ALV'+letter.upper()+'.BIN',str(extracted)],cwd=out,check=True)
        expected=b''.join(bytes((record^seed,))*128 for record in range(163))
        if extracted.read_bytes()!=expected:raise AssertionError('allocation isolation failed: '+letter)
    checks.append('independent host extraction matches both complete file patterns')
    t=terminal('cold-mappings')
    try:
        t.prompt()
        for letter,unit in zip('BCD',(3,4,5)):t.send('CONFIG /SHOW',letter+': HBIOS unit '+str(unit))
        t.send('CONFIG /LOGICAL=C /UNBIND /SAVE','Block configuration saved and verified.')
        t.send('CONFIG /SHOW','D: HBIOS unit 5')
        t.send('STAT MEM','Maximum loadable COM: 57344 bytes')
        checks+=['saved B/C/D mappings restored at cold boot','C unbind preserves B and D',
                 'default 56 KiB COM capacity preserved']
    finally:t.close()
    if (out/'system.img').read_bytes()[2048:2560]!=configuration(3,d_unit=5):
        raise AssertionError('unbinding C changed another saved binding')
    # A checksummed but unsuitable saved alias must be ignored independently.
    source=bytearray((out/'system.img').read_bytes());source[2048:2560]=configuration(3,c_unit=3,d_unit=5)
    alias=out/'saved-alias.img';alias.write_bytes(source)
    t=terminal('saved-alias',alias)
    try:
        t.prompt();t.send('CONFIG /SHOW','B: HBIOS unit 3')
        t.send('CONFIG /SHOW','C: unbound');t.send('CONFIG /SHOW','D: HBIOS unit 5')
        checks.append('cold boot skips a saved alias while restoring independent bindings')
    finally:t.close()
    legacy=bytearray(512);legacy[:8]=b'BWCF'+bytes((2,2,3,0x95))
    struct.pack_into('<H',legacy,8,-sum(struct.unpack('<256H',legacy))&65535)
    old=bytearray((out/'system.img').read_bytes());old[2048:2560]=legacy
    oldpath=out/'legacy-config.img';oldpath.write_bytes(old)
    t=terminal('legacy-rejection',oldpath)
    try:
        t.expect(r'entry @ 0x1000\]\.\.\.!')
        if b'A0>' in t.data:raise AssertionError('legacy configuration was silently accepted')
        checks.append('checksummed version-2 configuration rejected before OS entry')
    finally:t.close()
    (out/'result.json').write_text(json.dumps({'status':'PASS','checks':checks,
        'system_sha256':hashlib.sha256((image/'system.img').read_bytes()).hexdigest()},indent=2)+'\n')
    print('PASS:',out/'result.json')


if __name__=='__main__':main()
