#!/usr/bin/env python3
"""Retain explicit observations for remaining recovery/dispatch requirements.

Uses disposable emulator media and a declared seek-result provider; no claim
that the provider qualifies real controller timing or attached peripherals.
"""
import json,re,subprocess,time,sys
from pathlib import Path
from build_ccp import assemble
from test_bios import Z80
from system_layout import LAYOUT
from add_cpm_file_to_dmk import extract_raw,add_file
from build_montezuma_extended_790k import build,RAW_SIZE
import build_trs80_boot as boot
from run_trs80_command import DEFAULT_EMULATOR,key_args
R=Path(__file__).resolve().parents[1];W=R/'build/compatibility'/time.strftime('gaps-%Y%m%d-%H%M%S');W.mkdir()
asm=Path('/Users/nathanael/bin/z80asm')
listing=(R/'build/system/disk.lst').read_text()
def sym(n):
 return int(re.findall(r'^([0-9a-f]{4})\s+.*\b'+n+r':?\s*$',listing,re.M|re.I)[-1],16)
retry=[]
for name in ('DC_READ','DC_WRITE'):
 m=Z80(b'');binary=(R/'build/system/disk.bin').read_bytes();base=LAYOUT['DISK'];m.mem[base:base+len(binary)]=binary
 # The first seek fails; a second attempt would succeed. Count invocations.
 p=sym('DC_SEEK')
 # CP 1 leaves Z set, so explicitly return NZ on the first failure.
 m.mem[p:p+14]=bytes([0x21,0,0x70,0x34,0x7e,0xfe,1,0x20,4,0x3e,1,0xb7,0xc9,0xaf])
 m.mem[p+14]=0xc9
 m.hl=0x6000;m.run(sym(name),limit=1000)
 retry.append({'entry':name,'attempts':m.mem[0x7000],'status':m.a,'result':'F' if m.mem[0x7000]==1 and m.a else 'REVIEW'})
(W/'retry.json').write_text(json.dumps(retry,indent=2))
if '--retry-only' in sys.argv:
 print(W);print(retry);sys.exit(0)
source='''        ORG 100H
        LD HL,(1)
        LD DE,HOOK
        LD (1),DE
        RET
HOOK:   LD (OLD+1),HL
        LD DE,MSG
        LD C,9
        CALL 5
OLD:    JP 0
MSG:    DB 13,10,'RET INVOKED WBOOT',13,10,'$'
        END
'''
# Store the original target before returning; HL is not a preserved entry API.
source=source.replace('        LD DE,HOOK','        LD (OLD+1),HL\n        LD DE,HOOK').replace('HOOK:   LD (OLD+1),HL','HOOK:')
ret=assemble(asm,source,W/'RETPATH.COM',W/'retpath.lst',0x100)
raw=extract_raw((R/'build/compatibility/BetterCPM-Compatibility-Qualification.dmk').read_bytes());add_file(raw,'RETPATH.COM',ret);(W/'a.dmk').write_bytes(build(raw))
boot.FILESYSTEM_FIRST_SECTOR=0;boot.BLOCK_COUNT=RAW_SIZE//2048
full=bytearray(b'\xe5'*RAW_SIZE);boot.install_files(full,[('FULL.DAT',bytes((boot.BLOCK_COUNT-2)*2048))]);(W/'b.dmk').write_bytes(build(full))
a=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(W/'a.dmk'),'-d1',str(W/'b.dmk'),'-id','3500']
for c in ['RETPATH','VER','SAVE 1 B:NOSPACE.BIN','VER']:
 a+=key_args(c+'\r')+['-id','6000','-it']
a+=['-ix'];subprocess.run(a,cwd=W,timeout=180,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
s=[]
for p in sorted(W.glob('trs80-text-*.bin')):
 d=p.read_bytes()[:1920];s.append('\n'.join(bytes(x&127 for x in d[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80)))
(W/'screens.txt').write_text('\n\n--- SCREEN ---\n\n'.join(s));print(W);print(retry);print(s[-1])
