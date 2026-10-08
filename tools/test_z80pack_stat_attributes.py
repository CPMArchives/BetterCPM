#!/usr/bin/env python3
"""Qualify STAT wildcard attributes against every raw directory extent."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from test_z80pack_attributes import directory
from test_z80pack_sysgen_install import session
from test_z80pack_submit_xsub import ROOT


def digest(data):
    return hashlib.sha256(data).hexdigest()


def directory_offsets(diskdefs):
    definition = re.search(r'diskdef bettercpm-default\n(.*?)\nend', diskdefs.read_text(), re.S)[1]
    def value(key):
        return int(re.search(r'\b' + key + r'\s+(\d+)', definition)[1])
    size, sectors, boot, entries = map(value, ['seclen', 'sectrk', 'boottrk', 'maxdir'])
    skew = list(map(int, re.search(r'skewtab\s+([0-9,]+)', definition)[1].split(',')))
    return [((boot + logical // sectors) * sectors + skew[logical % sectors]) * size + byte
            for logical in range((entries * 32 + size - 1) // size)
            for byte in range(size)][:entries * 32]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, default=ROOT / 'build/z80pack-iobyte-qualified')
    parser.add_argument('--simulator', type=Path, default=Path.home() / 'projects/git/z80pack/cpmsim/cpmsim')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)
    work = report / 'runtime'
    work.mkdir()
    shutil.copytree(args.image_dir / 'disks', work / 'disks')
    shutil.copy2(args.image_dir / 'diskdefs', work / 'diskdefs')
    a, b = (work / 'disks' / f'drive{drive}.dsk' for drive in 'ab')
    # Break copied image symlinks before changing any test media.
    for image in (a, b):
        data = image.read_bytes()
        image.unlink()
        image.write_bytes(data)
    b.write_bytes(bytes([0xe5]) * len(b.read_bytes()))
    def cpm(tool, *arguments):
        subprocess.run([tool, '-T', 'raw', '-f', 'bettercpm-default', *map(str, arguments)], cwd=work, check=True)
    cpm('cpmrm', a, '0:stat.com')
    stat = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    binary = report / 'STAT.COM'
    binary.write_bytes(stat)
    cpm('cpmcp', a, binary, '0:STAT.COM')
    fixtures = [('0:MATCHA.DAT', 161), ('0:MATCHB.DAT', 513),
                ('0:KEEP.DAT', 513), ('3:MATCHA.DAT', 161)]
    for name, records in fixtures:
        payload = report / name.replace(':', '-')
        payload.write_bytes(bytes((i % 251 for i in range(records * 128))))
        cpm('cpmcp', b, payload, name)
    offsets = directory_offsets(work / 'diskdefs')
    raw = directory(b, work / 'diskdefs')
    seeded = bytearray(b.read_bytes())
    extent_counts = {}
    masks = {b'MATCHA  DAT': 4, b'MATCHB  DAT': 3, b'KEEP    DAT': 7}
    for at in range(0, len(raw), 32):
        if raw[at] == 0xe5:
            continue
        name = bytes(value & 127 for value in raw[at + 1:at + 12])
        key = (raw[at], name)
        extent_counts[key] = extent_counts.get(key, 0) + 1
        mask = masks[name]
        for bit in range(3):
            seeded[offsets[at + 9 + bit]] = (raw[at + 9 + bit] & 127) | (128 if mask & (1 << bit) else 0)
    assert extent_counts == {(0, b'MATCHA  DAT'): 1, (0, b'MATCHB  DAT'): 3,
                             (0, b'KEEP    DAT'): 3, (3, b'MATCHA  DAT'): 1}, extent_counts
    b.write_bytes(seeded)
    (report / 'before.dsk').write_bytes(seeded)
    observations = []
    for step, (option, column, enabled, text) in enumerate([
        ('$R/O', 9, True, 'R/O'), ('$R/W', 9, False, 'R/W'),
        ('$SYS', 10, True, 'SYS'), ('$DIR', 10, False, 'DIR')]):
        before = b.read_bytes()
        raw = directory(b, work / 'diskdefs')
        expected = bytearray(before)
        changed = []
        for at in range(0, len(raw), 32):
            name = bytes(value & 127 for value in raw[at + 1:at + 12])
            if raw[at] == 0 and name in (b'MATCHA  DAT', b'MATCHB  DAT'):
                physical = offsets[at + column]
                expected[physical] = (expected[physical] | 128) if enabled else (expected[physical] & 127)
                changed.append(at)
        command = f'STAT B:MATCH*.DAT {option}'
        output = session(args.simulator.resolve(), work / 'disks',
                         [(command.encode() + b'\r', b'A0>_ ', 30)], report / f'{step}-transcript.txt')
        for name in ('MATCHA', 'MATCHB'):
            assert re.search(rf'{name} +\.DAT set to {re.escape(text)}', output.decode(errors='replace')), output
        assert b'failed' not in output.lower(), output
        after = b.read_bytes()
        assert after == expected, f'{option}: changed unrelated bytes or missed an extent'
        (report / f'{step}-after.dsk').write_bytes(after)
        observations.append({'command': command, 'extents_checked': len(changed),
                             'before_sha256': digest(before), 'after_sha256': digest(after)})

    # Test-only wrapper makes the selected disk R/O just before SETATTR.
    listing = (ROOT / 'build/utilities/stat.lst').read_text()
    entry = int(re.search(r'^([0-9a-f]{4})\s+.*?\bSETATTR:', listing, re.M | re.I)[1], 16)
    trampoline = (len(stat) + 0x100 + 4095) & ~255
    rostat = bytearray(stat)
    original = bytes(rostat[entry - 0x100:entry - 0x100 + 3])
    rostat[entry - 0x100:entry - 0x100 + 3] = bytes((0xc3, trampoline & 255, trampoline >> 8))
    tail = bytes.fromhex('0e 1c cd 05 00') + original + bytes((0xc3, (entry + 3) & 255, (entry + 3) >> 8))
    rostat += bytes(trampoline - 0x100 - len(rostat)) + tail
    (report / 'ROSTAT.COM').write_bytes(rostat)
    cpm('cpmcp', a, report / 'ROSTAT.COM', '0:ROSTAT.COM')
    before = b.read_bytes()
    output = session(args.simulator.resolve(), work / 'disks',
                     [(b'ROSTAT B:MATCH*.DAT $SYS\r', b'A0>_ ', 30)], report / 'readonly-transcript.txt')
    for name in ('MATCHA', 'MATCHB'):
        assert re.search(rf'{name} +\.DAT attribute update failed: disk is read-only', output.decode(errors='replace')), output
    assert b.read_bytes() == before, 'rejected wildcard update changed media'
    evidence = {'result': 'PASS', 'stat_sha256': digest(stat),
                'simulator_sha256': digest(args.simulator.read_bytes()),
                'observations': observations, 'readonly_rejection_unchanged': True,
                'nonmatching_file_and_user_unchanged': True,
                'payload_allocation_extent_and_arc_unchanged': True}
    (report / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print('STAT wildcard R/O/R/W/SYS/DIR, all matching extents, unrelated bytes and rejected-update atomicity passed')


if __name__ == '__main__':
    main()
