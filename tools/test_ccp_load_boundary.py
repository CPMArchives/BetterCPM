#!/usr/bin/env python3
"""Patterned COM loads immediately below/above the configured CCP boundary."""
import json,struct,subprocess,shutil,time,os
from pathlib import Path
from build_ccp import assemble
from add_cpm_file_to_dmk import extract_raw,add_file
from build_montezuma_extended_790k import build
from run_trs80_command import key_args,DEFAULT_EMULATOR
from system_layout import LAYOUT
R=Path(__file__).resolve().parents[1];W=R/'build/compatibility'/time.strftime('load-boundary-%Y%m%d-%H%M%S');W.mkdir()
ccp=struct.unpack_from('<H',(R/'build/ccp/ccp.rlm').read_bytes(),10)[0]
cpx=struct.unpack_from('<H',(R/'build/cpx/BASIC.CPX').read_bytes(),14)[0]
ceiling=LAYOUT['TPA'];maximum=(ceiling-0x100)//128
for name,records in [('FIT',maximum),('OVER',maximum+1)]:
 w=W/name;w.mkdir()
 source='''        ORG 0100H
        LD HL,(%d)
        LD DE,%d
        OR A
        SBC HL,DE
        JR NZ,BAD
        LD HL,0180H
        LD DE,%d
LOOP:   LD A,H
        DEC A
        ADD A,A
        LD B,A
        LD A,L
        RLCA
        AND 1
        OR B
        CP (HL)
        JR NZ,BAD
        INC HL
        DEC DE
        LD A,D
        OR E
        JR NZ,LOOP
        LD DE,GOODMSG
        JR SHOW
BAD:    LD DE,BADMSG
SHOW:   LD C,9
        CALL 5
        RET
GOODMSG: DB 'LOADOK %s',13,10,'$'
BADMSG: DB 'LOAD PATTERN OR PROFILE FAILED',13,10,'$'
        END
'''%(LAYOUT['SYSTEM']+0x90,ceiling,(records-1)*128,name)
 data=assemble(Path('/Users/nathanael/bin/z80asm'),source,w/(name+'.COM'),w/'probe.lst',0x100)
 assert len(data)<=128
 data=data.ljust(128,b'\0')+b''.join(bytes([i&255])*128 for i in range(1,records))
 (w/(name+'.COM')).write_bytes(data)
 raw=extract_raw(Path(os.environ.get('BETTERCPM_TEST_IMAGE',str(R/'build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk'))).read_bytes());add_file(raw,name+'.COM',data);(w/'a.dmk').write_bytes(build(raw))
 args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(w/'a.dmk'),'-id','3500']+key_args(name+'\r')+['-id','12000','-it']+key_args('VER\r')+['-id','6000','-it','-ix']
 subprocess.run(args,cwd=w,timeout=180,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 screens=[]
 for p in sorted(w.glob('trs80-text-*.bin')):
  d=p.read_bytes()[:1920];screens.append('\n'.join(bytes(x&127 for x in d[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80)))
 (w/'screens.txt').write_text('\n\n--- SCREEN ---\n\n'.join(screens))
 (w/'fixture.json').write_text(json.dumps({'records':records,'bytes':len(data),'ccp_base':ceiling,'last_destination':0x100+len(data)-1,'expected_execution':name=='FIT'},indent=2))
 assert ('LOADOK '+name in '\n'.join(screens)) == (name=='FIT'), screens
 assert 'LOAD PATTERN OR PROFILE FAILED' not in '\n'.join(screens), screens
 assert 'A0>' in screens[-1], screens
 print(name,records,repr(screens[-1][:300]),flush=True)
print(W)
