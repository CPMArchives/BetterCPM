#!/usr/bin/env python3
"""Format/read/write disposable Archives and mixed-size SUPER tracks in trs80gp."""
from pathlib import Path
import tempfile,struct,json
from build_ccp import assemble
from build_disk_utilities import builtin_source
from test_disk_utilities import records,db,run
from system_layout import LAYOUT as L
ROOT=Path(__file__).resolve().parents[1]

def main():
 archive=next(b for n,b in records() if n.startswith('Archives Model III'))
 f=json.loads((ROOT/'metadata/mm-builtin-formats.json').read_text())['formats'][12];p=f['parameters']
 superdisk=bytes([1])+struct.pack('<HBBBHHBBHH',*p[:10])+bytes((p[12],p[10],p[11],p[13]))+bytes(f['sector_ids']).ljust(32,b'\0')+bytes(12)
 tail=(ROOT/'src/utilities/dup.mac').read_text().split('STREAM:',1)[1]
 tail='STREAM:'+tail.replace('        INCLUDE disk/common.inc',(ROOT/'src/utilities/disk/common.inc').read_text().replace('        INCLUDE disk/builtins.inc',builtin_source()))
 for name,binding,side,logical,last,sizes in [('archives',archive,1,3,39,[3]*5),('super',superdisk,0,1,43,[3]*5+[2])]:
  with tempfile.TemporaryDirectory(prefix='bettercpm-fdf-live-') as tmp:
   work=Path(tmp)
   text=f'''        ASEG
        ORG 100H
        LD SP,4000H
        CALL INIT
        LD HL,NEWB
        LD DE,REQ
        LD BC,80
        LDIR
        LD DE,REQ
        LD B,4
        CALL API
        JP NZ,FAIL
        LD DE,REQ
        LD B,3
        CALL API
        JP NZ,FAIL
        LD HL,REQ+1
        LD DE,CURB
        LD BC,64
        LDIR
        LD A,1
        LD (DCYL),A
        LD A,{side}
        LD (DSIDE),A
        CALL STREAM
        JP C,FAIL
        LD A,1
        LD (REQ),A
        LD (REQ+1),A
        LD A,{side}
        LD (REQ+2),A
        LD HL,(STRPTR)
        LD DE,TRACKBF
        OR A
        SBC HL,DE
        LD (REQ+3),HL
        LD HL,TRACKBF
        LD (REQ+5),HL
        LD DE,REQ
        LD B,5
        CALL API
        JP NZ,FAIL
        LD C,1
        CALL {L['BIOS']+27}
        LD BC,{logical}
        CALL {L['BIOS']+30}
        LD BC,{last}
        CALL {L['BIOS']+33}
        LD BC,3000H
        CALL {L['BIOS']+36}
        CALL {L['BIOS']+39}
        OR A
        JP NZ,FAIL
        LD HL,3000H
        LD B,128
ERASED: LD A,(HL)
        CP 0E5H
        JP NZ,FAIL
        LD (HL),05AH
        INC HL
        DJNZ ERASED
        LD C,0
        CALL {L['BIOS']+42}
        OR A
        JP NZ,FAIL
        CALL {L['BIOS']+39}
        OR A
        JP NZ,FAIL
        LD HL,3000H
        LD B,128
CHECK:  LD A,(HL)
        CP 05AH
        JP NZ,FAIL
        INC HL
        DJNZ CHECK
        LD BC,{last-1}
        CALL {L['BIOS']+33}
        CALL {L['BIOS']+39}
        OR A
        JP NZ,FAIL
        LD HL,3000H
        LD B,128
NEIGHBOR:LD A,(HL)
        CP 0E5H
        JP NZ,FAIL
        INC HL
        DJNZ NEIGHBOR
        LD DE,PASSMSG
        JR REPORT
DUNSUP:
FAIL:   LD DE,FAILMSG
REPORT: LD C,9
        CALL 5
        JP 0
PASSMSG:DB 'FDF TRACK READ WRITE PASS',13,10,'$'
FAILMSG:DB 'FDF TRACK FAIL',13,10,'$'
NEWB:
'''+db(bytes([1,1])+binding[1:]+bytes(15))+'\n'+tail
   probe=assemble(Path.home()/'bin/z80asm',text,work/'FDFTRACK.COM',work/'probe.lst',0x100)
   extras=[('FDFTRACK.COM',probe)]
   for file in ('utilities/RSX.COM','rsx/FDF.RSX'):
    p=ROOT/'build'/file;extras.append((p.name,p.read_bytes()))
   steps=[('RSX LOAD FDF\r',4000),('FDFTRACK\r',10000),('RSX UNLOAD FDF\r',4000),('RSX LIST\r',4000)]
   screens,w,original=run(work,'fdf-'+name,steps,extras)
   assert 'FDF TRACK READ WRITE PASS' in screens[1][0],screens[1][0]
   assert 'No RSXs loaded' in screens[-1][0] and 'TPA available: 53K' in screens[-1][0],screens[-1][0]
   data=(w/'b.dmk').read_bytes();length=int.from_bytes(data[2:4],'little')
   tr=data[16+(2+side)*length:16+(3+side)*length];found={}
   for i in range(0,128,2):
    ptr=int.from_bytes(tr[i:i+2],'little')&0x3fff
    if not ptr:break
    assert tr[ptr:ptr+3]==bytes([254,3 if side else 1,side])
    found[tr[ptr+3]]=tr[ptr+4]
   assert found==dict(enumerate(sizes,1)),found
   print(f'PASS: {name} track IDs and sizes, read/write, adjacent record, unload, 53K restoration',flush=True)
if __name__=='__main__':main()
