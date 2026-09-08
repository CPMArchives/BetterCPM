import sys,json,hashlib
from pathlib import Path
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'tools'))
from add_cpm_file_to_dmk import extract_raw,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
b=r/'build/compatibility';out=json.loads((b/'campaign-manual.json').read_text()) if (b/'campaign-manual.json').exists() else {}
def put(i,status,detail,p):
 out.setdefault(i,{'result':status,'detail':detail,'evidence':str(p.relative_to(r))})
for i in ('0063','0064','0078'):
 p=b/'console-pause'/str(int(i))/'result.json'
 if p.exists() and json.loads(p.read_text())['passed']:put(i,'P',json.loads(p.read_text())['rule'],p)
p=b/'run-20260907-224546/CONSTEST_0077/final.txt'
assert 'OBSERVED bytes/display: [A\tB]' in p.read_text();put('0077','P','Captured screen memory contains A, byte 09h, B in three adjacent cells; no BDOS space expansion.',p)
p=b/'run-20260907-223415/CONSTEST_0117_Z___VER_/final.txt'
assert 'A0>' in p.read_text() and 'OBSERVED: Function 10 returned' not in p.read_text();put('0117','P','Initial Ctrl-C left the input call through warm restart and returned to the CCP.',p)
for i,util in [('0025','CCPTEST'),('0028','CCPTEST'),('0026','ENTRYTST'),('0027','ENTRYTST')]:
 p=b/f'run-20260907-222051/{util}_{i}_Z/final.txt';s=p.read_text();assert 'test: Z' in s and s.rstrip().endswith('A0>');put(i,'P','Executed documented termination path; fresh CCP prompt captured after transfer.',p)
def filebytes(image):
 raw=extract_raw(image.read_bytes());base=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE;result=bytearray()
 for off in range(base,base+DIRECTORY_ENTRIES*32,32):
  e=raw[off:off+32]
  if e[0]==0 and bytes(x&127 for x in e[1:12])==b'BTRO    DAT':
   remaining=e[15]*128
   for j in range(16,32,2):
    block=int.from_bytes(e[j:j+2],'little')
    if not block or not remaining:break
    n=min(remaining,2048);result+=raw[base+block*2048:base+block*2048+n];remaining-=n
 return bytes(result)
before=filebytes(b/'BetterCPM-Compatibility-Console.dmk');assert before
for i in ('0368','0369'):
 w=b/f'run-20260907-222051/RANDTEST_{i}:REPORT';s=(w/'final.txt').read_text();assert 'File R/O' in s and s.rstrip().endswith('A0>') and filebytes(w/'a.dmk')==before
 put(i,'P','Read-only file write produced File R/O and warm restart; file bytes match pristine fixture.',w/'final.txt')
p=b/'bios-boundary/457/screens.txt';assert '0457  P  R' in p.read_text();put('0457','P','Real emulator write protection: status 01 protected, 00 restored; 128-byte transfer passed.',p)
for i in range(379,385):
 w=b/f'run-20260907-223510/DISKTEST_{i:04d}_D_VER_r';s=(w/'final.txt').read_text()
 assert 'Q): D' in s and 'FAIL: protected mutation returned' in s
 assert (w/'d.dmk').read_bytes()==(w/'d-before.dmk').read_bytes()
 put(f'{i:04d}','F','Disk bytes unchanged, but BDOS returned to the caller instead of the required R/O diagnostic and warm restart.',w/'final.txt')
p=b/'run-20260907-222250/___VER_r/final.txt';put('0479','F','A SPACE-only command produced ? instead of silently returning to the prompt; VER recovery succeeded.',p)
(b/'campaign-manual.json').write_text(json.dumps(out,indent=2)+'\n');print(len(out),'external verdicts recorded')
