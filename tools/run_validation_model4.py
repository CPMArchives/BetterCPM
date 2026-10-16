#!/usr/bin/env python3
"""Boot a private Model 4 System Disk and capture small returning suite groups."""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw, add_file
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR, key_args
from trs80gp_launch import run
from test_sysgen_install import screen


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--suite',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    report=json.loads((a.baseline/'report.json').read_text())
    original=a.baseline/report['image']
    assert report['target']=='trs80gp' and sha(original)==report['sha256']
    hashes={line.split()[1]:line.split()[0] for line in (a.suite/'suite/build/SHA256SUMS.txt').read_text().splitlines() if line.strip()}
    a.output.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='model4-returning-',dir=a.output.resolve()))
    raw=extract_raw(original.read_bytes());programs={}
    for name in ('CPUTEST','ECOTEST','DISKTEST'):
        program=a.suite/f'suite/build/{name}.COM'
        assert sha(program)==hashes[name+'.COM']
        programs[name]=sha(program);add_file(raw,name+'.COM',program.read_bytes())
    fixture=a.suite/'suite/runtime-payload/BTONE.DAT'
    assert fixture.stat().st_size==128
    add_file(raw,'BTONE.DAT',fixture.read_bytes())
    image=work/'a.dmk';image.write_bytes(build(bytes(raw)))
    # Default Model 4 B: is an OFF=0, 800K data format, unlike boot A:.
    blank=bytearray(b'\xE5')*len(raw)
    secondary=work/'b.dmk';secondary.write_bytes(build(bytes(blank)))
    checks=[('CPUTEST /ALL','0627  -  S','Summary: 2 pass, 0 fail, 0 error'),
            ('ECOTEST /GROUP:REQUIRED','0579  -  R','Summary: 1 pass, 0 fail, 0 error'),
            ('DISKTEST /SAFE','0378  ','Summary: 7 pass, 0 fail, 0 error')]
    args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-d1',str(secondary),
          '-itime','15000','-iw','Type TYPE README.TXT for more','-id','6000','-it']
    for command,last_row,expected in checks:
        args+=key_args(command+'\r')+['-iw',last_row,'-id','120','-it','-id','6000']
    args+=['-ix']
    run(args,cwd=work,timeout=300)
    captures=[]
    for index,(command,last_row,expected) in enumerate(checks,1):
        text=screen(work/f'trs80-text-{index}.bin')
        (work/f'case-{index}.txt').write_text(text+'\n')
        captures.append({'command':command,'expected_summary':expected,'status':'PASS' if expected in text else 'FAIL','screen':f'case-{index}.txt'})
    assert sha(original)==report['sha256']
    result={'baseline_sha256':report['sha256'],'programs':programs,'fixture_sha256':sha(fixture),
            'emulator_sha256':sha(DEFAULT_EMULATOR),'captures':captures,
            'scope':'three small aggregate groups; captured summaries/rows, exclusions are not passes'}
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'groups':3,'results':captures,'evidence':str(work)},indent=2))
    assert all(c['status']=='PASS' for c in captures),'Model 4 group failed; see retained result/screens'


if __name__=='__main__':main()
