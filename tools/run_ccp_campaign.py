#!/usr/bin/env python3
"""Run command-level fixtures against the real CCP on private emulator disks.

Captures are observations; review full predicates before assigning ledger verdicts.
"""
import concurrent.futures,json,shutil,subprocess,time,os,sys
from pathlib import Path
from build_ccp import assemble
from run_trs80_command import key_args,DEFAULT_EMULATOR
import build_trs80_boot as boot
from add_cpm_file_to_dmk import extract_raw,add_file
from build_montezuma_extended_790k import build,RAW_SIZE
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/compatibility'/time.strftime('ccp-%Y%m%d-%H%M%S')
OUT.mkdir(parents=True)
text=(ROOT/'tests/fixtures/conformance/ccpmark.mac').read_text()
def marker(identity):
 return assemble(Path('/Users/nathanael/bin/z80asm'),text.replace('@ID@',identity),OUT/(identity+'.com'),OUT/(identity+'.lst'),0x100).ljust(512,b'\0')
a=extract_raw(Path(os.environ.get('BETTERCPM_TEST_IMAGE',str(ROOT/'build/compatibility/BetterCPM-Compatibility-Campaign.dmk'))).read_bytes())
add_file(a,'NAME.COM',marker('A0'))
add_file(a,'ONLYA.COM',marker('ONLYA'))
(OUT/'a.dmk').write_bytes(build(a))
boot.FILESYSTEM_FIRST_SECTOR=0;boot.BLOCK_COUNT=RAW_SIZE//2048
b=bytearray(b'\xe5'*RAW_SIZE)
files=[('NAME.COM',marker('B0')),('NAME.COM',marker('B1'),1),('NAME.COM',marker('B15'),15)]
files += [(name+'.COM',marker('COLLIDE-'+name)) for name in ['DIR','ERA','REN','SAVE','TYPE','USER','DI','DIRX']]
files += [('ONE.TXT',b'FIRST\r\nLAST\x1aHIDDEN'),('EMPTY.TXT',b''),('TWO.TXT',b'SECOND\r\n\x1a'),('SYS.TXT',b'SYSTEM\x1a',0,2),('PRIVATE.TXT',b'USER1\x1a',1),('ERASE.TMP',b'ERASEME'),('KEEP.TMP',b'KEEPUSER1',1),('NEW.TXT',b'OTHERUSER',1),('LONG.TXT',b'LONGSTART\r\n'+b'0123456789'*20+b'\r\nLONGEND\x1aHIDDEN'),('CTRL.TXT',b'A\tB\x08C\r\nCONTROLEND\x1a')]
boot.install_files(b,files);(OUT/'b.dmk').write_bytes(build(b))
scenarios={
 'identity':['NAME','NAME.COM','NAME.TXT','VER'],
 'lookup':['B:','NAME','ONLYA','A:NAME','A:MISSING','VER'],
 'users':['B:','USER 1','NAME','DIR *.TXT','USER 0','NAME','USER 15','NAME','USER 16','VER'],
 'exact':['B:','DIR ONE.TXT','DI','DIRX','ERA MISSING.TXT','REN NEW=MISSING','TYPE MISSING','SAVE X BAD.DAT','USER 0','VER'],
 'directory':['B:','DIR','DIR *.TXT','DIR ONE.TXT','DIR SYS.TXT','DIR MISSING.TXT','DIR A:BTONE.DAT','DIR 1:*.TXT','VER'],
 'types':['B:','TYPE ONE.TXT','TYPE EMPTY.TXT','TYPE TWO.TXT','TYPE LONG.TXT','TYPE CTRL.TXT','TYPE MISSING.TXT','VER'],
 'erase':['B:','ERA ERASE.TMP','DIR *.TMP','ERA *.TXT','DIR *.TXT','DIR 1:*.TXT','VER'],
 'rename':['B:','REN NEW.TXT=ONE.TXT','DIR *.TXT','REN NEW.TXT=TWO.TXT','REN X.TXT=MISSING.TXT','REN B:X.TXT=A:BTONE.DAT','DIR *.TXT','VER'],
 'eraseall':['B:','ERA *.*','N','DIR *.TXT','ERA *.*','Y','DIR','DIR 1:*.TXT','VER'],
 'save':['B:','NAME','SAVE 2 MEM.BIN','DIR MEM.BIN','VER'],
 'missingtools':['STAT','SUBMIT TEST','XSUB','VER'],
}
def run(item):
 name,commands=item;w=OUT/name;w.mkdir()
 for letter in 'ab':shutil.copy2(OUT/(letter+'.dmk'),w/(letter+'.dmk'))
 args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(w/'a.dmk'),'-d1',str(w/'b.dmk'),'-id','3500']
 for command in commands:args+=key_args(command+'\r')+['-id','6000','-it']
 args+=['-ix']
 try:subprocess.run(args,cwd=w,check=True,timeout=360,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 except subprocess.TimeoutExpired:print(name,'TIMEOUT',flush=True)
 screens=[]
 for p in sorted(w.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.split('-')[-1])):
  raw=p.read_bytes()[:1920];screens.append('\n'.join(bytes(c&127 for c in raw[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80)))
 (w/'screens.txt').write_text('\n\n--- SCREEN ---\n\n'.join(screens))
 (w/'commands.json').write_text(json.dumps(commands,indent=2))
 print(name,len(screens),'screens',flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,[(k,v) for k,v in scenarios.items() if not sys.argv[1:] or k in sys.argv[1:]]))
print(OUT)
