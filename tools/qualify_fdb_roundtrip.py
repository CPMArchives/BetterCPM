#!/usr/bin/env python3
"""Qualify FDB.COM using freshly built system tracks and disposable media.

First run build_complete_system.py and (for cpmsim) build_z80pack_image.py
--system-tracks-only in an isolated build tree at the desired source revision.
This tool neither modifies that tree nor writes release/package destinations.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil
import subprocess
from build_fdb import ROOT, build
from build_fdf_catalog import catalogue_payload
from fdfdecomp import decompile
from fdf_v1 import parse, serialize
from build_distribution import construct, geometry
from test_z80pack_sysgen_install import session
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build as make_dmk
from run_trs80_command import DEFAULT_EMULATOR, key_args
from trs80gp_launch import run
from test_sysgen_install import screen


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',choices=('z80pack','trs80gp'),required=True)
    parser.add_argument('--build-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    parser.add_argument('--emulator',type=Path,default=DEFAULT_EMULATOR)
    args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True)
    root=args.build_root.resolve()
    image=build(destination=out)
    stock=catalogue_payload()
    # Keep the qualification filesystem small; all system tracks are copied
    # from the supplied freshly assembled platform build.
    names=[('FDB.COM',image),('DISK.FDB',stock),('HOST.FDF',decompile(stock).encode()),
           ('RCP.CPX',(root/'build/cpx/RCP.CPX').read_bytes())]
    if args.target=='z80pack':names.append(('BYE.COM',(root/'build/z80pack-tools/BYE.COM').read_bytes()))
    files=[({'name':name,'user':0},data) for name,data in names]
    raw=construct(args.target,root,out,files,geometry(args.target,root),'')
    commands=['FDB DISK.FDB ROUND.FDF','FDB ROUND.FDF ROUND.FDB','FDB HOST.FDF HOST.FDB']
    captures_text = ''
    if args.target=='z80pack':
        disks=out/'disks';disks.mkdir();disk=disks/'drivea.dsk';shutil.copy2(raw,disk)
        trace=session(args.simulator.resolve(),disks,
                      [(command.encode()+b'\r',b'A0>_ ',40) for command in commands]+
                      [(b'BYE /Y\r',b'System halted',10)],out/'transcript.bin')
        assert trace.count(b'FDB: complete.')==3
        captures_text = trace.decode("ascii", errors="replace")
        after=disk
        emulator=args.simulator
    else:
        disk=out/'test.dmk';disk.write_bytes(make_dmk(raw.read_bytes()))
        # Cold boot each command so the completion oracle cannot see a stale
        # message from the preceding invocation.
        for index,command in enumerate(commands):
            here=out/f'command-{index}';here.mkdir()
            invocation=[str(args.emulator),'-m4','-batch','-turbo','-d0',str(disk),'-itime','0','-iw','A0> ','-id','32']
            invocation+=key_args(command+'\r')+['-itime','0','-iw','FDB: complete.',
                                                '-iw','A0> ','-id','32','-it','-ix']
            (here/'invocation.json').write_text(json.dumps(invocation,indent=2)+'\n')
            run(invocation,cwd=here,check=True,timeout=180)
            captures=list(here.glob('trs80-text-*.bin'));assert len(captures)==1
            text=screen(captures[0]);captures[0].with_suffix('.txt').write_text(text)
            captures_text += text + '\n'
            assert 'FDB: complete.' in text and text.rstrip().endswith('A0>'),text
        after=out/'after.raw';after.write_bytes(extract_raw(disk.read_bytes()))
        emulator=args.emulator
    results={}
    for name in ('DISK.FDB','ROUND.FDF','ROUND.FDB','HOST.FDB'):
        path=out/name
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(after),'0:'+name,str(path)],cwd=out,check=True)
        results[name]={'bytes':path.stat().st_size,'sha256':sha(path.read_bytes())}
    assert (out/'DISK.FDB').read_bytes()==stock
    assert (out/'ROUND.FDB').read_bytes()==stock
    assert (out/'HOST.FDB').read_bytes()==stock
    text=(out/'ROUND.FDF').read_bytes().split(b'\x1a')[0].decode()
    assert serialize(parse(text))==stock
    report={'target':args.target,'result':'PASS','entries':108,'files':results,
            'fdb_com_bytes':len(image),'fdb_com_sha256':sha(image),
            'emulator_sha256':sha(emulator.read_bytes()),'build_root':str(root),
            'tpa_address_span_bytes':0xc800-0x100,'standard_tpa_bytes':53*1024,
            'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
    free = [int(n, 16) for n in re.findall(r'FDB stack free ([0-9A-F]{4})h of 0200h', captures_text)]
    assert len(free) == len(commands) and all(0 < n < 512 for n in free), free
    report['stack_free_bytes_by_command'] = free
    (out/'evidence.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {args.target}: native stock round trip and both host cross-checks')

if __name__=='__main__':
    main()
