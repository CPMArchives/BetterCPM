#!/usr/bin/env python3
"""Require native ZSM4/LINK parity for isolated memory and routing candidates.

Reads audit artifacts, stages private emulator disks and never publishes a
production binary. Run both memory and IOBYTE audit builders first.
"""
import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path
from build_native_trs80 import blank, run

ROOT = Path(__file__).resolve().parents[1]


def expand(path):
    text = path.read_text(encoding='ascii')
    return re.sub(r'^\s*INCLUDE\s+(\S+)\s*$',
                  lambda match: expand(path.parent / match[1]), text, flags=re.M | re.I)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cpmsim', type=Path, default=Path('/Users/nathanael/projects/git/z80pack/cpmsim/cpmsim'))
    parser.add_argument('--system-disk', type=Path, default=Path('/Users/nathanael/projects/git/z80pack/cpmsim/disks/library/cpm22-62khd.dsk'))
    parser.add_argument('--disk-template', type=Path, default=Path('/Users/nathanael/projects/git/cpm-compatibility/suite/disk-images/z80pack/ibm-3740/drivea.dsk'))
    parser.add_argument('--tools', type=Path, default=Path('/Users/nathanael/projects/git/cpm-compatibility/suite/build-tools'))
    args = parser.parse_args()
    audit = ROOT / 'build/audit/monitor-efficiency'
    rows = json.loads((audit / 'measurements.json').read_text())
    candidates = {row['component']: Path(row['directory']) for row in rows}
    candidates['bios'] = ROOT / 'build/audit/iobyte/trs80m4/combined'
    results = []
    for component, folder in candidates.items():
        with tempfile.TemporaryDirectory(prefix='bcpm-native-audit-') as temporary:
            work = Path(temporary)
            disks = work / 'disks'
            disks.mkdir()
            shutil.copy2(args.system_disk, disks / 'drivea.dsk')
            for drive in 'bcd':
                blank(args.disk_template, disks / f'drive{drive}.dsk')
            source = expand(folder / f'{component}.mac')
            # Link relocatable code at 0100h while retaining its resident logical
            # addresses through PHASE, as the production native builders do.
            source, count = re.subn(r'        ASEG\n        ORG\s+([^\n]+)',
                                   r'        CSEG\n        .PHASE  \1', source, count=1)
            assert count == 1, component
            source = re.sub(r'^\s*END\s*$', '        .DEPHASE\n        END', source, count=1, flags=re.M)
            unit = work / 'UNIT.MAC'
            unit.write_bytes((source.rstrip() + '\n').replace('\n', '\r\n').encode('ascii') + b'\x1a')
            run('cpmcp', '-f', 'ibm-3740', str(disks / 'drivec.dsk'), str(unit), '0:UNIT.MAC')
            for tool in ('ZSM4.COM', 'LINK.COM'):
                run('cpmcp', '-f', 'ibm-3740', str(disks / 'drived.dsk'), str(args.tools / tool), f'0:{tool}')
            commands = rf'''set timeout 15
spawn {args.cpmsim} -z -d {disks}
send -- "\r"
expect "A>"
send -- "B:\r"
expect "B>"
send -- "D:ZSM4 B:UNIT=C:UNIT\r"
expect -re {{Errors: +[0-9]+}}
expect "B>"
send -- "D:LINK UNIT\[A\]\r"
expect "CODE SIZE"
expect "B>"
send "\034"
expect eof
'''
            result = run('expect', '-c', commands, check=False)
            transcript = result.stdout + result.stderr
            (folder / 'native-build.log').write_text(transcript)
            if result.returncode or not re.search(r'Errors: +0', transcript) or 'CODE SIZE' not in transcript:
                raise SystemExit(f'{component} native build failed\n{transcript}')
            linked = work / 'UNIT.COM'
            run('cpmcp', '-f', 'ibm-3740', str(disks / 'driveb.dsk'), '0:UNIT.COM', str(linked))
            cross = (folder / f'{component}.bin').read_bytes()
            native = linked.read_bytes()[:len(cross)]
            if native != cross:
                raise SystemExit(f'{component}: native/cross mismatch')
            (folder / f'{component}-native.bin').write_bytes(native)
            results.append(dict(component=component, bytes=len(native), parity=True))
            print(f'PASS {component}: {len(native)} native/cross identical bytes', flush=True)
    (audit / 'native-parity.json').write_text(json.dumps(results, indent=2)+'\n')


if __name__ == '__main__':
    main()
