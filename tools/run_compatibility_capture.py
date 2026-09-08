#!/usr/bin/env python3
"""Capture suite screens on private four-drive trs80gp media; no guest patches.

Arguments are commands; optional ~ separates delayed keyboard responses.
Results are observations, not an automatic certification.
"""
import os,sys,subprocess,shutil,time,re,json,concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from run_trs80_command import key_args,DEFAULT_EMULATOR
import build_trs80_boot as boot
import add_cpm_file_to_dmk  # capture SYSTEM geometry before making DATA fixtures
from build_montezuma_extended_790k import build,RAW_SIZE
OUT=ROOT/'build/compatibility'/time.strftime('run-%Y%m%d-%H%M%S');OUT.mkdir(parents=True)
boot.FILESYSTEM_FIRST_SECTOR=0;boot.BLOCK_COUNT=RAW_SIZE//2048
bdos=(ROOT.parent/'cpm-compatibility/suite/build/BDOSTEST.COM').read_bytes()
for letter,files in [('b',[('BDOSTEST.COM',bdos),('BDSA.TMP',bdos),('BDSB.TMP',bdos)]),('c',[('BTBFILE.DAT',boot.CROSS_FIXTURE)]),('d',[])]:
 raw=bytearray(b'\xe5'*RAW_SIZE);boot.install_files(raw,files);(OUT/(letter+'.dmk')).write_bytes(build(raw))
