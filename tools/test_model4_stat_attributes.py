#!/usr/bin/env python3
"""Qualify Model 4 STAT wildcard attributes against complete logical media."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from add_cpm_file_to_dmk import extract_raw
from build_trs80_boot import FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE, DIRECTORY_ENTRIES
from run_trs80_command import DEFAULT_EMULATOR
from test_disk_utilities import ROOT, medium, keys
from test_sysgen_install import screen
from trs80gp_launch import run


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)
    stat = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    (report / 'STAT.COM').write_bytes(stat)
    listing = (ROOT / 'build/utilities/stat.lst').read_text()
    entry = int(re.search(r'^([0-9a-f]{4})\s+.*?\bSETATTR:', listing, re.M | re.I)[1], 16)
    trampoline = (len(stat) + 0x100 + 4095) & ~255
    rostat = bytearray(stat)
    original = bytes(rostat[entry - 0x100:entry - 0x100 + 3])
    rostat[entry - 0x100:entry - 0x100 + 3] = bytes((0xc3, trampoline & 255, trampoline >> 8))
    rostat += bytes(trampoline - 0x100 - len(rostat)) + bytes.fromhex('0e 1c cd 05 00') + original + bytes((0xc3, (entry + 3) & 255, (entry + 3) >> 8))
    (report / 'ROSTAT.COM').write_bytes(rostat)
    image = medium((('STAT.COM', stat), ('ROSTAT.COM', bytes(rostat)),
                    ('MATCHA.DAT', bytes(161 * 128), 0, 4),
                    ('MATCHB.DAT', bytes(513 * 128), 0, 3),
                    ('KEEP.DAT', bytes(513 * 128), 0, 7),
                    ('MATCHA.DAT', bytes(161 * 128), 3, 7)))
    disk = report / 'system.dmk'
    disk.write_bytes(image)
    (report / 'before.dmk').write_bytes(image)
    start = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
    observations = []
    operations = [('$R/O', 9, True, 'R/O'), ('$R/W', 9, False, 'R/W'),
                  ('$SYS', 10, True, 'SYS'), ('$DIR', 10, False, 'DIR'),
                  ('$SYS', None, None, None)]
    for index, (option, column, enabled, result) in enumerate(operations):
        work = report / f'step-{index}'
        work.mkdir()
        before_dmk = disk.read_bytes()
        before = extract_raw(before_dmk)
        expected = bytearray(before)
        selected = []
        for at in range(start, start + DIRECTORY_ENTRIES * 32, 32):
            name = bytes(value & 127 for value in before[at + 1:at + 12])
            if before[at] == 0 and name in (b'MATCHA  DAT', b'MATCHB  DAT'):
                selected.append(at)
                if column is not None:
                    expected[at + column] = (expected[at + column] | 128) if enabled else (expected[at + column] & 127)
        assert len(selected) == 7, len(selected)
        command = f'{"ROSTAT" if column is None else "STAT"} MATCH*.DAT {option}'
        completion = 'disk is read-only' if column is None else f'set to {result}'
        invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-d0', str(disk), '-id', '3000']
        invocation += keys(command + '\r') + ['-itime', '0', '-iw', completion,
                                              '-iw', 'A0> ', '-id', '500', '-it', '-ix']
        (work / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
        run(invocation, cwd=work, check=True, timeout=60)
        captures = list(work.glob('trs80-text-*.bin'))
        assert len(captures) == 1
        text = screen(captures[0])
        captures[0].with_suffix('.txt').write_text(text)
        assert 'A0>' + command in text and re.search(r'A0>\s*$', text.rstrip()), text
        current = text.rsplit('A0>' + command, 1)[1]
        for name in ('MATCHA', 'MATCHB'):
            suffix = 'attribute update failed: disk is read-only' if column is None else f'set to {result}'
            assert re.search(rf'{name} +\.DAT {suffix}', current), current
        after_dmk = disk.read_bytes()
        after = extract_raw(after_dmk)
        assert after == expected, f'{option}: unrelated bytes changed or a selected extent was missed'
        if column is None:
            assert after_dmk == before_dmk, 'rejected update changed physical media'
        (work / 'after.dmk').write_bytes(after_dmk)
        observations.append({'command': command, 'extents_checked': len(selected),
                             'before_raw_sha256': digest(before), 'after_raw_sha256': digest(after)})
    (report / 'evidence.json').write_text(json.dumps({
        'result': 'PASS', 'stat_sha256': digest(stat),
        'emulator_sha256': digest(DEFAULT_EMULATOR.read_bytes()), 'observations': observations,
        'unrelated_attributes_payload_allocation_and_users_preserved': True,
        'readonly_rejection_unchanged': True,
    }, indent=2) + '\n')
    print('Model 4 STAT wildcard attributes, all seven extents, unrelated media and rejection preservation passed')


if __name__ == '__main__':
    main()
