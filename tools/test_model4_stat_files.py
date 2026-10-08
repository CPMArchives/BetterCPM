#!/usr/bin/env python3
"""Qualify Model 4 STAT totals, wildcard ordering and direct user selection."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

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
    fixtures = [('STAT.COM', stat), ('MULTI.DAT', bytes(161 * 128)),
                ('LONG.DAT', bytes(513 * 128)), ('UONLY.DAT', bytes(128), 3)]
    fixtures += [(f'F{number:03}.DAT', bytes(128)) for number in reversed(range(5))]
    image = medium(tuple(fixtures))
    disk = report / 'system.dmk'
    disk.write_bytes(image)
    steps = [
        ('STAT MULTI.DAT', 'MULTI', [(161, 22, 2, 'MULTI')]),
        ('STAT LONG.DAT', 'LONG', [(513, 66, 5, 'LONG')]),
        ('STAT F*.DAT', 'F004', [(1, 2, 1, f'F{number:03}') for number in range(5)]),
        ('STAT 3:UONLY.DAT', 'UONLY', [(1, 2, 1, 'UONLY')]),
        ('STAT A3:UONLY.DAT', 'UONLY', [(1, 2, 1, 'UONLY')]),
        ('STAT UONLY.DAT', 'File Not Found', []),
    ]
    invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-d0', str(disk), '-id', '3000']
    for command, completion, _ in steps:
        invocation += keys('CLS\r') + ['-id', '300']
        invocation += keys(command + '\r') + ['-itime', '0', '-iw', completion,
                                              '-iw', 'A0> ', '-it']
    invocation += ['-ix']
    (report / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
    run(invocation, cwd=report, check=True, timeout=150)
    captures = sorted(report.glob('trs80-text-*.bin'), key=lambda path: int(path.stem.rsplit('-', 1)[1]))
    assert len(captures) == len(steps), len(captures)
    for capture, (command, _, expected) in zip(captures, steps):
        text = screen(capture)
        capture.with_suffix('.txt').write_text(text)
        assert 'A0>' + command in text, (command, text)
        current = text.rsplit('A0>' + command, 1)[1]
        rows = re.findall(r'(\d+) Recs +(\d+)K Bytes +(\d+) Ext R/W A:([A-Z0-9]+) +\.DAT', current)
        actual = [(*map(int, row[:3]), row[3]) for row in rows]
        assert actual == expected, (command, actual, expected, current)
        if not expected:
            assert 'File Not Found' in current, current
        assert re.search(r'A0>\s*$', text.rstrip()), (command, 'missing return to original user', text)
    assert disk.read_bytes() == image, 'STAT inspection changed disk media'
    (report / 'evidence.json').write_text(json.dumps({
        'result': 'PASS', 'commands': [command for command, _, _ in steps],
        'stat_sha256': digest(stat), 'boot_media_sha256': digest(image),
        'emulator_sha256': digest(DEFAULT_EMULATOR.read_bytes()), 'media_unchanged': True,
    }, indent=2) + '\n')
    print('Model 4 STAT multi-extent totals, wildcard ordering, numeric DU and user restoration passed')


if __name__ == '__main__':
    main()