def screen(p):
 raw=p.read_bytes()[:1920];return '\n'.join(bytes(c&127 for c in raw[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80))
def run(command):
 parts=command.split('~');command=parts[0];name=re.sub(r'[^A-Za-z0-9_.:-]', '_', '_'.join(parts).replace('/',''));w=OUT/name;w.mkdir(exist_ok=True)
 shutil.copy2(Path(os.environ.get('BETTERCPM_TEST_IMAGE', str(ROOT/'build/compatibility/BetterCPM-Compatibility.dmk'))),w/'a.dmk')
 args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo']
 for i,l in enumerate('abcd'):
  if l!='a':shutil.copy2(OUT/(l+'.dmk'),w/(l+'.dmk'))
  args += [f'-d{i}',str(w/(l+'.dmk'))]
 if command.startswith(('FILETEST /0253','FILETEST /ALL','RANDTEST /0556','RANDTEST /0557','RANDTEST /GROUP:LIFECYCLE')):
  raw=bytearray(b'\xe5'*RAW_SIZE);full=bytearray(128*128);full[-128:-120]=b'FULL-127'
  boot.install_files(raw,[('BTFULL.DAT',bytes(full))]+[(f'F{i:07d}.DAT',b'') for i in range(127)])
  (w/'d.dmk').write_bytes(build(raw))
 if command == 'DISKTEST /ALL' or command.startswith(tuple('DISKTEST /'+str(n).zfill(4) for n in range(379,385))):
  raw=bytearray(b'\xe5'*RAW_SIZE)
  full=bytearray(128*128);full[-128:-120]=b'FULL-127'
  boot.install_files(raw,[('BTFULL.DAT',bytes(full)),('BTREL.DAT',bytes(128)),('BTFILL.DAT',bytes((boot.BLOCK_COUNT-11)*2048))])
  (w/'d.dmk').write_bytes(build(raw))
 if command.startswith('RANDTEST /0346'):
  # This case writes until full. Leave two blocks free so the same boundary
  # is exercised without minutes of unrelated floppy transfers.
  from add_cpm_file_to_dmk import extract_raw,add_file
  raw=extract_raw((w/'a.dmk').read_bytes())
  from add_cpm_file_to_dmk import FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,BLOCK_COUNT,FIRST_DATA_BLOCK,DIRECTORY_ENTRIES
  used=set(range(FIRST_DATA_BLOCK)); directory=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
  for offset in range(directory,directory+DIRECTORY_ENTRIES*32,32):
   entry=raw[offset:offset+32]
   if entry[0]<16:
    used.update(int.from_bytes(entry[i:i+2],'little') for i in range(16,32,2))
  free=BLOCK_COUNT-len(used)
  assert free>2
  add_file(raw,'CAPACITY.DAT',bytes((free-2)*2048))
  (w/'a.dmk').write_bytes(build(raw))
  (w/'fixture.json').write_text(json.dumps({'free_blocks_before':free,'free_blocks_for_test':2}))
 if command.startswith(('RANDTEST /0368','RANDTEST /0369')):
  from add_cpm_file_to_dmk import extract_raw,add_file,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
  raw=extract_raw((w/'a.dmk').read_bytes())
  directory=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
  for offset in range(directory,directory+DIRECTORY_ENTRIES*32,32):
   if raw[offset+1:offset+12]==b'BTRO    DAT': raw[offset+9] |= 0x80
  (w/'a.dmk').write_bytes(build(raw))
  (w/'fixture.json').write_text(json.dumps({'file':'A:BTRO.DAT','read_only':True,'marker':'READONLY-000'}))
 shutil.copy2(w/'d.dmk',w/'d-before.dmk')
 args+=['-id','3500']+key_args(command+'\r')
 for index,response in enumerate(parts[1:]):
  # Console programs can take longer to load than a fixed keyboard delay.
  # The screen handshake is part of the instrument, not a guest-code patch.
  case=re.match(r'CONSTEST /(\d{4})',command)
  if command.startswith(('BIOSTEST /0439','BIOSTEST /0445','BIOSTEST /0448')):
   args += ['-iw', 'Run controlled console/logical-device tests' if index==0 else 'Type one uppercase K now:', '-it']
  elif index==0 and (command.startswith('DISKTEST /03') or command.startswith('BIOSTEST /042')):
   args += ['-iw','Enter its configured drive letter','-it']
  elif case and response=='Y' and (index>0 or len(parts)==2):
   args += ['-iw','Do OBSERVED and EXPECTED match?','-it']
  elif case and index==0:
   args += ['-iw','Probe '+case[1]+':','-it']
  else:
   args += ['-id',os.environ.get('BETTERCPM_RESPONSE_FRAMES','6000'),'-it']
  args += key_args(response.replace('\\r','\r'))
 for _ in range(1500):args+=['-id','100','-it']
 args+=['-ix']
 start=time.time(); proc=subprocess.Popen(args,cwd=w,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 seen=set();rows={};frames=[];last='';same=time.time();reason='frame budget'
 try:
  while proc.poll() is None:
   for p in sorted(w.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.split('-')[-1])):
    if p.name in seen:continue
    s=screen(p)
    if len(p.read_bytes())<1920:continue
    seen.add(p.name)
    if s!=last:frames.append(s);last=s;same=time.time()
    for line in s.splitlines():
     m=re.match(r'^(\d{4})\s+([PFEOS?-])\s+([RNXS])\s+(.*)',line)
     if m and (m[1] not in rows or len(line)>=len(rows[m[1]])):rows[m[1]]=line
   if re.search(r'^[A-P]\d+>[^\w\s]?\s*$',last,re.M) and len(seen)>10:
    reason='returned to CCP';break
   if time.time()-same>(240 if command.startswith('RANDTEST /0346') else float(os.environ.get('BETTERCPM_STABLE_SECONDS','60'))) and len(seen)>len(parts)+10:
    reason='stopped at stable screen (prompt or stalled test)';break
   if time.time()-start>480:reason='host time budget';break
   time.sleep(.25)
 finally:
  if proc.poll() is None:proc.terminate()
  try:proc.communicate(timeout=5)
  except subprocess.TimeoutExpired:proc.kill();proc.communicate()
 (w/'screens.txt').write_text('\n\n--- SCREEN ---\n\n'.join(frames))
 (w/'rows.txt').write_text('\n'.join(rows[k] for k in sorted(rows))+'\n')
 (w/'final.txt').write_text(last+'\n')
 (w/'result.json').write_text(json.dumps({'command':command,'responses':parts[1:],'end':reason,'seconds':time.time()-start,'rows':len(rows)},indent=2))
 print(name,reason,len(rows),'rows',flush=True)
commands=sys.argv[1:] or [n+' /ALL' for n in 'ENTRYTST BDOSTEST FILETEST RANDTEST DIRTEST CONSTEST CCPTEST DISKTEST BIOSTEST ERRTEST ECOTEST CPUTEST'.split()]
with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.environ.get("BETTERCPM_WORKERS","3"))) as pool:list(pool.map(run,commands))
