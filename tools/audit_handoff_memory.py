#!/usr/bin/env python3
"""Isolated handoff dispatch/removal footprint probes; not production implementation.
Run from the repository root after build_system.py and build_ccp.py.
"""
import sys, tempfile, subprocess
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
from build_ccp import assemble,relocation_offsets
from system_layout import expand_layout
s=Path('src/ccp/ccp.mac').read_text().replace('        CSEG\n        .PHASE  ','        ASEG\n        ORG     ').replace('        .DEPHASE\n','')
s=s.replace('CCP_DISPATCH:                           ; dispatch acquired or cold-start command','CCP_DISPATCH:                           ; audit prototype\n        XOR A\n        LD (LY_SYS+0B7H),A')
s=s.replace('        CALL    CPX_DISPATCH\n        JR      C,CCP_LOOP','        CALL    CPX_DISPATCH\n        JR NC,CCP_BAD\n        LD A,(LY_SYS+0B7H)\n        OR A\n        JR Z,CCP_LOOP')
p=Path('build/handoff-audit').resolve(); p.mkdir(parents=True, exist_ok=True); a=Path('/Users/nathanael/bin/z80asm')
base=assemble(a,s,p/'ccp.bin',p/'ccp.lst',0xbb00); alts=[]
for origin in [0xbc01,0xbd37]:
 t=s.replace('CCPBASE         EQU     0BB00H',f'CCPBASE         EQU     0{origin:04X}H')
 alts.append((assemble(a,t,p/f'ccp-{origin:x}.bin',p/f'ccp-{origin:x}.lst',origin),origin))
print('CCP request prototype',len(base),'allocation',(len(base)+255)&~255,'relocations',len(relocation_offsets(base,alts)))
s=Path('src/bios/config.mac').read_text().replace('        CSEG\n        .PHASE  ','        ASEG\n        ORG     ').replace('        .DEPHASE\n','')
s=s.replace('BCX_UNLOAD:                             ; unload selected CPX','BCX_UNLOAD:                             ; audit canonical RCP identity\n        PUSH HL\n        PUSH BC\n        PUSH IX\n        POP HL\n        LD DE,HA_NAME\n        LD B,8\nHA_COMPARE:\n        LD A,(DE)\n        CP (HL)\n        JR NZ,HA_KEEP\n        INC DE\n        INC HL\n        DJNZ HA_COMPARE\n        XOR A\n        LD (LY_SYS+0B6H),A\nHA_KEEP:\n        POP BC\n        POP HL')
s=s.replace('        JR      NC,BCX_OK', '        JP      NC,BCX_OK')
s=s.replace('        END',"HA_NAME: DB 'RCP     '\n        END")
with tempfile.TemporaryDirectory() as tmp:
 t=Path(tmp); (t/'config.mac').write_text(expand_layout(s))
 for name,source in [('disklinks.inc','build/system/disklink.inc'),('cpxlinks.inc','build/system/cpxlink.inc'),('bioslinks.inc','build/system/bioslink.inc'),('hardware.inc','src/platform/trs80m4/hardware.inc')]:
  (t/name).write_bytes(Path(source).read_bytes())
 subprocess.run([str(a),'-fb',f'-o{p}/config.bin',f'-l{p}/config.lst','config.mac'],cwd=t,check=True)
 d=(p/'config.bin').read_bytes(); print('control reset prototype',len(d)-0xf000 if d[:0xf000]==bytes(0xf000) else len(d))
