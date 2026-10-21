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
# Let SUBMIT queue commands across reconstruction. Fixed delays between PAINT
# and the next COM can otherwise drop keystrokes while the CCP is reloading.
from build_ccp import assemble
shutil.copy2(__file__,work/'executed-runner.py')
commands=['A0:STATE','B31:']
for index,name in enumerate(('ERET','EJUMP','EFN0','OVERRET')):
 if index<3:commands.append('A0:PAINT')
 commands += ['A7:'+name,'A0:STATE',f'A0:NFG{index}']
 source=f""" ORG 100H
 LD DE,MSG
 LD C,9
 CALL 5
 LD C,1
 CALL 5
 LD E,28
 LD C,2
 CALL 5
 RET
MSG: DB 'NATIVE FULL TPA GATE {index}',13,10,'$'
 END
"""
 binary=assemble(Path.home()/'bin/z80asm',source,work/f'NFG{index}.COM',work/f'NFG{index}.lst',0x100)
 (work/f'NFG{index}.asm').write_text(source);add_file(raw,f'NFG{index}.COM',binary)
commands.append('A0:NFDONE')
source=" ORG 100H\n LD DE,MSG\n LD C,9\n CALL 5\n RET\nMSG: DB 'NATIVE FULL TPA COMPLETE',13,10,'$'\n END\n"
binary=assemble(Path.home()/'bin/z80asm',source,work/'NFDONE.COM',work/'NFDONE.lst',0x100)
(work/'NFDONE.asm').write_text(source);add_file(raw,'NFDONE.COM',binary)
script=('\r\n'.join(commands)+'\r\n\x1a').encode();(work/'FTPA.SUB').write_bytes(script);add_file(raw,'FTPA.SUB',script);image.write_bytes(build(bytes(raw)))
args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-d1',str(secondary),'-itime','20000','-iw','Type TYPE README.TXT for more','-id','6000','-it']
args+=key_args('SUBMIT FTPA\r')
for index in range(4):args+=['-iw',f'NATIVE FULL TPA GATE {index}','-id','120','-it']+key_args(' ')
args+=['-iw','NATIVE FULL TPA COMPLETE','-id','6000','-it','-ix']
(work/'invocation.json').write_text(json.dumps(args,indent=2)+'\n')
try:
 run(args,cwd=work,timeout=1200)
 if not all((work/f'trs80-text-{idx}.bin').is_file() for idx in range(6)):
  raise AssertionError('native run did not reach all queued capture checkpoints')
except BaseException as error:
 assert sha(original)==report['sha256'], 'reference image changed during incomplete run'
 (work/'incomplete.json').write_text(json.dumps({'status':'INCOMPLETE','error':str(error),
  'captures':sorted(path.name for path in work.glob('trs80-text-*.bin')),
  'baseline_sha256':sha(original)},indent=2)+'\n')
 raise
captures=[]
for index in range(4):
 text=screen(work/f'trs80-text-{index+1}.bin');(work/f'case-{index}.txt').write_text(text+'\n')
 assert 'PATTERN OR RETURN FAILED' not in text
 assert 'STATE D=01 U=1F TOP=D501' in text
 assert f'NATIVE FULL TPA GATE {index}' in text
 if index<3:assert 'FULL-TPA '+('RET','JUMP','FUNCTION0')[index]+' ENTERED' in text
 else:
  assert 'A7:OVERRET' in text
  assert 'FULL-TPA' not in text, 'oversized command executed'
 captures.append({'screen':f'case-{index}.txt','status':'PASS'})
final=screen(work/'trs80-text-5.bin');(work/'final.txt').write_text(final+'\n')
assert 'NATIVE FULL TPA COMPLETE' in final and final.rstrip().endswith('B31>')
audit_report=dict(report,included=[item for item in report['included'] if item['name']!='STARTUP.SUB'])
audit=audit_files(original,image,audit_report,work);assert sha(original)==report['sha256']
audit['declared_fixture_changes']=['STARTUP.SUB: banner only, no optional monitor profile']
(work/'result.json').write_text(json.dumps({'status':'PASS','caller':'B31','lookup':'A7','captures':captures,'file_audit':audit,'baseline_sha256':sha(original),'emulator_sha256':sha(DEFAULT_EMULATOR),'queued_submit_and_explicit_input_gates':True,'fixtures':{name:sha(fixtures/name) for name in ['STATE.COM','PAINT.COM','ERET.COM','EJUMP.COM','EFN0.COM','OVERRET.COM']},'gate_sha256':{f'NFG{i}.COM':sha(work/f'NFG{i}.COM') for i in range(4)},'script_sha256':sha(work/'FTPA.SUB')},indent=2)+'\n');print(work)
