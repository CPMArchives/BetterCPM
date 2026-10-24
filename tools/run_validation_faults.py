#!/usr/bin/env python3
"""Observe live BDOS Ignore/Abort using one-shot final-BIOS error providers.

This qualifies the OS response after final BIOS failure, not controller retries.
Each scenario boots a fresh private disk; ignored-I/O data is not assumed valid.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from build_ccp import assemble
from test_z80pack_sysgen_install import session

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--diskdefs',type=Path,required=True)
    p.add_argument('--suite',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    a=p.parse_args()
    report=json.loads((a.baseline/'report.json').read_text());original=a.baseline/report['image']
    assert report['target']=='z80pack' and sha(original)==report['sha256']
    a.output.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='operator-recovery-',dir=a.output.resolve()))
    source=ROOT/'tests/fixtures/conformance/faultmore.mac'
    program=work/'FAULTIO.COM'
    assemble(Path.home()/'bin/z80asm',source.read_text(),program,work/'faultio.lst',0x100)
    fixture=a.suite/'suite/runtime-payload/BTONE.DAT';assert fixture.stat().st_size==128
    results={}
    for scenario in ('suspended','ignore','abort'):
        run=work/scenario;disks=run/'disks';disks.mkdir(parents=True)
        image=disks/'drivea.dsk';shutil.copy2(original,image);shutil.copy2(a.diskdefs,run/'diskdefs')
        for f in (program,fixture):
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(f),'0:'+f.name],cwd=run,check=True)
        commands=[(b'FAULTIO\r',b'Healthy file read passed; inject final BIOS errors.',30),(b'',b'Bad Sector',30)]
        if scenario=='suspended':
            try:
                session(a.simulator.resolve(),disks,commands+[(b'',b'READ CALLER RESUMED',0.5)],run/'transcript.bin')
            except AssertionError as error:
                assert 'timeout waiting for' in str(error),str(error)
            else:raise AssertionError('failed READ resumed without an operator choice')
            trace=(run/'transcript.bin').read_bytes()
            assert b'Bad Sector' in trace and b'READ CALLER RESUMED' not in trace
        elif scenario=='ignore':
            commands += [(b'I',b'READ CALLER RESUMED after operator ignore.',30),
                         (b'',b'Bad Sector',30),
                         (b'I',b'FAULT PROVIDER COMPLETED BOTH CALLS',30),
                         (b'',b'A0>_ ',30),(b'BYE /Y\r',b'System halted',10)]
            trace=session(a.simulator.resolve(),disks,commands,run/'transcript.bin')
            assert b'WRITE CALLER RESUMED after operator ignore.' in trace
            assert b'SETUP OR PROVIDER COUNT FAILED' not in trace
        else:
            commands += [(b'\x03',b'A0>_ ',30),(b'VER\r',b'BetterCP/M 0.90',30),
                         (b'',b'A0>_ ',30),(b'BYE /Y\r',b'System halted',10)]
            trace=session(a.simulator.resolve(),disks,commands,run/'transcript.bin')
            assert b'READ CALLER RESUMED' not in trace
        results[scenario]={'status':'PASS','image_after_sha256':sha(image),'transcript_sha256':sha(run/'transcript.bin')}
    assert sha(original)==report['sha256']
    result={'baseline_sha256':report['sha256'],'provider_source_sha256':sha(source),
            'provider_binary_sha256':sha(program),'fixture_sha256':sha(fixture),
            'simulator_sha256':sha(a.simulator),'scenarios':results,
            'scope':'live final-BIOS read/write Ignore, pending caller, Control-C abandonment and CCP reconstruction; not controller retry or ignored-data guarantees'}
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'scenarios':3,'status':'PASS','evidence':str(work)},indent=2))


if __name__=='__main__':main()
