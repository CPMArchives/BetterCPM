#!/usr/bin/env python3
"""Qualify Model 4 STAT two-drive reports and temporary drive read-only state."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from build_ccp import assemble
from build_montezuma_extended_790k import build, RAW_SIZE
from add_cpm_file_to_dmk import extract_raw
from test_disk_utilities import ROOT, medium, keys
from test_sysgen_install import screen
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--resume', action='store_true', help='Validate retained cases and run missing cases')
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=args.resume)
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)
    stat = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    listing = (ROOT / 'build/utilities/stat.lst').read_text()
    trampoline = (len(stat) + 0x100 + 255) & ~255

    def patched(name, count, source, stem):
        entry = int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':', listing, re.M | re.I)[1], 16)
        binary = bytearray(stat)
        original = binary[entry - 0x100:entry - 0x100 + count]
        binary[entry - 0x100:entry - 0x100 + count] = bytes((0xc3, trampoline & 255, trampoline >> 8)) + bytes(count - 3)
        tail = assemble(Path.home() / 'bin/z80asm', f' ORG {trampoline}\n' + source + '\n END\n', report / (stem + '.bin'), report / (stem + '.lst'), trampoline)
        binary += bytes(trampoline - 0x100 - len(binary)) + tail + original + bytes((0xc3, (entry + count) & 255, (entry + count) >> 8))
        return bytes(binary)

    def select(readonly=False):
        return ' LD E,1\n LD C,14\n CALL 5\n' + (' LD C,28\n CALL 5\n' if readonly else '') + ' LD E,0\n LD C,14\n CALL 5\n'

    ds = patched('DISKSTATUS', 5, select(), 'dsstat')
    ro = patched('DISKSTATUS', 5, select(True), 'rods')
    allstat = patched('ALLDETAILS', 5, select(), 'allstat')
    check = patched('FINISH', 3, ''' LD C,29
 CALL 5
 LD A,H
 OR A
 JR NZ,BAD
 LD A,L
 CP 2
 JR NZ,BAD
 LD DE,GOOD
 JR PRINT
BAD: LD DE,FAIL
PRINT: LD C,9
 CALL 5
 JR DONE
GOOD: DB 'B ONLY READ-ONLY',13,10,'$'
FAIL: DB 'READ-ONLY VECTOR WRONG',13,10,'$'
DONE:
''', 'assignck')
    extras = [('STAT.COM', stat), ('DSSTAT.COM', ds), ('RODS.COM', ro),
              ('ALLSTAT.COM', allstat), ('ASSIGNCK.COM', check)]
    for name, data in extras:
        (report / name).write_bytes(data)
    aimage = medium(tuple(extras))
    bimage = build(bytes([0xe5]) * RAW_SIZE)
    raw = extract_raw(aimage)
    directory = raw[40 * 512:40 * 512 + 128 * 32]
    used = {int.from_bytes(directory[at + offset:at + offset + 2], 'little')
            for at in range(0, len(directory), 32) if directory[at] <= 31
            for offset in range(16, 32, 2)} - {0}
    afree = (390 - 2 - len(used)) * 2
    a = report / 'a.dmk'
    b = report / 'b.dmk'
    if not args.resume:
        a.write_bytes(aimage)
        b.write_bytes(bimage)
    assert a.read_bytes() == aimage and b.read_bytes() == bimage

    def launch(stem, commands):
        work = report / stem
        retained = work.exists() and args.resume
        work.mkdir(exist_ok=retained)
        invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-d0', str(a), '-d1', str(b), '-id', '3000']
        for command, completion in commands:
            invocation += keys(command + '\r') + ['-itime', '0', '-iw', completion, '-iw', 'A0> ', '-id', '1000', '-it']
        invocation += ['-ix']
        if retained:
            assert json.loads((work / 'invocation.json').read_text()) == invocation
        else:
            (work / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
            run(invocation, cwd=work, check=True, timeout=90)
        captures = sorted(work.glob('trs80-text-*.bin'), key=lambda p: int(p.stem.rsplit('-', 1)[1]))
        assert len(captures) == len(commands)
        result = []
        for capture, (command, _) in zip(captures, commands):
            text = screen(capture); capture.with_suffix('.txt').write_text(text)
            assert re.search(r'A0>\s*$', text.rstrip()), text
            if command.startswith('ASSIGNCK '):
                assert 'B ONLY READ-ONLY' in text, text
                result.append(text)
            else:
                assert 'A0>' + command in text, text
                result.append(text.rsplit('A0>' + command, 1)[1])
        assert a.read_bytes() == aimage and b.read_bytes() == bimage, 'Inspection changed media'
        return result

    def status(text, expected):
        rows = re.findall(r'([A-P]): R/([WO]), Space: +(\d+)K', text)
        assert rows == expected, (rows, expected, text)

    status(launch('unlogged', [('STAT', f'Space: {afree}K')])[0], [('A', 'W', str(afree))])
    status(launch('two-drives', [('DSSTAT', 'B: R/W, Space: 796K')])[0], [('A', 'W', str(afree)), ('B', 'W', '796')])
    status(launch('readonly-status', [('RODS', 'B: R/O, Space: 796K')])[0], [('A', 'W', str(afree)), ('B', 'O', '796')])
    texts = launch('assignment-wboot', [('ASSIGNCK B:=R/O', 'B ONLY READ-ONLY'), ('DSSTAT', 'B: R/W, Space: 796K')])
    assert 'B ONLY READ-ONLY' in texts[0] and 'READ-ONLY VECTOR WRONG' not in texts[0]
    status(texts[1], [('A', 'W', str(afree)), ('B', 'W', '796')])
    assert 'Invalid STAT command' in launch('reject-rw', [('STAT B:=R/W', 'Invalid STAT command')])[0]
    common = {'32 Byte Directory Entries': 128, 'Checked Directory Entries': 128,
              'Records/Extent': 128, 'Records/Allocation Block': 16}
    expected = {
        'A': dict(common, **{'128 Byte Record Capacity': 6240, 'Kilobyte Drive Capacity': 780,
                            '128 Byte Records/Track': 80, 'Allocation Blocks': 390,
                            'Reserved Tracks': 2, 'Kilobytes Remaining': afree}),
        'B': dict(common, **{'128 Byte Record Capacity': 6400, 'Kilobyte Drive Capacity': 800,
                            '128 Byte Records/Track': 40, 'Allocation Blocks': 400,
                            'Reserved Tracks': 0, 'Kilobytes Remaining': 796})}
    for stem, command, drives in [('all-details', 'ALLSTAT DSK:', ['A', 'B']),
                                  ('selected-details', 'STAT B:DSK:', ['B'])]:
        text = launch(stem, [(command, '796: Kilobytes Remaining')])[0]
        sections = re.findall(r'([A-P]): Drive Characteristics\n(.*?)(?=[A-P]: Drive Characteristics|A0>|\Z)', text, re.S)
        assert [drive for drive, _ in sections] == drives, text
        for drive, body in sections:
            actual = {label: int(value) for value, label in re.findall(r'(\d+): ([A-Za-z0-9 /]+)', body)}
            assert actual == expected[drive], (actual, expected[drive], text)
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS', 'a_free_kib': afree,
        'b_free_kib': 796, 'expected_dpb_reports': expected, 'media_unchanged': True,
        'stat_sha256': hashlib.sha256(stat).hexdigest(),
        'a_sha256': hashlib.sha256(aimage).hexdigest(), 'b_sha256': hashlib.sha256(bimage).hexdigest(),
        'emulator_sha256': hashlib.sha256(DEFAULT_EMULATOR.read_bytes()).hexdigest()}, indent=2) + '\n')
    print('Model 4 STAT R/O lifecycle, WBOOT clearing and two-drive status/DPB passed')


if __name__ == '__main__':
    main()
