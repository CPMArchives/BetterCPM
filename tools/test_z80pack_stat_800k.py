#!/usr/bin/env python3
"""Qualify complete STAT listings and geometry on native 800K media."""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from fdf_format import select_fdf
from test_z80pack_native_build import build_binding_program
from test_z80pack_sysgen_install import digest, session
from test_z80pack_submit_xsub import ROOT


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
    fmt = select_fdf(ROOT / 'third_party/montezuma/DISK-INT.FDF',
                     'Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)')
    a, b, c = (work / 'disks' / f'drive{drive}.dsk' for drive in 'abc')
    data = a.read_bytes()
    a.unlink()
    a.write_bytes(data)
    for image in (b, c):
        image.unlink()
        image.write_bytes(bytes([0xe5]) * fmt.image_bytes)
    def cpm(tool, format_name, *arguments):
        subprocess.run([tool, '-T', 'raw', '-f', format_name, *map(str, arguments)], cwd=work, check=True)
    for filename in ('stat.com', 'bdosprb.com', 'rsx2tst.com'):
        cpm('cpmrm', 'bettercpm-default', a, '0:' + filename)
    stat = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    (report / 'STAT.COM').write_bytes(stat)
    cpm('cpmcp', 'bettercpm-default', a, report / 'STAT.COM', '0:STAT.COM')
    setup = build_binding_program(report)
    cpm('cpmcp', 'bettercpm-default', a, setup, '0:SETBUILD.COM')
    # Reverse insertion order makes the alphabetical-output check meaningful.
    for number in reversed(range(100)):
        records = {60: 161, 99: 513}.get(number, 1)
        source = report / 'payload.dat'
        source.write_bytes(bytes(records * 128))
        cpm('cpmcp', 'bettercpm-mm-80t-ds-data', b, source, f'0:F{number:03}.DAT')
    before = b.read_bytes()
    mapping = fmt.raw_record_map()
    raw_directory = b''.join(before[(logical // fmt.spt * fmt.spt + mapping[logical % fmt.spt]) * 128:
                                   (logical // fmt.spt * fmt.spt + mapping[logical % fmt.spt]) * 128 + 128]
                             for logical in range((fmt.drm + 1) * 32 // 128))
    entries = [raw_directory[at:at + 32] for at in range(0, len(raw_directory), 32)
               if raw_directory[at] != 0xe5]
    assert len(entries) == 105 and all(entry[0] == 0 for entry in entries)
    blocks = {int.from_bytes(entry[at:at + 2], 'little')
              for entry in entries for at in range(16, 32, 2)} - {0}
    free_kib = (fmt.dsm + 1 - fmt.directory_blocks - len(blocks)) * fmt.block_bytes // 1024
    assert free_kib == 512
    output = session(args.simulator.resolve(), work / 'disks', [
        (b'SETBUILD\r', b'A0>_ ', 30),
        (b'STAT B:F*.DAT\r', b'A0>_ ', 30),
        (b'STAT B:DSK:\r', b'A0>_ ', 30),
        (b'STAT B:\r', b'A0>_ ', 30),
    ], report / 'transcript.txt')
    text = output.decode(errors='replace')
    assert 'B SOURCE AND C WORK DISKS READY' in text and 'BUILD DISK SETUP FAILED' not in text, text
    rows = re.findall(r'(\d+) Recs +(\d+)K Bytes +(\d+) Ext R/W B:(F\d{3}) +\.DAT', text)
    assert len(rows) == 100, f'expected exactly 100 file rows, got {len(rows)}'
    for number, row in enumerate(rows):
        records, allocated, extents = {60: (161, 22, 2), 99: (513, 66, 5)}.get(number, (1, 2, 1))
        assert tuple(map(int, row[:3])) == (records, allocated, extents) and row[3] == f'F{number:03}', row
    for field in ('06400: 128 Byte Record Capacity', '00800: Kilobyte Drive Capacity',
                  '40: 128 Byte Records/Track', '400: Allocation Blocks',
                  '128: 32 Byte Directory Entries', '128: Checked Directory Entries',
                  '128: Records/Extent', '16: Records/Allocation Block',
                  '0: Reserved Tracks', 'Bytes Remaining On B: 512K'):
        assert field in text, field
    assert b.read_bytes() == before, 'STAT inspection modified the disk'
    evidence = {'result': 'PASS', 'format': fmt.name, 'files': 100,
                'physical_entries': 105, 'free_kib': 512,
                'stat_sha256': digest(stat), 'simulator_sha256': digest(args.simulator.read_bytes()),
                'disk_sha256': digest(before), 'disk_unchanged': True}
    (report / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print('STAT native 800K: 100 complete sorted files, multi-extent totals, exact DPB/free space and unchanged disk passed')


if __name__ == '__main__':
    main()
