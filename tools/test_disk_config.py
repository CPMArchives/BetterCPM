#!/usr/bin/env python3
"""Exercise the runtime disk ABI on disposable trs80gp media."""
import subprocess
import sys
import tempfile
from pathlib import Path
from build_trs80_boot import ROOT, install
from run_trs80_command import DEFAULT_EMULATOR, key_args

ASM = Path.home() / 'bin/z80asm'
# MM CP/M 1.26/1.30 SS definition from DISK.FDF, including sector skew.
PROFILE = bytes([1,36,0,4,15,1,84,0,127,0,192,0,32,0,2,0,40,18,1,128,
                 1,5,9,13,17,3,7,11,15,2,6,10,14,18,4,8,12,16]).ljust(64,b'\0')

def db(data):
    return '\n'.join('        DB '+','.join(str(v) for v in data[i:i+16]) for i in range(0,len(data),16))

def main():
    code = ['        ASEG','        ORG 100H','        LD SP,7000H']
    number = 0
    def step(instructions):
        nonlocal number
        number += 1
        code.extend([f'        LD A,{number}', '        LD (STAGE),A', instructions])
    def api(op, pointer='REQ', status=0):
        step(f'        LD B,{op}\n        LD C,207\n        LD DE,{pointer}\n        CALL 5\n        LD A,L\n        CP {status}\n        JP NZ,FAIL')
    step('        LD B,0\n        LD C,207\n        CALL 5\n        LD A,(HL)\n        CP 66\n        JP NZ,FAIL')
    api(1, '0FFF0H',1)  # pointer wrap must never reach protected memory
    code += ['        LD A,1','        LD (REQ),A']
    api(1)
    step('        LD A,(REQ+1)\n        CP 5\n        JP NZ,FAIL')
    code += ['        LD HL,PROFILE','        LD DE,REQ+1','        LD BC,64','        LDIR']
    api(4)
    api(3,'OUTREQ')
    step('        LD HL,REQ+1\n        LD DE,OUTREQ+1\n        LD B,64\nCMPLOOP:\n        LD A,(DE)\n        CP (HL)\n        JP NZ,FAIL\n        INC HL\n        INC DE\n        DJNZ CMPLOOP')
    # Second logical drive, same physical drive, a distinct format (OFF=0).
    code += ['        LD A,2','        LD (REQ),A','        XOR A','        LD (REQ+15),A']
    api(4)
    # Invalid duplicate sector IDs must leave existing definition intact.
    code += ['        LD A,1','        LD (REQ+22),A']
    api(4,status=1)
    # Hardware capability reduction must not invalidate attached formats.
    api(2,'PHREQ',2)
    # Format last cylinder on disposable physical 1, then verify BIOS I/O.
    api(5,'FMTREQ')
    step('        LD C,1\n        CALL 0EF1BH\n        LD A,H\n        OR L\n        JP Z,FAIL\n        LD BC,39\n        CALL 0EF1EH\n        LD BC,0\n        CALL 0EF21H\n        LD BC,BUFFER\n        CALL 0EF24H\n        CALL 0EF27H\n        OR A\n        JP NZ,FAIL\n        LD HL,BUFFER\n        LD B,128\nERASED:\n        LD A,(HL)\n        CP 0E5H\n        JP NZ,FAIL\n        LD (HL),05AH\n        INC HL\n        DJNZ ERASED')
    step('        LD C,0\n        CALL 0EF2AH\n        OR A\n        JP NZ,FAIL\n        CALL 0EF27H\n        OR A\n        JP NZ,FAIL\n        LD HL,BUFFER\n        LD B,128\nWRITTEN:\n        LD A,(HL)\n        CP 05AH\n        JP NZ,FAIL\n        INC HL\n        DJNZ WRITTEN')
    step('        LD BC,1\n        CALL 0EF21H\n        CALL 0EF27H\n        OR A\n        JP NZ,FAIL\n        LD HL,BUFFER\n        LD B,128\nADJACENT:\n        LD A,(HL)\n        CP 0E5H\n        JP NZ,FAIL\n        INC HL\n        DJNZ ADJACENT')
    code += ['        LD DE,PASSMSG','        LD C,9','        CALL 5','        JP 0',
             'FAIL:   ADD A,65','        LD E,A','        LD C,2','        CALL 5','        LD A,(STAGE)','        ADD A,65','        LD E,A','        LD C,2','        CALL 5',
             '        LD DE,FAILMSG','        LD C,9','        CALL 5','        JP 0',
             "PASSMSG: DB 13,10,'DISK ABI PASS',13,10,'$'", "FAILMSG: DB ' DISK ABI FAIL',13,10,'$'",
             'STAGE: DB 0','REQ: DB 1','        DS 79','OUTREQ: DB 1','        DS 79',
             'PHREQ: DB 1,5,35,1,0,2,15','        DS 73','PROFILE:',db(PROFILE),
             'FMTREQ: DB 1,39,0','        DW STREAMEND-STREAM,STREAM','        DS 73',
             'BUFFER: DS 128','STREAM:']
    stream = bytearray([0x4e]*80+[0]*12+[0xf6]*3+[0xfc]+[0x4e]*50)
    for sector in range(1,19):
        stream.extend([0]*12+[0xf5]*3+[0xfe,39,0,sector,1,0xf7]+[0x4e]*22+
                      [0]*12+[0xf5]*3+[0xfb]+[0xe5]*256+[0xf7]+[0x4e]*16)
    stream.extend([0x4e]*1500)
    code += [db(stream),'STREAMEND:','        END']
    with tempfile.TemporaryDirectory(prefix='bettercpm-disk-abi-') as name:
        work=Path(name)
        (work/'probe.mac').write_text('\n'.join(code)+'\n')
        subprocess.run([str(ASM),'-fb','-oprobe.com','probe.mac'],cwd=work,check=True,stdout=subprocess.DEVNULL)
        b=ROOT/'build'
        files=[('PROBE.COM',(work/'probe.com').read_bytes()),('BASIC.CPX',(b/'cpx/BASIC.CPX').read_bytes())]
        disk=install((b/'trs80/boot.bin').read_bytes(),(b/'trs80/stage1.bin').read_bytes(),
                     (b/'system/resident.bin').read_bytes(),(b/'ccp/ccp.rlm').read_bytes(),files)
        (work/'a.dmk').write_bytes(disk)
        # Seed writable media; write-track replaces its final SS track.
        (work/'b.dmk').write_bytes(disk)
        args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(work/'a.dmk'),'-d1',str(work/'b.dmk'),'-id','3000']
        args+=key_args('PROBE\r')+['-id','4000','-it','-ix']
        subprocess.run(args,cwd=work,check=True,timeout=90)
        screen=(work/'trs80-text-0.bin').read_bytes()[:1920]
        visible='\n'.join(screen[i:i+80].decode('ascii',errors='replace').rstrip() for i in range(0,1920,80))
        assert 'DISK ABI PASS' in visible, visible
        assert 'A0>' in visible.split('DISK ABI PASS',1)[1], 'warm boot did not return to prompt\n'+visible
        print('PASS: query, pointer guard, FDF binding, readback, alias, rejection, format, read/write, adjacent record, warm boot')

if __name__=='__main__': main()
