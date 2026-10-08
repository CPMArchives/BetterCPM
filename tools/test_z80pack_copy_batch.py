#!/usr/bin/env python3
"""Prove oversized transient COPY batches fail before destination mutation."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from test_disk_utilities import ROOT
from test_z80pack_sysgen_install import session


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    shutil.copytree(args.image_dir / 'disks', report / 'disks')
    shutil.copy2(args.image_dir / 'diskdefs', report / 'diskdefs')
    a, b = [report / 'disks' / f'drive{x}.dsk' for x in 'ab']
    def cpm(tool, disk, *values):
        subprocess.run([tool, '-T', 'raw', '-f', ('bettercpm-default' if disk == a else 'bettercpm-mm-80t-ds-data'), str(disk), *map(str, values)], cwd=report, check=True)
    cpm('cpmrm', a, '0:COPY.COM')
    cpm('cpmcp', a, ROOT / 'build/utilities/COPY.COM', '0:COPY.COM')
    from fdf_format import select_fdf
    from test_z80pack_native_build import build_binding_program
    fmt = select_fdf(ROOT / 'third_party/montezuma/DISK-INT.FDF',
                     'Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)')
    setup = build_binding_program(report)
    cpm('cpmcp', a, setup, '0:SETBUILD.COM')
    b.write_bytes(bytes([229]) * fmt.image_bytes)
    c = report / 'disks/drivec.dsk'
    c.write_bytes(bytes([229]) * fmt.image_bytes)
    fixture = report / 'empty.dat'
    fixture.write_bytes(b'')
    for number in range(65):
        cpm('cpmcp', b, fixture, f'1:F{number:03}.DAT')
    before = b.read_bytes()
    simulator = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    text = session(simulator, report / 'disks', [
        (b'SETBUILD\r', b'A0>_ ', 30),
        (b'CPX UNLOAD RCP\r', b'A0>_ ', 30),
        (b'COPY B1:*.DAT B2:\r', b'A0>_ ', 120)], report / 'overflow.txt')
    assert b'COPY BATCH TOO LARGE' in text, text
    assert b.read_bytes() == before, 'overflow modified source/destination media'
    cpm('cpmrm', b, '1:F064.DAT')
    source_before = b.read_bytes()
    text = session(simulator, report / 'disks', [
        (b'SETBUILD\r', b'A0>_ ', 30),
        (b'CPX UNLOAD RCP\r', b'A0>_ ', 30),
        (b'COPY B1:*.DAT C2:\r', b'A0>_ ', 120)], report / 'boundary.txt')
    assert b'COPY BATCH TOO LARGE' not in text, text
    assert b.read_bytes() == source_before, 'boundary copy modified source'
    for number in range(64):
        extracted = report / f'copied-{number}.dat'
        cpm('cpmcp', c, f'2:F{number:03}.DAT', extracted)
        assert extracted.read_bytes() == b''
    (report / 'evidence.json').write_text(json.dumps({
        'result': 'PASS', 'sources': 65, 'capacity': 64, 'overflow_media_unchanged': True, 'boundary_64_files_copied': True,
        'copy_sha256': hashlib.sha256((ROOT / 'build/utilities/COPY.COM').read_bytes()).hexdigest()}, indent=2) + '\n')
    print('Transient COPY 64-file batch passes; 65-file overflow preserves media')


if __name__ == '__main__':
    main()
