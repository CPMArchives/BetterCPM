#!/usr/bin/env python3
"""Verify native DUP copy/check preserves attributed raw media."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from test_z80pack_attributes import directory
from test_z80pack_sysgen_install import session


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True,
                        help='SYSGEN attribute fixture with all eight combinations on B:')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    work = report / 'runtime'
    shutil.copytree(args.runtime, work)
    a, b, c = (work / 'disks' / f'drive{d}.dsk' for d in 'abc')
    system, source = a.read_bytes(), b.read_bytes()
    raw = directory(b, work / 'diskdefs')
    for mask in range(8):
        name = f'ATTR{mask}   DAT'.encode()
        entry = next(raw[i:i+32] for i in range(0,len(raw),32)
                     if raw[i] == 0 and bytes(x & 127 for x in raw[i+1:i+12]) == name)
        assert bytes(x & 128 for x in entry[9:12]) == bytes(128 if mask & (1 << n) else 0 for n in range(3))
    c.write_bytes(bytes([0xA5]) * len(source))
    (report / 'destination-before.dsk').write_bytes(c.read_bytes())
    simulator = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    out = session(simulator, work / 'disks', [
        (b'DUP\r', b'Your choice:', 15),
        (b'B', b'Source logical drive', 15),
        (b'B', b'Destination logical drive', 15),
        (b'C', b'Destination contents will be erased. [Y/N]', 15),
        (b'Y', b'Copy complete; destination verified.', 60),
        (b'\r', b'Your choice:', 15),
        (b'C', b'Choose logical drive', 15),
        (b'C', b'Unreadable sectors: 00000', 60),
        (b'\r', b'Your choice:', 15),
        (b'\x03', b'A0>_ ', 15),
    ], report / 'transcript.txt')
    assert b'Copy complete; destination verified.' in out
    assert a.read_bytes() == system and b.read_bytes() == source
    assert c.read_bytes() == source, 'destination differs from source payload or metadata'
    assert directory(c, work / 'diskdefs') == raw
    # Run CHECK alone and prove it performs no media mutations on any disk.
    before = [disk.read_bytes() for disk in (a,b,c)]
    session(simulator, work / 'disks', [
        (b'DUP\r', b'Your choice:', 15),
        (b'C', b'Choose logical drive', 15),
        (b'C', b'Unreadable sectors: 00000', 60),
        (b'\r', b'Your choice:', 15),
        (b'\x03', b'A0>_ ', 15),
    ], report / 'check-only.txt')
    assert [disk.read_bytes() for disk in (a,b,c)] == before, 'CHECK changed media'
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS',
        'attributes': list(range(8)), 'image_bytes': len(source),
        'source_and_copy_sha256': hashlib.sha256(source).hexdigest(),
        'system_sha256': hashlib.sha256(system).hexdigest(),
        'simulator_sha256': hashlib.sha256(simulator.read_bytes()).hexdigest()},indent=2)+'\n')
    print('PASS: DUP complete raw copy preserves all attributes and payload; CHECK changes no media')


if __name__ == '__main__':
    main()
