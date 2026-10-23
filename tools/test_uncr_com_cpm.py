#!/usr/bin/env python3
"""Run standalone UNCR.COM on disposable stock CP/M 2.2/z80pack disks.

Verifies a manifest-authenticated historical file, binary/empty output, padded
header extensions/metadata, destination selection, collisions and bad-file
cleanup. Requires cpmtools/expect; user's emulator media are never accessed.
"""
import argparse
import csv
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from build_uncr import build
from test_uncr import decode, fixture, header
from test_uncr_com import crunch
from test_usq_com import padded
from test_usq_com_cpm import run

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    parser.add_argument('--z80pack', type=Path, default=Path.home() / 'projects/git/z80pack')
    parser.add_argument('--corpus', type=Path, default=ROOT.parent / 'cpm-2.2-compatibility-suite/suite/crunched-source')
    args = parser.parse_args()
    simulator = args.z80pack / 'cpmsim/cpmsim'
    template = args.z80pack / 'cpmsim/disks/library/cpm22-62khd.dsk'
    with (args.corpus / 'MANIFEST.tsv').open() as stream:
        row = next(row for row in csv.DictReader(stream, delimiter='\t') if row['utility'] == 'FILETEST')
    historical = (args.corpus / 'FILETEST.MZC').read_bytes()
    assert hashlib.sha256(historical).hexdigest() == row['mzc_sha256']
    historical_data, _, _ = decode(historical)
    size = int(row['mac_size'])
    assert hashlib.sha256(historical_data[:size]).hexdigest() == row['mac_sha256']
    data = bytes(range(256)) * 4 + b'CP/M\0\x1a\x90\xff'
    bad = bytearray(crunch(b'bad checksum' * 20, b'BAD.BIN')); bad[-1] ^= 1
    fixtures = {'GOOD.BZN': crunch(data, b'OUT.BIN[STAMP]'),
                'BAD.BZN': bytes(bad), 'UNSAFE.BZN': crunch(b'unsafe', b'B:EVIL.BIN'),
                'EMPTY.BZN': crunch(b'', b'EMPTY.BIN'),
                'STAMP.AZ': crunch(b'short extension', b'SHORT.A  [STAMP]'),
                'OLD.BZN': header(info=b'\x12\x10\0\0'),
                'BROKEN.BZN': fixture([144, 256], validate=False)[0],
                'FILETEST.MZC': historical}
    with tempfile.TemporaryDirectory(prefix='bettercpm-uncr-real-cpm-') as temp:
        work = Path(temp)
        build(args.assembler, work)
        disks = work / 'disks'; disks.mkdir()
        for letter in 'ab':
            shutil.copy2(template, disks / f'drive{letter}.dsk')
            if letter != 'a':
                run('mkfs.cpm', '-f', 'ibm-3740', disks / f'drive{letter}.dsk')
        def put(letter, name, raw):
            host = work / 'import.bin'; host.write_bytes(raw)
            run('cpmcp', '-f', 'ibm-3740', disks / f'drive{letter}.dsk', host, f'0:{name}')
        def get(letter, name):
            host = work / 'export.bin'; host.unlink(missing_ok=True)
            run('cpmcp', '-f', 'ibm-3740', disks / f'drive{letter}.dsk', f'0:{name}', host)
            assert host.exists(), (letter, name)
            return host.read_bytes()
        put('a', 'UNCR.COM', (work / 'UNCR.COM').read_bytes())
        before = {}
        for name, raw in fixtures.items():
            put('a', name, raw)
            before[name] = get('a', name)
        put('b', 'UCR00000.$$$', b'KEEP TEMP')
        temp_before = get('b', 'UCR00000.$$$')
        put('b', 'DRIVE.BZN', crunch(b'logged drive', b'DRIVE.TXT'))
        drive_before = get('b', 'DRIVE.BZN')
        commands = [
            ('UNCR GOOD.BZN B:', 'UNCR: complete.'),
            ('UNCR GOOD.BZN B:', 'UNCR: output exists; nothing replaced.'),
            ('UNCR BAD.BZN B:', 'UNCR: checksum mismatch.'),
            ('UNCR UNSAFE.BZN B:', 'UNCR: unsafe embedded filename.'),
            ('UNCR EMPTY.BZN B:', 'UNCR: complete.'),
            ('UNCR STAMP.AZ B:', 'UNCR: complete.'),
            ('UNCR OLD.BZN B:', 'UNCR: unsupported crunch variant.'),
            ('UNCR BROKEN.BZN B:', 'UNCR: invalid or truncated crunched file.'),
            ('UNCR B:DRIVE.BZN', 'UNCR: complete.'),
            ('UNCR FILETEST.MZC B:', 'UNCR: complete.'),
            ('UNCR', 'Usage: UNCR'),
        ]
        script = r'''
set timeout 30
proc await {text} {
 expect {
  -exact $text {return}
  timeout {puts "TIMEOUT waiting for $text"; exit 1}
  eof {puts "EOF waiting for $text"; exit 1}
 }
}
spawn [lindex $argv 0] -z -d [lindex $argv 1]
await "A>"
'''
        for command, message in commands:
            script += f'send -- "{command}\\r"\nawait "{message}"\nawait "A>"\n'
        script += 'send -- "\\034"\nexpect eof\n'
        (work / 'test.exp').write_text(script)
        env = dict(os.environ)
        env['PATH'] = str(simulator.parent / 'srctools') + os.pathsep + env['PATH']
        result = subprocess.run(['expect', str(work / 'test.exp'), str(simulator), str(disks)],
                                cwd=work, env=env, capture_output=True, text=True, timeout=180)
        assert result.returncode == 0, result.stdout + result.stderr
        for name, expected in (('OUT.BIN', padded(data)), ('EMPTY.BIN', b''),
                               ('SHORT.A', padded(b'short extension')),
                               ('FILETEST.MAC', padded(historical_data))):
            assert get('b', name) == expected, name
        assert get('a', 'DRIVE.TXT') == padded(b'logged drive')
        assert get('b', 'DRIVE.BZN') == drive_before
        assert get('b', 'UCR00000.$$$') == temp_before
        listing = run('cpmls', '-f', 'ibm-3740', disks / 'driveb.dsk').stdout.upper()
        assert 'BAD.BIN' not in listing and 'EVIL.BIN' not in listing, listing
        assert listing.count('.$$$') == 1 and 'UCR00000.$$$' in listing, listing
        for name in fixtures:
            assert get('a', name) == before[name], (name, 'source changed')
        assert get('a', 'UNCR.COM') == (work / 'UNCR.COM').read_bytes()
        print(f'PASS: {len(commands)} stock CP/M 2.2 commands; historical FILETEST.MAC hash,')
        print('binary/empty output, metadata, drives, collisions, cleanup and sources checked.')


if __name__ == '__main__':
    main()
