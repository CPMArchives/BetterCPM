#!/usr/bin/env python3
"""Freeze initial stock DRI ED file-state behavior on private BetterCP/M media."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]
REFERENCE=ROOT/'third_party/dri-ed/ED-CPM22-reference.COM'
ORACLE_SHA='adeeb92c897bd6a07579f06d163bd6ded549842203a5459c88a93d26c65fe85f'
FIXTURE=ROOT/'tools/fixtures/ed-initial-oracle.json'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image',type=Path,default=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk')
    p.add_argument('--diskdefs',type=Path,required=True)
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    p.add_argument('--stock-cpm',action='store_true',help='Use stock CP/M 2.2 instead of BetterCP/M')
    p.add_argument('--record',action='store_true',help='Explicitly record the oracle fixture after review')
    args=p.parse_args()
    assert hashlib.sha256(REFERENCE.read_bytes()).hexdigest()==ORACLE_SHA
    if args.stock_cpm:
        args.image=Path.home()/'projects/git/z80pack/cpmsim/disks/library/cpm22-1.dsk'
        assert hashlib.sha256(args.image.read_bytes()).hexdigest()=='86ac7cb1bdd6bac05fe6299b50f94cb26a047022ce00135fbecf7bbc5d3303d2'
    fixture=FIXTURE.with_name('ed-initial-oracle-cpm22.json') if args.stock_cpm else FIXTURE
    fmt='ibm-3740' if args.stock_cpm else 'bettercpm-default'
    parent=ROOT/'build/ed-development/oracle';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));results={}
    names=['TEST.TXT','TEST.BAK','TEST.$$$']
    cases=['new-E','new-Q','existing-E','existing-Q','split-E','collision']
    for case in cases:
        here=work/case;here.mkdir();disks=here/'disks';disks.mkdir()
        if not args.stock_cpm:shutil.copy2(args.diskdefs,here/'diskdefs')
        a=disks/'drivea.dsk';b=disks/'driveb.dsk'
        shutil.copy2(args.image,a);shutil.copy2(args.image,b)
        def tool(*cmd):return subprocess.run(list(cmd),cwd=here,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        tool('mkfs.cpm','-f',fmt,str(b))
        def put(disk,name,data):
            path=here/name;path.write_bytes(data)
            tool('cpmcp','-T','raw','-f',fmt,str(disk),str(path),'0:'+name)
        put(a,'EDREF.COM',REFERENCE.read_bytes())
        if not case.startswith('new'):
            put(a,'TEST.TXT',b'Original source\r\n\x1a');put(a,'TEST.BAK',b'Old backup\r\n\x1a')
        if case=='collision':put(b,'TEST.TXT',b'Destination\r\n\x1a')
        tail=b' B:' if case in ('split-E','collision') else b''
        prompt=b'B0>_ ' if case in ('split-E','collision') else b'A0>_ '
        if args.stock_cpm:
            prompt=b'B>' if case=='split-E' else b'A>'
        commands=[(b'EDREF TEST.TXT'+tail+b'\r',prompt if case=='collision' else b'*',15)]
        if case!='collision':
            if case=='new-E':commands.append((b'iHello world\x1a\r',b'*',10))
            if case.endswith('-Q'):
                commands.extend([(b'Q\r',b'(Y/N)?',10),(b'Y',prompt,10)])
            else:commands.append((b'E\r',prompt,10))
        commands.append((b'A:BYE\r',b'System halted',10))
        trace=session(args.simulator,disks,commands,here/'transcript.bin',initial_prompt=b'A>' if args.stock_cpm else b'A0>_ ')
        if case=='collision':assert b'FILE EXISTS, ERASE IT' in trace
        if case.startswith('new'):assert b'NEW FILE' in trace
        snapshots={}
        for letter,disk in [('A',a),('B',b)]:
            entries=tool('cpmls','-T','raw','-f',fmt,str(disk)).stdout.decode().upper().split()
            for name in names:
                key=letter+':'+name
                if name not in entries:snapshots[key]=None;continue
                path=here/(letter+'-'+name.replace('$','D'))
                tool('cpmcp','-T','raw','-f',fmt,str(disk),'0:'+name,str(path))
                data=path.read_bytes()
                snapshots[key]={'exported_bytes':len(data),'text_hex':data.rstrip(b'\x1a').hex()}
        results[case]={'exit_du':prompt.decode().split('>')[0]+('0' if args.stock_cpm else ''),'files':snapshots}
    report={'oracle_sha256':ORACLE_SHA,'cases':results}
    (work/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    if args.record:
        fixture.parent.mkdir(parents=True,exist_ok=True)
        fixture.write_text(json.dumps(report,indent=2)+'\n')
    else:assert report==json.loads(fixture.read_text()),work/'results.json'
    print(f'PASS: stock ED new/existing E/Q, backup/work states, split output and collision; {work}')


if __name__=='__main__':main()
