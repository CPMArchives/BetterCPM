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

COMMANDS={'CCPTEST':'/GROUP:REQUIRED','ENTRYTST':'/GROUP:REQUIRED','ECOTEST':'/GROUP:REQUIRED','CPUTEST':'/ALL','BDOSTEST':'/GROUP:REQUIRED','DIRTEST':'/SAFE','FILETEST':'/SAFE','RANDTEST':'/SAFE','DISKTEST':'/SAFE','BIOSTEST':'/SAFE','ERRTEST':'/SAFE'}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True,help='immutable z80pack release directory with report.json')
    parser.add_argument('--diskdefs',type=Path,required=True)
    parser.add_argument('--suite',type=Path,required=True,help='pinned private suite clone with freshly rebuilt suite/build')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--program',choices=COMMANDS,required=True)
    parser.add_argument('--disk-required',action='store_true',help='DISKTEST required group on prepared D: allocation-full disk')
    parser.add_argument('--file-required',action='store_true',help='reviewed FILETEST required group with full D: fixture')
    parser.add_argument('--case',choices=['0023','0024','0513'],help='rerun a triaged individual case')
    parser.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    args=parser.parse_args()
    if args.file_required and args.program!='FILETEST':parser.error('--file-required requires FILETEST')
    if args.disk_required and args.program!='DISKTEST':parser.error('--disk-required requires DISKTEST')
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
    fixtures=[]
    data_suite=args.program in ('DIRTEST','FILETEST','RANDTEST','BDOSTEST','ERRTEST','DISKTEST')
    target=image
    if data_suite:
        # Use an expendable B: so suite-created large files have the full
        # data area and never compete with System Disk contents.
        for letter in 'bcd':
            data_disk=disks/f'drive{letter}.dsk';shutil.copy2(original,data_disk)
            subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(data_disk),'0:*.*'],cwd=work,check=True)
        target=disks/'driveb.dsk'
    def install(source,destination):
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(target),str(source),destination],cwd=work,check=True)
    install(program,'0:'+name)
    if data_suite:
        payload=suite/'suite/runtime-payload'
        for fixture in sorted(payload.iterdir()):
            if fixture.suffix.upper() not in ('.DAT','.CFG'):continue
            install(fixture,'0:'+fixture.name)
            fixtures.append({'name':fixture.name,'user':0,'sha256':sha(fixture),'bytes':fixture.stat().st_size})
        install(payload/'BTUSR.DAT','1:BTUSR.DAT')
        if args.program=='BDOSTEST':
            for pair_name in ('BDSA.TMP','BDSB.TMP'):
                install(payload/'BTEMPTY.DAT','0:'+pair_name)
                fixtures.append({'name':pair_name,'drive':'B','user':0,'sha256':sha(payload/'BTEMPTY.DAT'),'bytes':0})
        subprocess.run(['cpmchmod','-T','raw','-f','bettercpm-default',str(target),'0444','0:BTRO.DAT'],cwd=work,check=True)
        fixtures.append({'name':'BTUSR.DAT','user':1,'sha256':sha(payload/'BTUSR.DAT')})
        fixtures.append({'name':'BTRO.DAT','user':0,'read_only':True})
        cross=work/'BTBFILE.DAT';cross.write_bytes((b'BFILE-000 '*15)[:128])
        target=disks/'drivec.dsk';install(cross,'0:BTBFILE.DAT');target=disks/'driveb.dsk'
        fixtures.append({'name':'BTBFILE.DAT','drive':'C','sha256':sha(cross),'bytes':128})
        if args.program=='RANDTEST' or args.file_required or args.disk_required:
            # Lifecycle 0556/0557 require failed growth on prepared D:.
            # Match SCRATCH /DISK: 128-record control + release + filler.
            definition=(work/'diskdefs').read_text().split('end',1)[0]
            geometry={k:int(re.search(r'(?m)^\s*'+k+r'\s+(\d+)',definition)[1])
                      for k in ('tracks','boottrk','sectrk','seclen','blocksize','maxdir')}
            block=geometry['blocksize']
            blocks=(geometry['tracks']-geometry['boottrk'])*geometry['sectrk']*geometry['seclen']//block
            directory_blocks=(geometry['maxdir']*32+block-1)//block
            control=bytearray(128*128);control[-128:-120]=b'FULL-127'
            control_path=work/'BTFULL.DAT';control_path.write_bytes(control)
            release=work/'BTREL.DAT';release.write_bytes(bytes(128))
            filler=work/'BTFILL.DAT'
            filler.write_bytes(bytes((blocks-directory_blocks-(len(control)+block-1)//block-1)*block))
            target=disks/'drived.dsk'
            for fixture in (control_path,release,filler):
                install(fixture,'0:'+fixture.name)
                fixtures.append({'name':fixture.name,'drive':'D','sha256':sha(fixture),'bytes':fixture.stat().st_size})
            physical_extent=16//(1 if blocks<=256 else 2)*block
            used_entries=sum(max(1,(f.stat().st_size+physical_extent-1)//physical_extent)
                             for f in (control_path,release,filler))
            for slot in range(0 if args.disk_required else geometry['maxdir']-used_entries):
                install(payload/'BTEMPTY.DAT',f'0:F{slot:07d}.DAT')
            fixtures.append({'drive':'D','full_directory':None if args.disk_required else geometry['maxdir'],
                             'allocated_blocks':blocks,'directory_blocks':directory_blocks})
            target=disks/'driveb.dsk'

    elif args.program=='ECOTEST':
        fixture=suite/'suite/runtime-payload/BTONE.DAT'
        if fixture.stat().st_size!=128:raise ValueError('BTONE must be exactly one record')
        install(fixture,'0:BTONE.DAT')
        fixtures.append({'name':'BTONE.DAT','sha256':sha(fixture),'bytes':128})
    if args.case and ((args.program=='ENTRYTST' and args.case not in ('0023','0024')) or (args.program!='ENTRYTST' and not(args.program=='ECOTEST' and args.case=='0513'))):raise ValueError('case not reviewed for this program')
    command=args.program+' '+('/'+args.case if args.case else ('/GROUP:REQUIRED' if args.file_required or args.disk_required else COMMANDS[args.program]))
    commands=[(b'B:\r',b'B0>_ ',30)] if data_suite else []
    prompt=b'B0>_ ' if data_suite and not args.disk_required else b'A0>_ '
    if args.disk_required:
        commands += [(command.encode()+b'\r',b'Enter its configured drive letter, or Q to quit (B-P or Q): ',30)]
    outgoing=b'D' if args.disk_required else command.encode()+b'\r'
    commands += [(outgoing,b'Summary:',120),(b'',prompt,30),(b'BYE /Y\r',b'System halted',10)]
    initial_disks={disk.name:sha(disk) for disk in sorted(disks.glob('*.dsk'))}
    trace=session(args.simulator.resolve(),disks,commands,work/'transcript.bin')
    if args.disk_required:
        exported=work/'BTFULL-after.DAT'
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disks/'drived.dsk'),'0:BTFULL.DAT',str(exported)],cwd=work,check=True)
        if exported.read_bytes()!=control_path.read_bytes():raise ValueError('allocation-failure campaign changed completed BTFULL data')
    text=trace.decode('ascii',errors='replace');rows={}
    for match in re.finditer(r'^\s*(\d{4})\s+([PFEOS?\-])\s+([A-Z?])\s+([^\r\n]*)',text,re.M):
        item,status,classification,observed=match.groups()
        if item in rows:raise ValueError('duplicate result row '+item)
        rows[item]={'status':status,'class':classification,'observed':observed.strip()}
    if not rows:raise ValueError('no classified result rows captured')
    counts={status:sum(row['status']==status for row in rows.values()) for status in sorted({r['status'] for r in rows.values()})}
    summary=re.search(r'Summary:[^\r\n]*',text)
    result={'baseline_revision':report['source']['revision'],'baseline_sha256':report['sha256'],'suite_revision':subprocess.check_output(['git','-C',str(suite),'rev-parse','HEAD'],text=True).strip(),'program_sha256':sha(program),'simulator_sha256':sha(args.simulator),'command':command,'initial_disks':initial_disks,'final_disks':{disk.name:sha(disk) for disk in sorted(disks.glob('*.dsk'))},'fixtures':fixtures,'rows':rows,'counts':counts,'printed_summary':summary.group() if summary else None,'scope':'selected returning group only; observations/exclusions/not-run are not passes','failed_or_error_rows':[k for k,v in rows.items() if v['status'] in ('F','E')]}
    if sha(original)!=report['sha256']:raise ValueError('reference image changed')
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'command':command,'counts':counts,'failed_or_error_rows':result['failed_or_error_rows'],'evidence':str(work)},indent=2))


if __name__=='__main__':main()
