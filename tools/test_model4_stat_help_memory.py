#!/usr/bin/env python3
"""Qualify Model 4 STAT help, live RSX memory maps and rejected ECB metadata."""
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
from system_layout import SYMBOLS
from add_cpm_file_to_dmk import extract_raw
from build_trs80_boot import FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE


def validate_map(text):
    rows = [(int(high, 16), int(low, 16), int(size), owner) for high, low, size, owner
            in re.findall(r'([0-9A-F]{4})-([0-9A-F]{4}) +(\d+) ([^\n]+)', text)]
    assert rows and rows[0][0] == 65535 and rows[-1][:3] == (255, 0, 256), text
    for index, (high, low, size, owner) in enumerate(rows):
        assert high >= low and size == high - low + 1, (owner, high, low, size)
        if index:
            assert rows[index - 1][1] == high + 1, ('gap/overlap', rows[index - 1], rows[index])
    assert sum(row[2] for row in rows) == 65536, rows
    assert rows[0][1] == SYMBOLS['LY_LIMIT'], rows[0]
    gate = next(row for row in rows if row[3] == 'Dynamic CP/M gateway')
    assert gate[2] == 3
    maximum = int(re.search(r'Maximum loadable COM: +(\d+) bytes', text)[1])
    assert maximum == ((gate[1] - 256) // 128) * 128, (gate, maximum)
    return rows, maximum

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    report = args.report.resolve(); report.mkdir(parents=True, exist_ok=args.resume)
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)
    stat = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    listing = (ROOT / 'build/utilities/stat.lst').read_text()
    entry = int(re.search(r'^([0-9a-f]{4})\s+.*?\bMEMREPORT:', listing, re.M | re.I)[1], 16) - 0x100
    assert stat[entry] == 0x21
    address = (len(stat) + 0x100 + 255) & ~255
    extras = [('STAT.COM', stat), ('RSX.COM', (ROOT / 'build/utilities/RSX.COM').read_bytes()),
              ('ECHO.RSX', (ROOT / 'build/rsx/ECHO.RSX').read_bytes())]
    overlays = ('R3PACK', 'R3CACHE')
    extras += [(name + '.RSX', (ROOT / 'build/system' / (name + '.RSX')).read_bytes())
               for name in overlays]
    for name, record in [('NOMETA.COM', bytes(32)), ('BADSIG.COM', b'XX\1' + bytes(29)),
                         ('BADVER.COM', b'BM\2' + bytes(29))]:
        patched = bytearray(stat)
        patched[entry + 1:entry + 3] = address.to_bytes(2, 'little')
        patched += bytes(address - 0x100 - len(patched)) + record
        extras.append((name, bytes(patched)))
    for name, data in extras:
        (report / name).write_bytes(data)
    image = medium(tuple(extras))
    disk = report / 'system.dmk'
    if not args.resume:
        disk.write_bytes(image)
    assert disk.read_bytes() == image

    def launch(stem, commands):
        work = report / stem
        retained = args.resume and work.exists()
        work.mkdir(exist_ok=retained)
        invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-d0', str(disk), '-id', '3000']
        for command, completion in commands:
            invocation += keys(command + '\r') + ['-itime', '0']
            if completion is not None:
                invocation += ['-iw', completion]
            # A0> may still be visible in the command echo. Allow the file-
            # backed RSX transaction to finish before typing the next command.
            delay = '20000' if command.startswith('RSX LOAD ') else '6000'
            invocation += ['-iw', 'A0> ', '-id', delay, '-it']
        invocation += ['-ix']
        if retained:
            assert json.loads((work / 'invocation.json').read_text()) == invocation
        else:
            disk.write_bytes(image)
            (work / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
            run(invocation, cwd=work, check=True, timeout=90)
        captures = sorted(work.glob('trs80-text-*.bin'), key=lambda p: int(p.stem.rsplit('-', 1)[1]))
        assert len(captures) == len(commands)
        results = []
        for capture, (command, _) in zip(captures, commands):
            text = screen(capture); capture.with_suffix('.txt').write_text(text)
            assert re.search(r'A0>\s*$', text.rstrip()), text
            if command.startswith('RSX LOAD '):
                assert 'RSX module or profile error' not in text, text
            # The complete memory map can scroll the command echo off screen.
            results.append(text.rsplit('A0>' + command, 1)[-1])
        if any(command.startswith('RSX LOAD ') for command,_ in commands):
            # Loading legitimately creates the manager's ordinary cache file.
            protected=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
            assert extract_raw(disk.read_bytes())[:protected]==extract_raw(image)[:protected]
        else:
            assert disk.read_bytes() == image, 'Inspection changed media'
        return results

    helptext = launch('help', [('STAT VAL:', 'BAT: console input uses RDR:; output uses LST:.')])[0]
    for line in ['Temp R/O Disk: d:=R/O', 'Set Indicator: d:filename.typ $R/O $R/W $SYS $DIR',
                 'File Size    : d:filename.typ $S (logical record count)',
                 'Drive Status : STAT or d:', 'Disk Details : DSK: d:DSK:',
                 'User Status  : USR:', 'Device Status: DEV:', 'Memory Status: MEM',
                 'CON:=TTY: CRT: BAT: UC1:', 'RDR:=TTY: PTR: UR1: UR2:',
                 'PUN:=TTY: PTP: UP1: UP2:', 'LST:=TTY: CRT: LPT: UL1:',
                 'Separate multiple assignments with spaces.',
                 'BAT: console input uses RDR:; output uses LST:.']:
        assert line in helptext, (line, helptext)

    baseline = launch('memory', [('STAT MEM', 'Maximum loadable COM:')])[0]
    loaded = launch('loaded-memory-completed', [('RSX LOAD ECHO', None),
                                    ('STAT MEM', 'Maximum loadable COM:')])[1]
    before, before_max = validate_map(baseline)
    after, after_max = validate_map(loaded)
    assert not any(row[3] == 'Loaded RSX allocation' for row in before)
    assert any(row[3] == 'Loaded RSX allocation' for row in after)
    assert after_max < before_max, (before_max, after_max)
    for stem in ('NOMETA', 'BADSIG', 'BADVER'):
        text = launch(stem.lower(), [(stem + ' MEM', 'STAT MEM requires BetterCP/M ECB version 1')])[0]
        assert 'STAT MEM requires BetterCP/M ECB version 1' in text and 'BetterCP/M Memory Map' not in text, text
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS',
        'baseline_maximum_com': before_max, 'loaded_maximum_com': after_max,
        'baseline_map': before, 'loaded_map': after, 'inspection_media_unchanged': True,
        'rsx_cache_writes_allowed': True,
        'stat_sha256': hashlib.sha256(stat).hexdigest(),
        'media_sha256': hashlib.sha256(image).hexdigest(),
        'emulator_sha256': hashlib.sha256(DEFAULT_EMULATOR.read_bytes()).hexdigest()}, indent=2) + '\n')
    print('Model 4 STAT VAL, complete memory maps, loaded RSX and invalid metadata passed')


if __name__ == '__main__':
    main()
