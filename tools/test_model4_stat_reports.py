#!/usr/bin/env python3
"""Qualify Model 4 STAT free space, DPB reporting and user enumeration."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from add_cpm_file_to_dmk import extract_raw
from build_trs80_boot import (FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE,
                             DIRECTORY_ENTRIES, BLOCK_COUNT, FIRST_DATA_BLOCK)
from run_trs80_command import DEFAULT_EMULATOR
from test_disk_utilities import ROOT, medium, keys
from test_sysgen_install import screen
from trs80gp_launch import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--verify-existing', action='store_true',
                        help='Validate retained captures without launching the emulator')
    args = parser.parse_args()
    report = args.report.resolve()
    if not args.verify_existing:
        report.mkdir(parents=True, exist_ok=False)
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)
    stat = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    (report / 'STAT.COM').write_bytes(stat)
    image = medium((('STAT.COM', stat), ('U3.DAT', bytes(128), 3),
                    ('U15.DAT', bytes(128), 15)))
    raw = extract_raw(image)
    start = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
    entries = [raw[start + n * 32:start + (n + 1) * 32]
               for n in range(DIRECTORY_ENTRIES)]
    live = [entry for entry in entries if entry[0] <= 31]
    users = sorted({entry[0] for entry in live})
    assert users == [0, 3, 15], users
    blocks = {int.from_bytes(entry[offset:offset + 2], 'little')
              for entry in live for offset in range(16, 32, 2)} - {0}
    assert all(FIRST_DATA_BLOCK <= block < BLOCK_COUNT for block in blocks)
    free = (BLOCK_COUNT - FIRST_DATA_BLOCK - len(blocks)) * 2
    # Installed A: profile in src/bios/tables.mac: 80,4,15,0,389,127,C000,32,2.
    details = { '128 Byte Record Capacity': 6240, 'Kilobyte Drive Capacity': 780,
                '128 Byte Records/Track': 80, 'Allocation Blocks': 390,
                '32 Byte Directory Entries': 128, 'Checked Directory Entries': 128,
                'Records/Extent': 128, 'Records/Allocation Block': 16,
                'Reserved Tracks': 2, 'Kilobytes Remaining': free }
    steps = [('STAT', f'Space: {free}K', 'status'), ('STAT A:', f'On A: {free}K', 'space'),
             ('STAT DSK:', 'Kilobytes Remaining', 'details'),
             ('STAT A:DSK:', 'Kilobytes Remaining', 'details'),
             ('STAT USR:', 'Active Files:', 'users')]
    disk = report / 'system.dmk'
    if not args.verify_existing:
        disk.write_bytes(image)
    captures = []
    for number, (command, completion, _) in enumerate(steps):
        case = report / f'case-{number}'
        if not args.verify_existing:
            case.mkdir()
        invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo',
                      '-d0', str(disk), '-id', '3000']
        invocation += keys(command + '\r') + ['-itime', '0', '-iw', completion,
                                               '-iw', 'A0> ', '-id', '500', '-it', '-ix']
        if not args.verify_existing:
            (case / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
            run(invocation, cwd=case, check=True, timeout=60)
        else:
            assert json.loads((case / 'invocation.json').read_text()) == invocation
        captured = list(case.glob('trs80-text-*.bin'))
        assert len(captured) == 1, (command, captured)
        captures.append(captured[0])
    for capture, (command, _, kind) in zip(captures, steps):
        text = screen(capture)
        capture.with_suffix('.txt').write_text(text)
        assert 'A0>' + command in text, (command, text)
        current = text.rsplit('A0>' + command, 1)[1]
        if kind == 'status':
            assert re.findall(r'([A-P]): R/([WO]), Space: +(\d+)K', current) == [('A', 'W', str(free))], current
        elif kind == 'space':
            assert re.search(r'Bytes Remaining On A: +' + str(free) + r'K', current), current
        elif kind == 'details':
            actual = {label: int(value) for value, label in
                      re.findall(r'(\d+): ([A-Za-z0-9 /]+)', current)}
            assert actual == details, (actual, details, current)
            assert current.count('A: Drive Characteristics') == 1, current
        else:
            assert re.search(r'Active User : +0\s', current), current
            assert re.search(r'Active Files: +0 +3 +15\s', current), current
        assert re.search(r'A0>\s*$', text.rstrip()), (command, text)
    assert disk.read_bytes() == image, 'STAT reporting changed media'
    (report / 'evidence.json').write_text(json.dumps({
        'result': 'PASS', 'commands': [step[0] for step in steps],
        'free_kib': free, 'allocated_blocks': sorted(blocks), 'users': users,
        'expected_dpb_report': details, 'media_unchanged': True,
        'stat_sha256': hashlib.sha256(stat).hexdigest(),
        'boot_media_sha256': hashlib.sha256(image).hexdigest(),
        'emulator_sha256': hashlib.sha256(DEFAULT_EMULATOR.read_bytes()).hexdigest(),
    }, indent=2) + '\n')
    print('Model 4 STAT free space, exact DPB fields and user enumeration passed')


if __name__ == '__main__':
    main()
