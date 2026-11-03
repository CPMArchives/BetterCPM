#!/usr/bin/env python3
from pathlib import Path
import sys,json,hashlib
import argparse
parser=argparse.ArgumentParser(description='Qualify supplied Model 4 P2DOS with persistent case results and a guest completion oracle.')
parser.add_argument('--baseline',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--timeout',type=int,default=480)
args=parser.parse_args()
from add_cpm_file_to_dmk import extract_raw,add_file
from build_montezuma_extended_790k import build
from build_ccp import assemble
from test_z80pack_clock_lifecycle import PROBE
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run
from test_model4_copy import files
out=args.output.resolve();out.mkdir();(out/'frehd').mkdir()
# Preserve ABI checks, then persist each unique invocation result before JP 0.
writer='''        PUSH DE
        LD HL,OUTREC
        LD B,16
LOGCOPY:LD A,(DE)
        LD (HL),A
        INC DE
        INC HL
        DJNZ LOGCOPY
        LD DE,05CH
        LD C,22
        CALL 5
        INC A
        JP Z,0
        LD DE,OUTREC
        LD C,26
        CALL 5
        LD DE,05CH
        LD C,21
        CALL 5
        LD DE,05CH
        LD C,16
        CALL 5
        POP DE
'''
probe=PROBE.replace('PRINT:\n','PRINT:\n'+writer).replace('        END\n','OUTREC: DS 128\n        END\n');code=assemble(Path.home()/'bin/z80asm',probe,out/'CLKPROB.COM',out/'probe.lst',0x100)
report=json.loads((args.baseline/'report.json').read_text())
assert report['target']=='trs80gp'
source=(args.baseline/report['image']).resolve()
assert hashlib.sha256(source.read_bytes()).hexdigest()==report['sha256']
raw=extract_raw(source.read_bytes());add_file(raw,'CLKPROB.COM',code)
commands=['RSX LOAD M4SCRN','RSX LOAD ADM3A','CLKPROB C01 2','RSX LOAD FREHDCLK','RSX LOAD P2DOS','CLKPROB C02 0','RSX UNLOAD FREHDCLK','CLKPROB C03 1','RSX LOAD FREHDCLK','CLKPROB C04 0','RSX UNLOAD P2DOS','CLKPROB C05 2','TYPE DONE.TXT']
# Replace the startup batch, not any guest production binary.
from build_trs80_boot import FILESYSTEM_FIRST_SECTOR,DIRECTORY_ENTRIES
for i in range(DIRECTORY_ENTRIES):
 at=FILESYSTEM_FIRST_SECTOR*512+i*32
 if raw[at]==0 and bytes(raw[at+1:at+12])==b'STARTUP SUB':raw[at]=0xe5
add_file(raw,'STARTUP.SUB',('\r\n'.join(commands)+'\r\n\x1a').encode());add_file(raw,'DONE.TXT',b'QUALIFICATION COMPLETE\r\n\x1a');disk=out/'private.dmk';disk.write_bytes(build(raw))
cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-frehd_dir',str(out/'frehd'),'-d0',str(disk),'-itime','15000','-iw','QUALIFICATION COMPLETE','-id','500','-it','-ix'];(out/'invocation.json').write_text(json.dumps(cmd,indent=2));run(cmd,cwd=out,timeout=args.timeout)
actual=files(bytes(extract_raw(disk.read_bytes()))[20480:]);result={}
for n in ['C01','C02','C03','C04','C05']:
 data=actual[(0,n.encode().ljust(11))][0];assert data.startswith(b'CLOCK ABI PASS'),(n,data);result[n]=hashlib.sha256(data).hexdigest()
unchanged=[]
for entry in report['included']:
 if entry['name']=='STARTUP.SUB':continue
 name,_,ext=entry['name'].partition('.')
 key=(entry.get('user',0),name.encode().ljust(8)+ext.encode().ljust(3))
 assert hashlib.sha256(actual[key][0][:entry['bytes']]).hexdigest()==entry['sha256'],entry['name']
 unchanged.append(entry['name'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==report['sha256']
(out/'result.json').write_text(json.dumps({'status':'PASS','cases':result,'unchanged_shipped_files_except_private_startup':unchanged,'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'probe_sha256':hashlib.sha256(code).hexdigest(),'emulator_sha256':hashlib.sha256(DEFAULT_EMULATOR.read_bytes()).hexdigest(),'source_image_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Supplied P2DOS and FREHDCLK, absent/loaded/provider removed/replaced/frontend removed; ABI and failed GET atomicity before result logging. Only startup and probe/marker added on private image.'},indent=2));print('PASS')
