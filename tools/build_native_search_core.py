#!/usr/bin/env python3
"""Require native ZSM4/LINK parity for SEARCH's core; no release promotion."""
import argparse
import os
from pathlib import Path
import re
import shutil
import tempfile

from build_ccp import assemble
from build_native_trs80 import blank, run

ROOT = Path(__file__).resolve().parents[1]


def main():
    base = Path.home()/'projects/git/z80pack/cpmsim'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cpmsim', type=Path, default=base/'cpmsim')
    parser.add_argument('--system-disk', type=Path,
                        default=base/'disks/library/cpm22-62khd.dsk')
    parser.add_argument('--disk-template', type=Path,
                        default=base/'disks/library/cpm22-1.dsk')
    parser.add_argument('--tools', type=Path,
                        default=Path.home()/'projects/git/cpm-compatibility/suite/build-tools')
    args = parser.parse_args()
    os.environ['PATH'] = str(args.cpmsim.parent/'srctools') + os.pathsep + os.environ.get('PATH', '')
    out = ROOT/'build/search-core'
    out.mkdir(parents=True, exist_ok=True)
    body = ''.join((ROOT/'src/utilities/search'/part).read_text()
                   for part in ('matcher.inc', 'state.inc')) + '\n        END\n'
    # Materialize storage identically; linker hole fill is not executable state.
    body = re.sub(r'(?m)^(?:(\w+:)\s*)? +DS +([0-9]+) *$',
                  r'\1\n        REPT \2\n        DB 0\n        ENDM', body)
    expected = assemble(Path.home()/'bin/z80asm', '        ORG 0100H\n'+body,
                        out/'search-parity.bin', out/'search-parity.lst', 0x100)
    with tempfile.TemporaryDirectory(prefix='search-native-') as temporary:
        work = Path(temporary)
        disks = work/'disks'
        disks.mkdir()
        shutil.copy2(args.system_disk, disks/'drivea.dsk')
        for drive in 'bcd':
            blank(args.disk_template, disks/f'drive{drive}.dsk')
        source = work/'SCORE.MAC'
        native_source = ('        CSEG\n        .PHASE 0100H\n' +
                         body.replace('        END\n', '        .DEPHASE\n        END\n'))
        source.write_bytes(native_source.replace('\n', '\r\n').encode('ascii') + b'\x1a')
        run('cpmcp', '-f', 'ibm-3740', str(disks/'drivec.dsk'), str(source), '0:SCORE.MAC')
        for tool in ('ZSM4.COM', 'LINK.COM'):
            run('cpmcp', '-f', 'ibm-3740', str(disks/'drived.dsk'),
                str(args.tools/tool), '0:'+tool)
        commands = f'''set timeout 60
spawn {args.cpmsim} -z -d {disks}
expect "A>"
send -- "B:\\r"
expect "B>"
send -- "D:ZSM4 SCORE=C:SCORE\\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK SCORE\\[A\\]\\r"
expect "CODE SIZE"
expect "B>"
send "\\034"
expect eof
'''
        result = run('expect', '-c', commands, check=False)
        log = result.stdout + result.stderr
        (out/'NATIVE-SEARCH-CORE.LOG').write_text(log)
        if result.returncode or not re.search(r'Errors: +0\b', log) or 'CODE SIZE' not in log:
            raise SystemExit('Native SEARCH core build failed:\n'+log)
        target = work/'SCORE.COM'
        run('cpmcp', '-f', 'ibm-3740', str(disks/'driveb.dsk'), '0:SCORE.COM', str(target))
        native = target.read_bytes()
        (out/'search-native.COM').write_bytes(native)
        if native[:len(expected)] != expected:
            raise SystemExit('Native/cross SEARCH core mismatch')
    print(f'SEARCH core: {len(expected)} native byte-identical bytes')


if __name__ == '__main__':
    main()
