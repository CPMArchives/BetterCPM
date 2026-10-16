#!/usr/bin/env python3
"""Run pinned directory/BDOS groups on private native Model 4 data disks."""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR, key_args
from run_validation_model4 import sha, audit_files
from test_sysgen_install import screen
from trs80gp_launch import run


def audit_data(work):
    results={}
    for letter in 'bc':
        raw=work/f'{letter}-after.raw'
        raw.write_bytes(extract_raw((work/f'{letter}.dmk').read_bytes()))
        checked=subprocess.run(['fsck.cpm','-T','raw','-f','native-data','-n',str(raw)],cwd=work,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (work/f'{letter}-filesystem.txt').write_text(checked.stdout)
        results[letter]={'sha256':sha(raw),'filesystem_status':checked.returncode}
        assert checked.returncode==0, 'data filesystem check failed: '+letter
    (work/'data-audit.json').write_text(json.dumps(results,indent=2)+'\n')
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','suite','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--program',choices=('DIRTEST','BDOSTEST'),required=True)
    args=parser.parse_args()
    report=json.loads((args.baseline/'report.json').read_text())
    original=args.baseline/report['image']
    assert report['target']=='trs80gp' and sha(original)==report['sha256']
    program=args.suite/f'suite/build/{args.program}.COM'
    hashes={line.split()[1]:line.split()[0] for line in (args.suite/'suite/build/SHA256SUMS.txt').read_text().splitlines() if line.strip()}
    assert sha(program)==hashes[program.name]
    args.output.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix=args.program.lower()+'-',dir=args.output.resolve()))
    image=work/'a.dmk';shutil.copy2(original,image)
    # Default Model 4 B/C data profiles have no reserved system-track prefix.
    (work/'diskdefs').write_text('diskdef native-data\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 0\n os 2.2\nend\n')
    blank=b'\xe5'*len(extract_raw(original.read_bytes()))
    data={letter:work/f'{letter}.raw' for letter in 'bc'}
    for path in data.values():path.write_bytes(blank)
    fixtures=[]
    def install(path,name,user=0,drive='b'):
        subprocess.run(['cpmcp','-T','raw','-f','native-data',str(data[drive]),str(path),f'{user}:{name}'],cwd=work,check=True)
        fixtures.append({'drive':drive.upper(),'user':user,'name':name,'bytes':path.stat().st_size,'sha256':sha(path)})
    install(program,program.name)
    payload=args.suite/'suite/runtime-payload'
    for path in sorted(payload.iterdir()):
        if path.suffix.upper() in ('.DAT','.CFG'):install(path,path.name)
    install(payload/'BTUSR.DAT','BTUSR.DAT',user=1)
    subprocess.run(['cpmchmod','-T','raw','-f','native-data',str(data['b']),'0444','0:BTRO.DAT'],cwd=work,check=True)
    cross=work/'BTBFILE.DAT';cross.write_bytes((b'BFILE-000 '*15)[:128])
    install(cross,cross.name,drive='c')
    if args.program=='BDOSTEST':
        for name in ('BDSA.TMP','BDSB.TMP'):install(payload/'BTEMPTY.DAT',name)
    for letter,path in data.items():(work/f'{letter}.dmk').write_bytes(build(path.read_bytes()))
    selector='/SAFE' if args.program=='DIRTEST' else '/GROUP:REQUIRED'
    last='0566  ' if args.program=='DIRTEST' else '0531  '
    passes=49 if args.program=='DIRTEST' else 56
    expected=f'Summary: {passes} pass, 0 fail, 0 error'
    command=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-d1',str(work/'b.dmk'),'-d2',str(work/'c.dmk'),'-itime','15000','-iw','Type TYPE README.TXT for more','-id','6000']
    command+=key_args('B:\r')+['-id','6000','-it']
    command+=key_args(args.program+' '+selector+'\r')+['-iw',last,'-id','120','-it','-ix']
    initial={letter:sha(work/f'{letter}.dmk') for letter in 'abc'}
    try:
        run(command,cwd=work,timeout=900)
    except Exception as error:
        (work/'run-error.json').write_text(json.dumps({'status':'ERROR','error_type':type(error).__name__,'message':str(error),'initial_disks':initial,'fixtures':fixtures},indent=2)+'\n')
        raise
    ready=screen(work/'trs80-text-0.bin')
    (work/'drive-ready.txt').write_text(ready+'\n')
    assert any(line.startswith('B0>') for line in ready.splitlines()), 'drive-change readiness capture was not the B prompt'
    text=screen(work/'trs80-text-1.bin')
    (work/'screen.txt').write_text(text+'\n')
    result={'baseline_sha256':report['sha256'],'program_sha256':sha(program),'emulator_sha256':sha(DEFAULT_EMULATOR),'fixtures':fixtures,'read_only_fixture':'B0:BTRO.DAT','command':args.program+' '+selector,'expected_summary':expected,'suite_status':'PASS' if expected in text else 'FAIL','status':'PENDING_AUDIT','initial_disks':initial,'final_disks':{letter:sha(work/f'{letter}.dmk') for letter in 'abc'},'scope':'native final aggregate summary and trailing rows; manual/excluded cards are not passes; no complete scrolling transcript'}
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    assert sha(original)==report['sha256']
    try:
        result['data_filesystem_audit']=audit_data(work)
        result['system_file_audit']=audit_files(original,image,report,work)
    except Exception as error:
        result['status']='ERROR'
        result['audit_error']=str(error)
        (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        raise
    result['status']=result['suite_status']
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'evidence':str(work),'expected_summary':expected},indent=2),flush=True)
    assert result['status']=='PASS','native group failed; see retained screens'


if __name__=='__main__':main()
