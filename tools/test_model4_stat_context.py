#!/usr/bin/env python3
"""Qualify STAT empty media and B3 restoration through native Model 4 BDOS."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from build_ccp import assemble
from build_montezuma_extended_790k import build, RAW_SIZE
from test_disk_utilities import ROOT, medium, keys
from test_sysgen_install import screen
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--resume', action='store_true', help='Validate retained cases and run missing cases')
    args = parser.parse_args()
    report = args.report.resolve(); report.mkdir(parents=True, exist_ok=args.resume)
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)
    stat = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    listing = (ROOT / 'build/utilities/stat.lst').read_text()
    entry = int(re.search(r'^([0-9a-f]{4})\s+.*?\bSTART:', listing, re.M | re.I)[1], 16)
    offset = entry - 0x100
    assert stat[offset:offset + 2] == bytes.fromhex('ed73'), 'START must save SP with a four-byte instruction'
    trampoline = (len(stat) + 0x100 + 255) & ~255
    tail = assemble(Path.home() / 'bin/z80asm', f''' ORG {trampoline}
 LD E,1
 LD C,14
 CALL 5
 LD E,3
 LD C,32
 CALL 5
 END
''', report / 'context.bin', report / 'context.lst', trampoline)
    wrapper = bytearray(stat)
    wrapper[offset:offset + 4] = bytes((0xc3, trampoline & 255, trampoline >> 8, 0))
    wrapper += bytes(trampoline - 0x100 - len(wrapper)) + tail + stat[offset:offset + 4] + bytes((0xc3, (entry + 4) & 255, (entry + 4) >> 8))
    (report / 'STAT.COM').write_bytes(stat)
    (report / 'CTXSTAT.COM').write_bytes(wrapper)
    aimage = medium((('STAT.COM', stat), ('CTXSTAT.COM', bytes(wrapper)), ('ONLY.DAT', bytes(128))))
    bimage = build(bytes([0xe5]) * RAW_SIZE)
    a = report / 'a.dmk'
    b = report / 'b.dmk'
    if not args.resume:
        a.write_bytes(aimage)
        b.write_bytes(bimage)
    assert a.read_bytes() == aimage and b.read_bytes() == bimage
    cases = [
        ('USR:', 'Active Files:', 'empty_users'),
        ('B:*.DAT', 'File Not Found', 'File Not Found'),
        ('A0:ONLY.DAT', 'ONLY', 'file'),
        ('A0:MISSING.DAT', 'File Not Found', 'File Not Found'),
        ('A:DSK:', 'Kilobytes Remaining', 'details'),
        ('A32:*.DAT', 'Invalid STAT command', 'Invalid STAT command'),
        ('32:*.DAT', 'Invalid STAT command', 'Invalid STAT command'),
        ('A0:ONLY.DAT EXTRA', 'Invalid STAT command', 'Invalid STAT command'),
        ('A0:F*X.DAT', 'Invalid filespec', 'Invalid filespec'),
    ]
    for number, (operand, completion, expected) in enumerate(cases):
        work = report / f'case-{number}'
        retained = work.exists() and args.resume
        work.mkdir(exist_ok=retained)
        command = 'CTXSTAT ' + operand
        invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-d0', str(a), '-d1', str(b), '-id', '3000']
        invocation += keys(command + '\r') + ['-itime', '0', '-iw', completion, '-iw', 'B3> ', '-id', '500', '-it', '-ix']
        if retained:
            assert json.loads((work / 'invocation.json').read_text()) == invocation
        else:
            (work / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
            run(invocation, cwd=work, check=True, timeout=60)
        captures = list(work.glob('trs80-text-*.bin')); assert len(captures) == 1
        text = screen(captures[0]); captures[0].with_suffix('.txt').write_text(text)
        assert 'A0>' + command in text and re.search(r'B3>\s*$', text.rstrip()), text
        current = text.rsplit('A0>' + command, 1)[1]
        if expected == 'empty_users':
            assert re.search(r'Active User : +3\s', current), current
            assert re.search(r'Active Files:\s*B3>', current), current
        elif expected == 'file':
            assert re.search(r'0*1 Recs +0*2K Bytes +0*1 Ext R/W A:ONLY +\.DAT', current), current
        elif expected == 'details':
            assert current.count('A: Drive Characteristics') == 1 and 'B: Drive Characteristics' not in current, current
            assert '00780: Kilobyte Drive Capacity' in current, current
        else:
            assert expected in current, current
        assert a.read_bytes() == aimage and b.read_bytes() == bimage, 'STAT changed media'
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS',
        'commands': ['CTXSTAT ' + case[0] for case in cases],
        'entry_context': 'B3', 'returned_context': 'B3', 'media_unchanged': True,
        'stat_sha256': hashlib.sha256(stat).hexdigest(),
        'wrapper_sha256': hashlib.sha256(wrapper).hexdigest(),
        'a_sha256': hashlib.sha256(aimage).hexdigest(), 'b_sha256': hashlib.sha256(bimage).hexdigest(),
        'emulator_sha256': hashlib.sha256(DEFAULT_EMULATOR.read_bytes()).hexdigest()}, indent=2) + '\n')
    print('Model 4 STAT empty media and B3 restoration after success and errors passed')


if __name__ == '__main__':
    main()
