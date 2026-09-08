#!/usr/bin/env python3
"""Execute the assembled CCP with declared BDOS EOF/error result providers."""
from pathlib import Path
from build_ccp import assemble
from test_ccp import cpu,symbol,BASE
from system_layout import LAYOUT
R=Path(__file__).resolve().parents[1];W=R/'build/compatibility/loader-results';W.mkdir(exist_ok=True)
source='''        ORG %d
        LD A,C
        CP 32
        JR Z,USER
        CP 26
        JR Z,DMA
        CP 20
        JR Z,READ
        XOR A
        RET
USER:   LD A,E
        CP 0FFH
        LD A,7
        RET Z
        LD A,E
        LD (0F106H),A
        RET
DMA:    LD (0F100H),DE
        XOR A
        RET
READ:   LD HL,0F102H
        INC (HL)
        LD A,(HL)
        CP 1
        JR NZ,FINAL
        LD HL,PROGRAM
        LD DE,(0F100H)
        LD BC,128
        LDIR
        XOR A
        RET
FINAL:  LD A,(0F103H)
        RET
PROGRAM: DB 03EH,1,032H,4,0F1H,0C3H,0FFH,0FFH
        DS 120
        END
'''%LAYOUT['BDOS']
stub=assemble(Path('/Users/nathanael/bin/z80asm'),source,W/'provider.bin',W/'provider.lst',LAYOUT['BDOS'])
for result in (1,2,0xFF,0):
 m=cpu();m.sp=0xF300
 for key,name in [('SYSTEM','gateway'),('EXTENSIONS','extensions')]:
  data=(R/f'build/system/{name}.bin').read_bytes();base=LAYOUT[key];m.mem[base:base+len(data)]=data
 m.mem[0:3]=bytes([0xc3,0xff,0xff])  # record warm-boot handoff without rebuilding
 m.setword(LAYOUT['SYSTEM']+0x90,0x9000)
 m.mem[LAYOUT['BDOS']:LAYOUT['BDOS']+len(stub)]=stub
 m.setword(LAYOUT['SYSTEM']+0x8c,BASE)
 command=b'PROBE ONE.TXT TWO.DAT';m.mem[symbol('CCP_COUNT')]=len(command);start=symbol('CCP_DATA');m.mem[start:start+len(command)]=command
 m.mem[0x5c:0x80]=bytes([0xa5])*36;m.mem[0xF103]=result
 address=symbol('CCP_LOAD');m.mem[0xF200:0xF204]=bytes([0xCD,address&255,address>>8,0xC9])
 m.run(0xF200,limit=1000000)
 assert m.mem[0xF106]==7,'caller user was not restored'
 if result==1:
  assert m.mem[0xF104]==1,'EOF did not execute the complete image'
  assert m.mem[0x5d:0x65]==b'ONE     ' and m.mem[0x6d:0x75]==b'TWO     '
  assert m.mem[0x81:0x91]==b' ONE.TXT TWO.DAT'
 else:
  assert m.mem[0xF104]==0,f'failed load executed at status {result:02X}'
  assert m.pc==0xffff,'failed load did not enter warm boot'
 print(f'EOF/error provider {result:02X}: execution and preparation boundary passed')
print('Successful EOF, logical read failure, final BIOS-error return, and oversize rejection passed')
# The surviving resident USER branch reparses its decimal operand without
# preparing transient FCBs/tail. Stop at its normal next-prompt destination.
m=cpu();m.mem[symbol('CCP_LOOP')]=0xc9
m.mem[LAYOUT['BDOS']:LAYOUT['BDOS']+5]=bytes([0x7b,0x32,5,0xf1,0xc9])
command=b'USER 7';m.mem[symbol('CCP_COUNT')]=len(command);start=symbol('CCP_DATA');m.mem[start:start+len(command)]=command
m.mem[0x5c:0x100]=bytes([0xa5])*164
address=symbol('CCP_TRYUSER');m.mem[0xF200:0xF204]=bytes([0xcd,address&255,address>>8,0xc9]);m.run(0xF200,limit=1000)
assert m.mem[0xF105]==7 and m.mem[0x5c:0x100]==bytes([0xa5])*164
print('Resident USER reparsed operand without preparing transient FCBs/tail')
