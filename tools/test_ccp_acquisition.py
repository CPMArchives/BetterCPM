#!/usr/bin/env python3
"""Feed exact raw console bytes, observe the real CCP before/after host CR."""
import json,subprocess,shutil,time,sys
from pathlib import Path
from build_ccp import assemble
from add_cpm_file_to_dmk import extract_raw,add_file
from build_montezuma_extended_790k import build
from run_trs80_command import key_args,DEFAULT_EMULATOR
R=Path(__file__).resolve().parents[1]
W=R/'build/compatibility'/time.strftime('acquisition-%Y%m%d-%H%M%S');W.mkdir()
marker=(R/'tests/fixtures/conformance/ccpmark.mac').read_text().replace('@ID@','ACQUIRE')
m=assemble(Path('/Users/nathanael/bin/z80asm'),marker,W/'NAME.COM',W/'marker.lst',0x100)
for name,keys in [('mixed',b'nAmX\x08E mIxEd'),('tab',b'NAME\tMIXED'),('prime',b'SAVE 2 B:MEM.BIN')]:
 if sys.argv[1:] and name not in sys.argv[1:]:continue
 w=W/name;w.mkdir()
 source=(R/'tests/fixtures/conformance/keyfeed.mac').read_text().replace('@KEYS@',','.join(str(x) for x in keys)).replace('@PRIME@', '''        PUSH BC
        LD HL,0100H
        LD DE,0101H
        LD BC,511
        LD (HL),0A5H
        LDIR
        POP BC''' if name=='prime' else '')
 provider=assemble(Path('/Users/nathanael/bin/z80asm'),source,w/'provider.bin',w/'provider.lst',0x9000)
 install='''        ORG 0100H
        LD HL,DATA
        LD DE,9000H
        LD BC,%d
        LDIR
        CALL 9000H
        JP 0
DATA:
%s
        END
'''%(len(provider),'\n'.join('        DB '+','.join(str(x) for x in provider[i:i+16]) for i in range(0,len(provider),16)))
 loader=assemble(Path('/Users/nathanael/bin/z80asm'),install,w/'FEED.COM',w/'feed.lst',0x100)
 raw=extract_raw((R/'build/compatibility/BetterCPM-Compatibility-RO.dmk').read_bytes())
 add_file(raw,'FEED.COM',loader);add_file(raw,'NAME.COM',m);(w/'a.dmk').write_bytes(build(raw))
 shutil.copy2(R/'build/compatibility/ccp-20260907-235509/b.dmk',w/'b.dmk')
 args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(w/'a.dmk'),'-d1',str(w/'b.dmk'),'-id','3500']+key_args('FEED\r')+['-id','6000','-it']+key_args('\r')+['-id','6000','-it','-ix']
 subprocess.run(args,cwd=w,check=True,timeout=180,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 screens=[]
 for p in sorted(w.glob('trs80-text-*.bin')):
  raw=p.read_bytes()[:1920];screens.append('\n'.join(bytes(x&127 for x in raw[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80)))
 (w/'screens.txt').write_text('\n\n--- SCREEN ---\n\n'.join(screens))
 good=len(screens)==2 and 'MARK ACQUIRE' not in screens[0]
 if name=='mixed':good=good and 'MARK ACQUIRE DU A/00 TAIL[ MIXED]' in screens[1]
 elif name=='tab':good=good and 'MARK ACQUIRE' not in screens[1] and '?' in screens[1]
 else:good=good and 'SAVE 2 B:MEM.BIN' in screens[0] and '?' not in screens[1]
 (w/'result.json').write_text(json.dumps({'passed':good,'keys_hex':keys.hex(),'provider':'temporary public CONST/CONIN endpoints; restored before host CR'},indent=2))
 print(name,good,flush=True)
print(W)
