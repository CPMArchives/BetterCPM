#!/usr/bin/env python3
"""Install from a bootable source and preserve every attribute combination."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from build_ccp import assemble
from test_z80pack_attributes import PROBE, directory
from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    fixture = report / 'fixture'
    shutil.copytree(args.runtime, fixture)
    simulator = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    def cpm(work, tool, *arguments):
        subprocess.run([tool, '-T', 'raw', '-f', 'bettercpm-default',
                        *map(str, arguments)], cwd=work, check=True)
    # The same digit selects both the attribute mask and its fixture filename.
    source = PROBE.replace("        SUB '0'\n", "        SUB '0'\n        PUSH AF\n        ADD A,'0'\n        LD (FCB+5),A\n        POP AF\n").replace("'ATTR    DAT'", "'ATTR0   DAT'")
    (report / 'attrset.mac').write_text(source)
    binary = report / 'ATTRSET.COM'
    assemble(Path.home() / 'bin/z80asm', source, binary, report / 'attrset.lst', 0x100)
    a, b = (fixture / 'disks' / f'drive{d}.dsk' for d in 'ab')
    cpm(fixture, 'cpmrm', a, '0:ATTRPROB.COM')
    cpm(fixture, 'cpmcp', a, binary, '0:ATTRSET.COM')
    payload = report / 'payload.dat'
    payload.write_bytes(bytes(range(128)))
    for mask in range(8):
        cpm(fixture, 'cpmcp', b, payload, f'0:ATTR{mask}.DAT')
        out = session(simulator, fixture / 'disks',
                      [(f'ATTRSET {mask}\r'.encode(), b'A0>_ ', 15)],
                      report / f'set-{mask}.txt')
        assert b'ATTRIBUTE PASS' in out and b'ATTRIBUTE FAIL' not in out
    raw_before = directory(b, fixture / 'diskdefs')
    for mask in range(8):
        name = f'ATTR{mask}   DAT'.encode()
        entry = next(raw_before[i:i+32] for i in range(0,len(raw_before),32)
                     if raw_before[i] == 0 and bytes(x & 127 for x in raw_before[i+1:i+12]) == name)
        assert bytes(x & 128 for x in entry[9:12]) == bytes(128 if mask & (1 << n) else 0 for n in range(3))
    manifest = json.loads(args.manifest.read_text())
    reserved = manifest['reserved_records'] * 128
    observations = []
    for label, command in [('disk', 'SYSGEN A: B:')]:
        work = report / label
        shutil.copytree(fixture, work)
        a, b = (work / 'disks' / f'drive{d}.dsk' for d in 'ab')
        before = b.read_bytes()
        (work / 'before.dsk').write_bytes(before)
        out = session(simulator, work / 'disks',
                      [(command.encode() + b'\r', b'Proceed (Y/N)?', 30),
                       (b'Y', b'A0>_ ', 60)], work / 'install.txt')
        assert b'System installed and verified.' in out, out
        after = b.read_bytes()
        assert after[:reserved] != before[:reserved], 'system area did not change'
        assert after[reserved:] == before[reserved:], 'filesystem bytes changed'
        assert directory(b, work / 'diskdefs') == raw_before
        for mask in range(8):
            recovered = work / f'attr{mask}.dat'
            cpm(work, 'cpmcp', b, f'0:ATTR{mask}.DAT', recovered)
            assert recovered.read_bytes() == payload.read_bytes()
        (work / 'installed.dsk').write_bytes(after)
        a.unlink()
        a.write_bytes(after)
        session(simulator, work / 'disks', [], work / 'cold-boot.txt')
        observations.append({'path': label, 'command': command,
            'before_sha256': hashlib.sha256(before).hexdigest(),
            'installed_sha256': hashlib.sha256(after).hexdigest(),
            'filesystem_sha256': hashlib.sha256(after[reserved:]).hexdigest()})
    shutil.copy2(args.manifest, report / 'manifest.json')
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS',
        'reserved_bytes': reserved, 'cases': observations,
        'directory_sha256': hashlib.sha256(raw_before).hexdigest(),
        'simulator_sha256': hashlib.sha256(simulator.read_bytes()).hexdigest()}, indent=2)+'\n')
    print('PASS: disk-source SYSGEN preserves all eight attribute combinations and entire filesystem; installed disk cold boots')


if __name__ == '__main__':
    main()
