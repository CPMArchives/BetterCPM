#!/usr/bin/env python3
"""Exercise internal COPY verification against native BDOS file reads."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from test_disk_utilities import ROOT
from test_z80pack_sysgen_install import session


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--image-dir', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    shutil.copytree(args.image_dir / 'disks', report / 'disks')
    shutil.copy2(args.image_dir / 'diskdefs', report / 'diskdefs')
    disk = report / 'disks/driveb.dsk'
    disk.write_bytes(bytes([229]) * len(disk.read_bytes()))
    listing = (ROOT / 'build/utilities/copy-transient.lst').read_text()
    def addr(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':', listing, re.M | re.I)[1], 16)
    def cpm(tool, image, *values):
        subprocess.run([tool, '-T', 'raw', '-f', 'bettercpm-default', str(image), *map(str, values)], cwd=report, check=True)
    base = (ROOT / 'build/utilities/COPY.COM').read_bytes()
    cases = [
        ('empty', b'', b'', True),
        ('one', bytes(range(128)), bytes(range(128)), True),
        ('extents', bytes(range(256))*130, bytes(range(256))*130, True),
        ('first-byte', b'A'*128, b'B'+b'A'*127, False),
        ('last-byte', b'A'*256, b'A'*255+b'B', False),
        ('shorter', b'A'*256, b'A'*128, False),
        ('longer', b'A'*128, b'A'*256, False),
        ('missing-source', None, b'A'*128, False),
        ('missing-target', b'A'*128, None, False),
    ]
    results = []
    for label, source, target, expected in cases:
        for user, data in ((1, source), (3, target)):
            subprocess.run(['cpmrm', '-T', 'raw', '-f', 'bettercpm-default', str(disk), f'{user}:DATA.DAT'], cwd=report, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if data is not None:
                f = report / f'{label}-{user}.dat'
                f.write_bytes(data)
                cpm('cpmcp', disk, f, f'{user}:DATA.DAT')
        image = bytearray(base)
        for name, value in [('BC_CSDRV',1), ('BC_CSUSR',1), ('BC_CDDRV',1), ('BC_CDUSR',3)]:
            image[addr(name)-0x100] = value
        for name in ('BC_FCB', 'BC_NEWFCB'):
            off = addr(name)-0x100
            image[off:off+36] = bytes(36)
            image[off+1:off+12] = b'DATA    DAT'
        # A proof-only entry calls the real core and prints its carry result.
        entry = 0x100 + len(image)
        success, failure = entry+26, entry+31
        def word(n): return bytes((n & 255, n >> 8))
        code = b'\xcd'+word(addr('CTVERIFY'))+b'\xda'+word(entry+14)
        code += b'\x11'+word(success)+b'\x0e\x09\xc3'+word(entry+19)
        code += b'\x11'+word(failure)+b'\x0e\x09\xcd\x05\x00\xcd'+word(addr('BC_COK'))+b'\xc7'
        assert len(code) == 26
        image[:3] = b'\xc3'+word(entry)
        image += code+b'GOOD$BAD$'
        proof = report / 'VERIFY.COM'
        proof.write_bytes(image)
        a = report / 'disks/drivea.dsk'
        subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(a),'0:VERIFY.COM'],cwd=report,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        cpm('cpmcp', a, proof, '0:VERIFY.COM')
        before = disk.read_bytes()
        text = session(Path.home() / 'projects/git/z80pack/cpmsim/cpmsim', report / 'disks',
                       [(b'VERIFY\r', b'A0>_ ', 60)], report / f'{label}.txt')
        assert (b'GOOD' in text) == expected, label
        assert (b'BAD' in text) == (not expected), label
        assert disk.read_bytes() == before, (label, 'verification changed media')
        results.append(label)
    (report / 'evidence.json').write_text(json.dumps({'result':'PASS','cases':results,
        'copy_sha256':hashlib.sha256(base).hexdigest()}, indent=2)+'\n')
    print('Native COPY record comparison and EOF/open failure cases pass')


if __name__ == '__main__':
    main()
