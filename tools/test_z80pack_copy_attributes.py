#!/usr/bin/env python3
"""Verify COPY/MOVE attribute preservation using the released BDOS in cpmsim."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from test_z80pack_attributes import directory
from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True,
                        help='Qualified attribute runtime containing ATTRPROB.COM')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--profile', choices=('cpx', 'transient'), default='cpx')
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    work = report / 'runtime'
    shutil.copytree(args.runtime, work)
    a, b = (work / 'disks' / f'drive{drive}.dsk' for drive in 'ab')
    def cpm(tool, *arguments):
        return subprocess.run([tool, '-T', 'raw', '-f', 'bettercpm-default',
                               *map(str, arguments)], cwd=work, check=True)
    for name in ('COPY.COM', 'MOVE.COM'):
        shutil.copy2(ROOT / 'build/utilities' / name, report / name)
        cpm('cpmrm', a, '0:' + name)
        cpm('cpmcp', a, ROOT / 'build/utilities' / name, '0:' + name)
    shutil.copy2(ROOT / 'build/cpx/RCP.CPX', report / 'RCP.CPX')
    cpm('cpmrm', a, '0:RCP.CPX')
    cpm('cpmcp', a, ROOT / 'build/cpx/RCP.CPX', '0:RCP.CPX')
    simulator = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    def run(command, label):
        commands = [(b'CPX UNLOAD RCP\r', b'A0>_ ', 15)]
        if args.profile == 'cpx':
            commands.append((b'CPX LOAD RCP\r', b'A0>_ ', 15))
        commands.append((command.encode() + b'\r', b'A0>_ ', 15))
        return session(simulator, work / 'disks', commands,
                       report / (label + '.txt'))
    def entry(name):
        raw = directory(b, work / 'diskdefs')
        matches = [raw[i:i+32] for i in range(0, len(raw), 32)
                   if raw[i] == 0 and bytes(x & 127 for x in raw[i+1:i+12]) == name]
        assert len(matches) <= 1, matches
        return matches[0] if matches else None
    observations = []
    for mask in range(8):
        assert b'ATTRIBUTE PASS' in run(f'ATTRPROB {mask}', f'set-{mask}')
        source = entry(b'ATTR    DAT')
        run(f'COPY B:ATTR.DAT B:C{mask}.DAT', f'copy-{mask}')
        copied = entry(f'C{mask:<7}DAT'.encode())
        assert copied is not None and copied[9:12] == source[9:12], (mask, copied, source)
        extracted = report / f'copy-{mask}.dat'
        cpm('cpmcp', b, f'0:C{mask}.DAT', extracted)
        assert extracted.read_bytes() == bytes(range(128))
        assert entry(b'ATTR    DAT') == source
        observations.append({'mask': mask, 'source': source.hex(), 'copy': copied.hex()})
    # A read-only source may be copied, but MOVE must not erase it.
    out = run('MOVE B:ATTR.DAT B:RO.MOV', 'move-read-only')
    assert b'COPY MADE; SOURCE NOT ERASED' in out
    assert entry(b'ATTR    DAT') is not None
    assert bytes(x & 128 for x in entry(b'RO      MOV')[9:12]) == bytes((128, 128, 128))
    # SYS and ARC survive a successful MOVE when R/O is clear.
    assert b'ATTRIBUTE PASS' in run('ATTRPROB 6', 'set-move')
    run('MOVE B:ATTR.DAT B:OK.MOV', 'move-success')
    assert entry(b'ATTR    DAT') is None
    assert entry(b'OK      MOV')[9:12] == bytes((ord('M'), ord('O') | 128, ord('V') | 128))
    (report / 'evidence.json').write_text(json.dumps({
        'result': 'PASS', 'profile': args.profile, 'observations': observations,
        'copy_sha256': hashlib.sha256((ROOT / 'build/utilities/COPY.COM').read_bytes()).hexdigest(),
        'move_sha256': hashlib.sha256((ROOT / 'build/utilities/MOVE.COM').read_bytes()).hexdigest(),
        'rcp_sha256': hashlib.sha256((ROOT / 'build/cpx/RCP.CPX').read_bytes()).hexdigest(),
        'simulator_sha256': hashlib.sha256(simulator.read_bytes()).hexdigest(),
    }, indent=2) + '\n')
    print('PASS: eight COPY attribute combinations, read-only MOVE rejection, successful MOVE preservation')


if __name__ == '__main__':
    main()
