#!/usr/bin/env python3
"""Compare disk/reader source lists with pinned DRI PIP."""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from test_pip_hex import record
from test_pip_reader_hex_media import launcher
from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, default=ROOT/'build/z80pack')
    parser.add_argument('--reference-only', action='store_true')
    parser.add_argument('--simulator', type=Path,
                        default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    args = parser.parse_args()
    report = ROOT/'build/test-results/pip-reader-lists'
    report.mkdir(parents=True, exist_ok=True)
    obj = b'OBJECT'.ljust(128, b'\0')
    payload = b'noise\r\n'+record(b'ABC')+b'\n:00000001FF\r\n\x1a'
    cases = ['PREFIX.COM,INP:[O]', 'PREFIX.COM,RDR:[O]',
             'PREFIX.TXT,INP:[H]', 'INP:[H],PREFIX.COM', 'PREFIX.COM,INP:[OSnoise\x1a]', 'RAW.TXT,INP:[O]', 'EMPTY.TXT,RDR:[O]']
    binaries = [('REF', ROOT/'third_party/dri-pip/PIP-1.5-reference.COM')]
    if not args.reference_only:
        binaries.insert(0, ('OUR', ROOT/'build/pip-development/PIP.COM'))
    with tempfile.TemporaryDirectory(prefix='pip-reader-list-',dir='/private/tmp') as tmp:
        work = Path(tmp)
        shutil.copytree(args.image_dir/'disks',work/'disks')
        shutil.copy2(args.image_dir/'diskdefs',work/'diskdefs')
        disk = work/'disks/drivea.dsk'
        output_disk = work/'disks/driveb.dsk'
        def install(source, target):
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(source),target],cwd=work,check=True)
        for name, data in [('PREFIX.COM', obj), ('PREFIX.TXT', b'prefix\x1aTAIL'), ('RAW.TXT',obj), ('EMPTY.TXT',b'')]:
            source = work/name
            source.write_bytes(data)
            install(source, '4:'+name)
        commands = [(b'A4:\r', b'A4>_ ',30)]
        for i, sources in enumerate(cases):
            for prefix, binary in binaries:
                name = prefix+str(i)
                program = work/(name+'.COM')
                program.write_bytes(launcher(binary, ('B:'+name+'.DAT='+sources).encode(), payload))
                install(program, '0:'+program.name)
                commands.append((b':'+name.encode()+b'\r', b'A4>_ ',30))
        session(args.simulator,work/'disks',commands,report/'transcript.txt')
        for i, sources in enumerate(cases):
            outputs = []
            for prefix, _ in binaries:
                name = prefix+str(i)+'.DAT'
                output = work/name
                subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(output_disk),'4:'+name,str(output)],cwd=work,check=True)
                outputs.append(output.read_bytes())
            if i < 2 or i in (4,5):
                assert outputs[-1] == obj, (sources, outputs[-1])
            if i == 6:assert outputs[-1] == b'', outputs[-1]
            if len(outputs) == 2:
                assert outputs[0] == outputs[1], (sources, outputs)
    print('PASS: disk/reader source lists and carried object EOF match pinned DRI PIP')


if __name__ == '__main__':
    main()
