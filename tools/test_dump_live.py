#!/usr/bin/env python3
"""Run DUMP on disposable copies of a hash-identified BetterCP/M cpmsim image."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from test_z80pack_sysgen_install import session
from build_dump import version_text
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    a=p.parse_args();report=json.loads((a.baseline/'report.json').read_text());original=a.baseline/report['image']
    assert sha(original)==report['sha256']
    output=ROOT/'build/dump-development';output.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='live-',dir=output));disks=work/'disks';disks.mkdir()
    image=disks/'drivea.dsk';shutil.copy2(original,image);shutil.copy2(a.baseline/'diskdefs',work/'diskdefs')
    def run(*args):return subprocess.run(args,cwd=work,check=True,capture_output=True)
    payload=bytes(range(256));(work/'TEST.BIN').write_bytes(payload);(work/'EMPTY.BIN').write_bytes(b'')
    for source,target in [(ROOT/'build/utilities/DUMP.COM','0:DUMP.COM'),(work/'TEST.BIN','0:TEST.BIN'),(work/'EMPTY.BIN','0:EMPTY.BIN'),(work/'TEST.BIN','3:TEST.BIN')]:
        run('cpmcp','-f','bettercpm-default',str(image),str(source),target)
    commands=[(b'DUMP /VER\r',b'A0>_ ',15),(b'DUMP TEST.BIN\r',b'A0>_ ',20),(b'DUMP EMPTY.BIN\r',b'A0>_ ',15),(b'DUMP MISSING.BIN\r',b'A0>_ ',15),(b'A3:\r',b'A3>_ ',15)]
    commands.append((b'A0:DUMP A:TEST.BIN\r',b'A3>_ ',20))
    raw=session(a.simulator,disks,commands,transcript_path=work/'transcript.bin')
    expected=b''.join(b'\r\n'+f'{i:04X}'.encode()+b''.join(f' {b:02X}'.encode() for b in payload[i:i+16]) for i in range(0,256,16))+b'\r\n'
    assert raw.count(expected)==2,'normal and cross-user invocation must dump exact records'
    assert version_text().encode() in raw
    assert b'NO INPUT FILE PRESENT ON DISK\r\n' in raw
    for user in [0,3]:
        target=work/f'extracted-{user}.bin';run('cpmcp','-f','bettercpm-default',str(image),f'{user}:TEST.BIN',str(target));assert target.read_bytes()==payload
    run('fsck.cpm','-f','bettercpm-default','-n',str(image))
    assert sha(original)==report['sha256']
    result={'status':'PASS','baseline_sha256':sha(original),'program_sha256':sha(ROOT/'build/utilities/DUMP.COM'),'transcript_sha256':sha(work/'transcript.bin'),'scope':'Live cpmsim on accepted V052 BetterCP/M image: version, exact 256-byte output, empty/missing input, A0 program invoked from A3 with caller user preserved; source data and baseline unchanged; filesystem check.'}
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(work)


if __name__=='__main__':main()
