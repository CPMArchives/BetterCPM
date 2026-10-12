#!/usr/bin/env python3
"""Cost fixed BIOS trampolines with mutable targets and cold-boot fallback setup.

Dispatch/size experiment: no production RSX lifecycle integration. Callback pointers are
unsafe during provider movement unless a separate publication/rebind contract
is implemented. Production BIOS and layout are never replaced.
"""
from pathlib import Path
import json
import argparse
root=Path(__file__).resolve().parents[1]
from audit_monitor_memory import assemble
from system_layout import LAYOUT,expand_layout
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--assembler',type=Path,default=Path('/Users/nathanael/bin/z80asm'))
args=parser.parse_args()
source=(root/'src/bios/bios.mac').read_text()
rows=[]
for name,ops in [('output',( ('OUT','PL_CONOT','JP      PL_CONOT'),)), ('console',(('OUT','PL_CONOT','JP      PL_CONOT'),('STATUS','PL_CONST','CALL    PL_CONST'),('INPUT','PL_CONIN','CALL    PL_CONIN'))), ('console-cursor',(('OUT','PL_CONOT','JP      PL_CONOT'),('STATUS','PL_CONST','CALL    PL_CONST'),('INPUT','PL_CONIN','CALL    PL_CONIN'),('CURSOR','PL_CURSOR','JP      PL_CURSOR')))]:
 s=source;init='';tail=''
 for op,target,old in ops:
  assert s.count(old)==1,old
  s=s.replace(old,old.split()[0]+'      MH_'+op)
  init+=f'        LD HL,{target}\n        LD (MP_{op}),HL\n'
  tail+=f'MH_{op}:\n        LD HL,(MP_{op})\n        JP (HL)\nMP_{op}: DW 0\n'
 s=s.replace('        CALL    PL_INIT',init+'        CALL    PL_INIT')
 s=s.replace('        .DEPHASE',tail+'\n        .DEPHASE')
 out=root/'build/audit/monitor-efficiency'/('hooks-'+name);out.mkdir(exist_ok=True)
 for filename,p in [('biosplat.inc',root/'src/bios/biosplat.inc'),('m4cons.inc',root/'src/platform/trs80m4/m4cons.inc'),('m4scroll.inc',root/'src/platform/trs80m4/m4scroll.inc'),('reload.inc',root/'src/platform/trs80m4/reload.inc')]:
  (out/filename).write_text(expand_layout(p.read_text()))
 data=assemble(s,'bios',LAYOUT['BIOS'],out,args.assembler)
 rows.append(dict(profile=name,bytes=len(data),growth=len(data)-636,directory=str(out)))
# One shared multiplexed target plus explicit internal/raw BIOS vectors.
# This prototype measures dispatch only; transaction binding remains absent.
s=source
for old,new in [('JP      PL_CONOT','JP      MH_OUT'),
                ('CALL    PL_CONST','LD A,1\n        CALL    MC_CALL'),
                ('CALL    PL_CONIN','LD A,2\n        CALL    MC_CALL'),
                ('JP      PL_CURSOR','JP      MH_CUR')]:
 assert s.count(old)==1,old
 s=s.replace(old,new)
s=s.replace('BIOBOOT:','MONCALL: JP MC_CALL\nMONRAW:  JP MC_RAW\nMONBASE: JP MC_BASE\n\nBIOBOOT:',1)
s=s.replace('        CALL    PL_INIT','        CALL MC_BASE\n        CALL    PL_INIT',1)
s=s.replace('        .DEPHASE',"""
MH_OUT:
        XOR A
        JP MC_CALL
MH_CUR:
        LD A,3
MC_CALL:
        LD HL,(MP_MON)
        JP (HL)
MC_RAW:
        OR A
        JP Z,PL_CONOT
        DEC A
        JP Z,PL_CONST
        DEC A
        JP Z,PL_CONIN
        DEC A
        JP Z,PL_CURSOR
        DEC A
        JR Z,MC_CLEAR
        DEC A
        RET Z
        LD A,0FFH
        RET
MC_CLEAR:
        LD C,01CH
        JP PL_CONOT
MC_BASE:
        LD HL,MC_RAW
        LD (MP_MON),HL
        RET
MP_MON: DW 0
        .DEPHASE""",1)
out=root/'build/audit/monitor-efficiency/hooks-multiplex';out.mkdir(parents=True,exist_ok=True)
for filename,p in [('biosplat.inc',root/'src/bios/biosplat.inc'),('m4cons.inc',root/'src/platform/trs80m4/m4cons.inc'),('m4scroll.inc',root/'src/platform/trs80m4/m4scroll.inc'),('reload.inc',root/'src/platform/trs80m4/reload.inc')]:
 (out/filename).write_text(expand_layout(p.read_text()))
data=assemble(s,'bios',LAYOUT['BIOS'],out,args.assembler)
rows.append(dict(profile='multiplex',bytes=len(data),growth=len(data)-636,directory=str(out)))
print(json.dumps(rows,indent=2))
(root/'build/audit/monitor-efficiency/hooks.json').write_text(json.dumps(rows,indent=2)+'\n')
