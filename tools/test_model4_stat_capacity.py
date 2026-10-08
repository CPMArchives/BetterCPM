#!/usr/bin/env python3
"""Qualify a full Model 4 directory and native STAT workspace failure."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw
from test_disk_utilities import ROOT, medium, keys
from test_sysgen_install import screen
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve(); report.mkdir(parents=True, exist_ok=False)
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)
    stat = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    listing = (ROOT / 'build/utilities/stat.lst').read_text()
    def address(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':', listing, re.M | re.I)[1], 16)
    constrained = bytearray(stat)
    entry = address('SUMROOM') - 256
    # Return zero available slots without changing BDOS memory boundaries.
    cap = address('SUMCAP')
    constrained[entry:entry + 7] = bytes((0x21, 0, 0, 0x22, cap & 255, cap >> 8, 0xc9))
    (report / 'STAT.COM').write_bytes(stat)
    (report / 'LIMSTAT.COM').write_bytes(constrained)
    base = [('STAT.COM', stat), ('LIMSTAT.COM', bytes(constrained))]
    def entries(image):
        raw = extract_raw(image)
        directory = raw[40 * 512:40 * 512 + 128 * 32]
        return [directory[n:n + 32] for n in range(0, len(directory), 32) if directory[n] <= 31]
    remaining = 128 - len(entries(medium(tuple(base))))
    fixtures = [(f'F{number:03}.DAT', bytes(128)) for number in reversed(range(remaining))]
    image = medium(tuple(base + fixtures))
    assert len(entries(image)) == 128
    disk = report / 'system.dmk'; disk.write_bytes(image)
    cases = [('STAT F*.DAT', f'F{remaining - 1:03}', 'full'),
             ('LIMSTAT F*.DAT $SYS', 'Insufficient transient memory for matching files', 'limited')]
    for number, (command, completion, kind) in enumerate(cases):
        work = report / f'case-{number}'; work.mkdir()
        invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-d0', str(disk), '-id', '3000']
        invocation += keys(command + '\r') + ['-itime', '0', '-iw', completion, '-iw', 'A0> ', '-id', '500', '-it', '-ix']
        (work / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
        run(invocation, cwd=work, check=True, timeout=90)
        captures = list(work.glob('trs80-text-*.bin')); assert len(captures) == 1
        text = screen(captures[0]); captures[0].with_suffix('.txt').write_text(text)
        assert re.search(r'A0>\s*$', text.rstrip()), text
        if kind == 'full':
            rows = re.findall(r'(\d+) Recs +(\d+)K Bytes +(\d+) Ext R/W A:F(\d{3}) +\.DAT', text)
            assert len(rows) >= 10, text
            numbers = [int(row[3]) for row in rows]
            assert numbers == list(range(numbers[0], remaining)), (numbers, remaining)
            assert all(tuple(map(int, row[:3])) == (1, 2, 1) for row in rows)
            assert 'Insufficient transient memory' not in text
        else:
            assert completion in text and 'set to SYS' not in text, text
        assert disk.read_bytes() == image, 'STAT changed full-directory media'
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS',
        'directory_entries': 128, 'matching_files': remaining,
        'full_listing_scope': 'retained sorted tail; complete listing covered by existing 100-file campaign',
        'limited_slots': 0, 'attribute_request_rejected_before_mutation': True,
        'media_unchanged': True, 'stat_sha256': hashlib.sha256(stat).hexdigest(),
        'limited_stat_sha256': hashlib.sha256(constrained).hexdigest(),
        'media_sha256': hashlib.sha256(image).hexdigest(),
        'emulator_sha256': hashlib.sha256(DEFAULT_EMULATOR.read_bytes()).hexdigest()}, indent=2) + '\n')
    print('Model 4 STAT full directory and explicit workspace failure preserve media')


if __name__ == '__main__':
    main()
