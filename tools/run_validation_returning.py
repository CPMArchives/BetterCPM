#!/usr/bin/env python3
"""Capture reviewed returning suite groups on private copies of a baseline disk.

Results are fresh observations, not whole-system certification. Other programs
need their separately reviewed scratch fixtures and operator procedures.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from test_z80pack_sysgen_install import session

COMMANDS={'ENTRYTST':'/GROUP:REQUIRED','ECOTEST':'/GROUP:REQUIRED','CPUTEST':'/ALL','BDOSTEST':'/GROUP:GATEWAY'}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True,help='immutable z80pack release directory with report.json')
    parser.add_argument('--diskdefs',type=Path,required=True)
    parser.add_argument('--suite',type=Path,required=True,help='pinned private suite clone with freshly rebuilt suite/build')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--program',choices=COMMANDS,required=True)
    parser.add_argument('--case',choices=['0023','0024','0513'],help='rerun a triaged individual case')
    parser.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    args=parser.parse_args()
    baseline=args.baseline.resolve();suite=args.suite.resolve()
    report=json.loads((baseline/'report.json').read_text())
    if report['target']!='z80pack':raise ValueError('cpmsim baseline required')
    original=baseline/report['image']
    if sha(original)!=report['sha256']:raise ValueError('baseline image hash mismatch')
    name=args.program+'.COM';program=suite/'suite/build'/name
    hashes={line.split()[1]:line.split()[0] for line in (suite/'suite/build/SHA256SUMS.txt').read_text().splitlines() if line.strip()}
    if sha(program)!=hashes[name]:raise ValueError('rebuilt suite program hash mismatch')
    args.output.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix=args.program.lower()+'-',dir=args.output.resolve()))
    disks=work/'disks';disks.mkdir();image=disks/'drivea.dsk';shutil.copy2(original,image)
    shutil.copy2(args.diskdefs,work/'diskdefs')
    subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(program),'0:'+name],cwd=work,check=True)
    fixtures=[]
    if args.program=='ECOTEST':
        fixture=suite/'suite/runtime-payload/BTONE.DAT'
        if fixture.stat().st_size!=128:raise ValueError('BTONE must be exactly one record')
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(fixture),'0:BTONE.DAT'],cwd=work,check=True)
        fixtures.append({'name':'BTONE.DAT','sha256':sha(fixture),'bytes':128})
    if args.case and ((args.program=='ENTRYTST' and args.case not in ('0023','0024')) or (args.program!='ENTRYTST' and not(args.program=='ECOTEST' and args.case=='0513'))):raise ValueError('case not reviewed for this program')
    command=args.program+' '+('/'+args.case if args.case else COMMANDS[args.program])
    trace=session(args.simulator.resolve(),disks,[(command.encode()+b'\r',b'Summary:',60),(b'',b'A0>_ ',30),(b'BYE\r',b'System halted',10)],work/'transcript.bin')
    text=trace.decode('ascii',errors='replace');rows={}
    for match in re.finditer(r'^\s*(\d{4})\s+([PFEOS?\-])\s+([A-Z?])\s+([^\r\n]*)',text,re.M):
        item,status,classification,observed=match.groups()
        if item in rows:raise ValueError('duplicate result row '+item)
        rows[item]={'status':status,'class':classification,'observed':observed.strip()}
    if not rows:raise ValueError('no classified result rows captured')
    counts={status:sum(row['status']==status for row in rows.values()) for status in sorted({r['status'] for r in rows.values()})}
    summary=re.search(r'Summary:[^\r\n]*',text)
    result={'baseline_revision':report['source']['revision'],'baseline_sha256':report['sha256'],'suite_revision':subprocess.check_output(['git','-C',str(suite),'rev-parse','HEAD'],text=True).strip(),'program_sha256':sha(program),'simulator_sha256':sha(args.simulator),'command':command,'fixtures':fixtures,'rows':rows,'counts':counts,'printed_summary':summary.group() if summary else None,'scope':'selected returning group only; observations/exclusions/not-run are not passes','failed_or_error_rows':[k for k,v in rows.items() if v['status'] in ('F','E')]}
    if sha(original)!=report['sha256']:raise ValueError('reference image changed')
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'command':command,'counts':counts,'failed_or_error_rows':result['failed_or_error_rows'],'evidence':str(work)},indent=2))


if __name__=='__main__':main()
