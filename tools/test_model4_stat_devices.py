#!/usr/bin/env python3
"""Bounded Model 4 STAT device-interface parity with output-triggered captures."""
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
    image = medium((('STAT.COM', stat),))
    disk = report / 'system.dmk'
    disk.write_bytes(image)
    steps = [
        ('STAT DEV:', 'LST: is LPT:', ['CON: is CRT:', 'RDR: is PTR:', 'PUN: is PTP:', 'LST: is LPT:']),
        ('STAT CON:=CRT: LST:=CRT:', 'LST: is CRT:', ['CON: is CRT:', 'LST: is CRT:']),
        ('STAT CRT:', 'CRT: assigned to LST:', ['CRT: assigned to CON:', 'CRT: assigned to LST:']),
        ('STAT PTP:', 'PTP: assigned to PUN:', ['PTP: assigned to PUN:']),
        ('STAT UP1:', 'UP1: not assigned', ['UP1: not assigned']),
        ('STAT XYZ:', 'Unknown device target', ['Unknown device target']),
        ('STAT PTP:X', 'Invalid STAT command', ['Invalid STAT command']),
        ('STAT DEV:', 'LST: is CRT:', ['CON: is CRT:', 'RDR: is PTR:', 'PUN: is PTP:', 'LST: is CRT:']),
    ]
    invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-d0', str(disk), '-id', '3000']
    for command, completion, _ in steps:
        # Prepare the display before issuing the command. Completion also
        # requires the returned prompt, and assertions scope output to its echo.
        invocation += keys('CLS\r') + ['-id', '300']
        # The echoed command has A0>STAT, while the returned prompt has A0>
        # followed by a blank. Wait for both output and the actual warm exit.
        invocation += keys(command + '\r') + ['-itime', '0', '-iw', completion,
                                              '-iw', 'A0> ', '-it']
    invocation += ['-ix']
    (report / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
    run(invocation, cwd=report, check=True, timeout=120)
    captures = sorted(report.glob('trs80-text-*.bin'), key=lambda path: int(path.stem.rsplit('-', 1)[1]))
    assert len(captures) == len(steps), len(captures)
    for capture, (command, _, expected) in zip(captures, steps):
        text = screen(capture)
        capture.with_suffix('.txt').write_text(text)
        assert command in text, (command, text)
        current = text.rsplit('A0>' + command, 1)[1]
        for line in expected:
            assert current.count(line) == 1, (command, line, text)
        assert re.search(r'A0>\s*$', text.rstrip()), (command, 'missing completed return to prompt', text)
    assert disk.read_bytes() == image, 'device queries/assignments changed disk media'
    (report / 'evidence.json').write_text(json.dumps({
        'result': 'PASS', 'commands': [command for command, _, _ in steps],
        'stat_sha256': digest(stat), 'boot_media_sha256': digest(image),
        'emulator_sha256': digest(DEFAULT_EMULATOR.read_bytes()),
        'media_unchanged': True, 'scope': 'STAT device interface; actual BIOS routing remains separate',
    }, indent=2) + '\n')
    print('Model 4 STAT default mapping, assignment list, inverse queries and unchanged state/media passed')


if __name__ == '__main__':
    main()
