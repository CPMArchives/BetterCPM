#!/usr/bin/env python3
"""Build a private same-extent random-I/O candidate; do not alter production.

The candidate's state addresses are pinned to the baseline for isolated image
comparisons. Full production integration/qualification is a separate step.
"""
import subprocess,tempfile,json,re,argparse,hashlib
from pathlib import Path
from system_layout import expand_layout,LAYOUT
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=root/'build/audit/random-same-extent');args=p.parse_args()
out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
s=(root/'src/bdos/unified.mac').read_text()
if 'RANDOM_SAME_EXTENT_V1' in s:
 raise SystemExit('Candidate already integrated. Use test_random_same_extent_candidate.py --production; reproduce the private audit from commit 0d8e2db.')
original=s
(out/'baseline.mac').write_text(s)
s=s.replace('        CALL    UB_RDECODE\n        XOR     A\n        CALL    UB_EXTENT','        CALL    UB_RDECODE\n        LD      A,0\n        CALL    C,UB_EXTENT')
s=s.replace('        CALL    UB_RDECODE\n        LD      A,1\n        CALL    UB_EXTENT','        CALL    UB_RDECODE\n        LD      A,1\n        CALL    C,UB_EXTENT')
start=s.index('UB_RVALID:');end=s.index('\n  ; Activate the requested extent',start)
s=s[:start]+'''UB_RVALID:
  ; Private candidate: R1:R0 >> 7 supplies logical EX/S2. RLA consumes
  ; R0 bit 7 carried by ADD; AND discards the unrelated high EX bits.
        LD      A,(IX+33)
        ADD     A,A
        LD      A,(IX+34)
        LD      H,A
  ; A zero-RC FCB may be a bare search FCB, not an activated empty file.
  ; Keep its normal lookup. Upper EX flags conservatively take that path too.
        RLA
        AND     01FH
        LD      L,A
        LD      A,H
        RRCA
        RRCA
        RRCA
        RRCA
        AND     0FH
        LD      H,A
        LD      A,(IX+15)
        OR      A
        JR      Z,UR_DECODE
        LD      A,(IX+14)
        AND     03FH
        CP      H
        JR      NZ,UR_SWITCH
        LD      A,(IX+12)
        CP      L
        JR      Z,UR_POSITION
UR_SWITCH:
  ; RC is nonzero on both incoming branches; preserve the decoded target
  ; across Close. A genuine extent change must still commit dirty state.
        PUSH    HL
        CALL    UB_CCORE
        POP     HL
UR_DECODE:
        LD      (IX+14),H
        LD      (IX+12),L
        SCF
UR_POSITION:
  ; RES changes the position without changing the carry result: NC keeps
  ; the live FCB, C asks the random caller to activate the decoded extent.
        LD      A,(IX+33)
        RES     7,A
        LD      (IX+32),A
        RET
''' + s[end:]
# Fall through to the immediately following helper, retaining both labels.
for helper in ('UB_CCORE','UB_MAKECORE','UB_READCORE','UB_WCORE'):
 needle='        CALL    '+helper+'\n        RET\n'
 assert s.count(needle)==1,(helper,s.count(needle))
 s=s.replace(needle,'',1)
# Ordinary tail calls; no inline return-address data in these services.
for helper in ('BIO_RDRIN','BIO_CONST','UB_GETIN','UB_ECHO'):
 needle='        CALL    '+helper+'\n        RET\n'
 assert s.count(needle)==1,(helper,s.count(needle))
 s=s.replace(needle,'        JP      '+helper+'\n',1)
s=s.replace('        JP      UB_ATDONE','        JR      UB_ATDONE')
# Preserve the frozen core-state addresses used by other resident components.
# This candidate saves two code bytes; pad them before mutable state, not by
# moving the BIOS/BDOS boundaries or shrinking the private stack.
s=s.replace('UB_OLDSP:','        DB 0,0 ; private candidate ABI padding\nUB_OLDSP:',1)
(out/'candidate.mac').write_text(s)
for name in ('baseline','candidate'):
 text=expand_layout((out/(name+'.mac')).read_text()).replace('        CSEG\n        .PHASE  ','        ASEG\n        ORG     ').replace('        .DEPHASE\n','')
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp)/'bdos.mac';p.write_text(text)
  (p.parent/'versions.inc').write_bytes((root/'src/bdos/versions.inc').read_bytes())
  subprocess.run([str(Path.home()/'bin/z80asm'),'-fb','-o'+str(out/(name+'.bin')),'-l'+str(out/(name+'.lst')),str(p)],check=True)
 print(name,(out/(name+'.bin')).stat().st_size,'limit',LAYOUT['EXTENSIONS']-LAYOUT['BDOS'])

labels={}
for name in ('baseline','candidate'):
    labels[name]={}
    for line in (out/(name+'.lst')).read_text().splitlines():
        m=re.match(r'^([0-9a-f]{4})\s+.*\b(UB_OLDSP|UB_DMA|UB_DRIVE|UB_USERNO|UB_COLUMN|UB_LISTE|UB_STACK|UB_STKTOP):',line,re.I)
        if m:labels[name][m[2]]=int(m[1],16)
assert labels['baseline']==labels['candidate'], 'private candidate moved a frozen state/stack address'
assert (out/'candidate.bin').stat().st_size<=LAYOUT['EXTENSIONS']-LAYOUT['BDOS']
assert (root/'src/bdos/unified.mac').read_text()==original
(out/'audit.json').write_text(json.dumps({'status':'PRIVATE_CANDIDATE','baseline_bytes':(out/'baseline.bin').stat().st_size,'candidate_bytes':(out/'candidate.bin').stat().st_size,'state_addresses':labels['candidate'],'abi_padding_bytes':2,'production_source_changed':False,'baseline_sha256':hashlib.sha256((out/'baseline.bin').read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256((out/'candidate.bin').read_bytes()).hexdigest(),'scope':'Memory audit only; production integration and complete qualification pending.'},indent=2)+'\n')
