#!/usr/bin/env python3
"""Observe selected CONSTEST output cases before supplying their confirmation.

This is an external byte-stream observer, not a blanket Yes responder. Cases
requiring screen rendering, keys, timing or separate devices need other oracles.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from test_z80pack_sysgen_install import session


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--diskdefs',type=Path,required=True)
    parser.add_argument('--suite',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    args=parser.parse_args()
    report=json.loads((args.baseline/'report.json').read_text())
    original=args.baseline/report['image']
    assert report['target']=='z80pack' and sha(original)==report['sha256']
    program=args.suite/'suite/build/CONSTEST.COM'
    hashes={line.split()[1]:line.split()[0] for line in (args.suite/'suite/build/SHA256SUMS.txt').read_text().splitlines() if line.strip()}
    assert sha(program)==hashes['CONSTEST.COM']
    args.output.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='constest-output-',dir=args.output.resolve()))
    disks=work/'disks';disks.mkdir();disk=disks/'drivea.dsk'
    shutil.copy2(original,disk);shutil.copy2(args.diskdefs,work/'diskdefs')
    subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(program),'0:CONSTEST.COM'],cwd=work,check=True)
    # Expectations are independent literal observations from reviewed case
    # recipes, not text inferred from the program's printed EXPECTED field.
    values={52:b'[A]',53:b'[$]',54:b'[F9ADDR]',55:b'[LEFT]',56:b'[X]',57:b'[]'}
    confirmation=b'Do OBSERVED and EXPECTED match? (Y/N; no Enter) '
    commands=[]
    for case,value in values.items():
        expected=b'OBSERVED: '+value+b'\r\nEXPECTED: '+value
        if case==53:expected+=b' (one dollar-sign character)'
        commands += [(f'CONSTEST /{case:04d}\r'.encode(),expected+b'\r\n'+confirmation,30),
                     (b'Y',f'{case:04d}  P  R'.encode(),30),(b'',b'A0>_ ',30)]
    expected=b'OBSERVED:\r\nA\r\nB\r\nEXPECTED:\r\nA\r\nB\r\n'+confirmation
    commands += [(b'CONSTEST /0058\r',expected,30),(b'Y',b'0058  P  R',30),
                 (b'',b'A0>_ ',30),(b'BYE\r',b'System halted',10)]
    # session sends each Y only after its exact independent observation matches.
    session(args.simulator.resolve(),disks,commands,work/'transcript.bin')
    assert sha(original)==report['sha256']
    result={'baseline_sha256':report['sha256'],'program_sha256':sha(program),
            'simulator_sha256':sha(args.simulator),'cases':list(range(52,59)),
            'pass':7,'oracle':'external literal byte-stream comparison before each confirmation',
            'scope':'cpmsim output only; no inference for rendering, timing, input or device separation'}
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'pass':7,'evidence':str(work)},indent=2))


if __name__=='__main__':main()
