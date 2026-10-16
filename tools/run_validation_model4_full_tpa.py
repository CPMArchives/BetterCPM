#!/usr/bin/env python3
"""Observe native Model 4 full-TPA cross-user loads and protected returns."""
import sys,json,shutil,argparse,tempfile
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw,add_file,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run
from test_sysgen_install import screen
from run_validation_returning import sha
from run_validation_model4 import audit_files
parser=argparse.ArgumentParser(description=__doc__)
for name in ('baseline','fixtures','output'):parser.add_argument('--'+name,type=Path,required=True)
parser.add_argument('--prepare-only',action='store_true',help='create private manual-test images without launching the emulator')
a=parser.parse_args();ref=a.baseline.resolve();report=json.loads((ref/'report.json').read_text())
original=ref/report['image'];assert report['target']=='trs80gp' and sha(original)==report['sha256']
a.output.mkdir(parents=True,exist_ok=True)
work=Path(tempfile.mkdtemp(prefix='model4-full-tpa-',dir=a.output.resolve()))
raw=extract_raw(original.read_bytes());fixtures=a.fixtures.resolve()
# Isolate the unloaded-TPA contract from the shipping optional monitor profile.
# Only this declared fixture file changes; all other shipped files are audited.
for idx in range(DIRECTORY_ENTRIES):
 offset=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE+idx*32
 if raw[offset]==0 and raw[offset+1:offset+12]==b'STARTUP SUB':raw[offset]=0xE5
startup=b':VER /BANNER\r\n\x1a'
add_file(raw,'STARTUP.SUB',startup)

for name in ['STATE.COM','PAINT.COM','ERET.COM','EJUMP.COM','EFN0.COM','OVERRET.COM']:
 add_file(raw,name,(fixtures/name).read_bytes())
 if name.startswith(('ERET','EJUMP','EFN0','OVERRET')):
  for idx in range(DIRECTORY_ENTRIES):
   offset=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE+idx*32
   if raw[offset]==0 and raw[offset+1:offset+9].decode('ascii','replace').strip()==name.split('.')[0]:raw[offset]=7
image=work/'a.dmk';image.write_bytes(build(bytes(raw)));secondary=work/'b.dmk';secondary.write_bytes(build(b'\xe5'*len(raw)))
if a.prepare_only:
 manifest={'baseline_sha256':sha(original),'a':str(image),'b':str(secondary),
  'fixture_changes':['STARTUP.SUB: banner only; no optional RSX profile'],
  'fixtures':{name:sha(fixtures/name) for name in ['STATE.COM','PAINT.COM','ERET.COM','EJUMP.COM','EFN0.COM','OVERRET.COM']},
  'status':'PREPARED; not a test pass'}
 (work/'manual-fixture.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps(manifest,indent=2));sys.exit(0)
args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-d1',str(secondary),'-itime','20000','-iw','Type TYPE README.TXT for more','-id','2000','-it']
args+=key_args('A0:STATE\r')+['-id','120','-it','-iw','STATE D=00 U=00 TOP=D501','-id','2000']
args+=key_args('B31:\r')+['-id','2000']
for name,route in [('ERET','RET'),('EJUMP','JUMP'),('EFN0','FUNCTION0')]:
 args+=key_args('A0:PAINT\r')+['-id','2000']
 args+=key_args('A7:'+name+'\r')+['-iw','FULL-TPA '+route+' ENTERED','-id','2000','-it']
 args+=key_args('A0:STATE\r')+['-iw','STATE D=01 U=1F TOP=D501','-id','120','-it','-id','2000']
args+=key_args('A7:OVERRET\r')+['-id','2000','-it']
args+=key_args('A0:STATE\r')+['-iw','STATE D=01 U=1F TOP=D501','-id','120','-it','-ix']
try:
 run(args,cwd=work,timeout=600)
 if not all((work/f'trs80-text-{idx}.bin').is_file() for idx in range(10)):
  raise AssertionError('native run did not reach all capture checkpoints')
except BaseException as error:
 assert sha(original)==report['sha256'], 'reference image changed during incomplete run'
 (work/'incomplete.json').write_text(json.dumps({'status':'INCOMPLETE','error':str(error),
  'captures':sorted(path.name for path in work.glob('trs80-text-*.bin')),
  'baseline_sha256':sha(original)},indent=2)+'\n')
 raise
captures=[]
for idx in range(8):
 text=screen(work/f'trs80-text-{idx+2}.bin');(work/f'case-{idx}.txt').write_text(text+'\n')
 assert 'PATTERN OR RETURN FAILED' not in text
 if idx in (0,2,4):assert 'FULL-TPA '+('RET','JUMP','FUNCTION0')[idx//2]+' ENTERED' in text
 if idx in (1,3,5,7):
  assert 'A0:STATE' in text
  assert 'STATE D=01 U=1F TOP=D501' in text.rsplit('A0:STATE',1)[-1]
 if idx==6:
  assert 'A7:OVERRET' in text
  assert 'FULL-TPA' not in text.rsplit('A7:OVERRET',1)[-1],'oversized command executed'
 captures.append({'screen':f'case-{idx}.txt','status':'PASS'})
audit_report=dict(report,included=[item for item in report['included'] if item['name']!='STARTUP.SUB'])
audit=audit_files(original,image,audit_report,work);assert sha(original)==report['sha256']
audit['declared_fixture_changes']=['STARTUP.SUB: banner only, no optional monitor profile']
(work/'result.json').write_text(json.dumps({'status':'PASS','caller':'B31','lookup':'A7','captures':captures,'file_audit':audit,'baseline_sha256':sha(original),'emulator_sha256':sha(DEFAULT_EMULATOR),'fixtures':{name:sha(fixtures/name) for name in ['STATE.COM','PAINT.COM','ERET.COM','EJUMP.COM','EFN0.COM','OVERRET.COM']}},indent=2)+'\n');print(work)
