#!/usr/bin/env python3
"""Qualify native cpmsim STAT memory maps and rejected ECB metadata."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from test_disk_utilities import ROOT
from test_model4_stat_help_memory import validate_map
from test_z80pack_sysgen_install import session


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, default=ROOT / 'build/z80pack-iobyte-qualified')
    parser.add_argument('--simulator', type=Path, default=Path.home() / 'projects/git/z80pack/cpmsim/cpmsim')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve(); report.mkdir(parents=True, exist_ok=False)
    work = report / 'runtime'; work.mkdir()
    shutil.copytree(args.image_dir / 'disks', work / 'disks')
    shutil.copy2(args.image_dir / 'diskdefs', work / 'diskdefs')
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)
    stat = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    listing = (ROOT / 'build/utilities/stat.lst').read_text()
    entry = int(re.search(r'^([0-9a-f]{4})\s+.*?\bMEMREPORT:', listing, re.M | re.I)[1], 16) - 256
    assert stat[entry] == 0x21
    address = (len(stat) + 256 + 255) & ~255
    artifacts = [('STAT.COM', stat), ('ECHO.RSX', (ROOT / 'build/rsx/ECHO.RSX').read_bytes())]
    for name, record in [('NOMETA.COM', bytes(32)), ('BADSIG.COM', b'XX\1' + bytes(29)),
                         ('BADVER.COM', b'BM\2' + bytes(29))]:
        binary = bytearray(stat)
        binary[entry + 1:entry + 3] = address.to_bytes(2, 'little')
        binary += bytes(address - 256 - len(binary)) + record
        artifacts.append((name, bytes(binary)))
    disk = work / 'disks/drivea.dsk'
    subprocess.run(['cpmrm', '-T', 'raw', '-f', 'bettercpm-default', str(disk),
                    '0:bdosprb.com', '0:rsx2tst.com', '0:rsxtest.com', '0:stattst.com', '0:svctest.com', '0:stat.com', '0:echo.rsx'], cwd=work, check=True)
    for name, binary in artifacts:
        path = report / name; path.write_bytes(binary)
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(disk), str(path), '0:' + name], cwd=work, check=True)
    before_media = {p.name: p.read_bytes() for p in (work / 'disks').glob('*.dsk')}
    commands = ['STAT MEM', 'RSX LOAD ECHO', 'STAT MEM', 'RSX UNLOAD ECHO', 'STAT MEM',
                'NOMETA MEM', 'BADSIG MEM', 'BADVER MEM']
    (report / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    transcript = session(args.simulator.resolve(), work / 'disks',
                         [(command.encode() + b'\r', b'A0>_ ', 30) for command in commands],
                         report / 'transcript.bin')
    text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', transcript.decode('ascii', errors='replace')).replace('\r', '')
    (report / 'transcript.txt').write_text(text)
    blocks = text.split('A0>_ ')[1:]
    assert len(blocks) >= len(commands), text
    results = []
    for index, command in enumerate(commands):
        block = blocks[index]
        assert command in block, (command, block)
        if command == 'STAT MEM':
            results.append(validate_map(block))
        elif command.startswith('RSX '):
            assert 'RSX module or profile error' not in block, block
        else:
            assert 'STAT MEM requires BetterCP/M ECB version 1' in block and 'BetterCP/M Memory Map' not in block, block
    baseline, loaded, unloaded = results
    assert baseline == unloaded, (baseline, unloaded)
    assert not any(row[3] == 'Loaded RSX allocation' for row in baseline[0])
    assert any(row[3] == 'Loaded RSX allocation' for row in loaded[0])
    assert loaded[1] < baseline[1]
    assert all((work / 'disks' / name).read_bytes() == image for name, image in before_media.items()), 'STAT/RSX inspection changed disk media'
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS', 'commands': commands,
        'baseline_maximum_com': baseline[1], 'loaded_maximum_com': loaded[1],
        'unload_restores_map': True, 'baseline_map': baseline[0], 'loaded_map': loaded[0],
        'media_unchanged': True, 'stat_sha256': hashlib.sha256(stat).hexdigest(),
        'simulator_sha256': hashlib.sha256(args.simulator.read_bytes()).hexdigest(),
        'disk_sha256': {name: hashlib.sha256(image).hexdigest() for name, image in before_media.items()}}, indent=2) + '\n')
    print('cpmsim STAT complete memory maps, RSX load/unload and invalid metadata passed')


if __name__ == '__main__':
    main()
