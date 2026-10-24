#!/usr/bin/env python3
"""Exercise physical CLI changes against actual cpmsim API state on private disks."""
import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from build_ccp import assemble
from startup_record import build as startup
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
from system_layout import LAYOUT
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def state_probe(work):
    return assemble(Path.home()/'bin/z80asm','''        ASEG
        ORG 100H
        LD SP,4000H
        LD DE,TITLE
        LD C,9
        CALL 5
        LD A,1
        LD (OP),A
AGAIN: XOR A
        LD (INDEX),A
NEXT:  LD A,(INDEX)
        LD (REQ),A
        LD A,(OP)
        LD B,A
        LD DE,REQ
        LD C,181
        CALL 5
        LD A,L
        OR A
        JP NZ,FAIL
        LD HL,REQ+1
        LD B,6
        LD A,(OP)
        CP 1
        JR Z,DUMP
        LD B,64
DUMP:  LD A,(HL)
        CALL HEX
        INC HL
        DJNZ DUMP
        LD A,(INDEX)
        INC A
        LD (INDEX),A
        CP 4
        JR C,NEXT
        LD A,(OP)
        CP 3
        JR Z,DONE
        LD A,3
        LD (OP),A
        JR AGAIN
DONE:  LD DE,ENDMSG
        LD C,9
        CALL 5
        JP 0
FAIL:  LD DE,BAD
        LD C,9
        CALL 5
        JP 0
HEX:   PUSH AF
        RRCA
        RRCA
        RRCA
        RRCA
        CALL NIBBLE
        POP AF
NIBBLE:AND 15
        ADD A,'0'
        CP ':'
        JR C,PUT
        ADD A,7
PUT:   PUSH BC
        PUSH DE
        PUSH HL
        LD E,A
        LD C,2
        CALL 5
        POP HL
        POP DE
        POP BC
        RET
TITLE: DB 'STATE ', '$'
ENDMSG:DB 13,10,'$'
BAD:   DB 'STATE FAILED',13,10,'$'
OP:    DB 0
INDEX: DB 0
REQ:   DS 80
        END
''',work/'STATE.COM',work/'state.lst',0x100)


def main():
    p=argparse.ArgumentParser();p.add_argument('--diskdefs',type=Path,required=True);a=p.parse_args()
    parent=ROOT/'build/config-physical-cli';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));probe=state_probe(work)
    fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
    def offset(record):
        track,n=divmod(record,fmt.spt)
        return track*fmt.raw_track_bytes+fmt.raw_record_map()[n]*128
    cases=[('compound',b'CONFIG /PHYSICAL=1 /TYPE=5 /TRACKS=35 /SIDES=1 /STEP=12 /SPINUP=3 /SETTLE=20\r'),
           ('boot-guard',b'CONFIG /PHYSICAL=0 /TRACKS=35\r'),
           ('invalid',b'CONFIG /PHYSICAL=1 /SETTLE=20 /SIDES=3\r'),
           ('boot-timing',b'CONFIG /PHYSICAL=0 /SETTLE=20\r')]
    results=[]
    for name,command in cases:
        here=work/name;here.mkdir();disks=here/'disks';disks.mkdir()
        shutil.copy2(a.diskdefs,here/'diskdefs');image=disks/'drivea.dsk'
        shutil.copy2(ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk',image)
        for label in ('CONFIG.COM','DISK.FDB'):
            subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:'+label],cwd=here,check=True)
        for label,data in [('CONFIG.COM',(ROOT/'build/utilities/CONFIG.COM').read_bytes()),('STATE.COM',probe)]:
            path=here/label;path.write_bytes(data)
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(path),'0:'+label],cwd=here,check=True)
        data=bytearray(image.read_bytes());bcst=startup('',system_base=LAYOUT['SYSTEM'])
        for i,n in enumerate((1,2)):data[offset(n):offset(n)+128]=bcst[i*128:(i+1)*128]
        image.write_bytes(data);before=bytes(data)
        trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,
                      [(b'STATE\r',b'A0>_ ',20),(command,b'A0>_ ',20),
                       (b'STATE\r',b'A0>_ ',20),(b'BYE /Y\r',b'System halted',10)],here/'transcript.bin')
        states=[bytes.fromhex(s.decode()) for s in re.findall(rb'STATE ([0-9A-F]{560})',trace)]
        assert len(states)==2,trace
        old,new=states;expected=bytearray(old)
        if name=='compound':
            expected[6:12]=bytes([5,35,1,1,3,20])
            for i in range(1,4):
                at=24+i*64
                if old[at]==1 and (old[at+16]>35 or old[at+19]&0x60):expected[at]=255
            assert b'until cold boot' in trace and b'unconfigured' in trace,trace
        elif name=='boot-timing':
            expected[5]=20
            assert b'until cold boot' in trace,trace
        elif name=='invalid':assert b'Invalid CONFIG usage.' in trace,trace
        else:assert b'Nothing changed.' in trace,trace
        assert new==bytes(expected),(name,old.hex(),new.hex(),bytes(expected).hex())
        assert image.read_bytes()==before,(name,'CLI saved disk bytes')
        assert b'Push ENTER' not in trace and b'(Y/N)?' not in trace,trace
        if name=='compound':
            cold=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,
                         [(b'STATE\r',b'A0>_ ',20),(b'BYE /Y\r',b'System halted',10)],here/'cold.bin')
            assert bytes.fromhex(re.findall(rb'STATE ([0-9A-F]{560})',cold)[0].decode())==old,cold
        results.append({'case':name,'result':'PASS'})
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print('PASS: compound live profile, boot guard, late-invalid tail, safe boot timing, no catalogue dependency, no disk writes and cold reset;',work)


if __name__=='__main__':main()
