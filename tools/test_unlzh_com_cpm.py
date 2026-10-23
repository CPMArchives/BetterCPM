#!/usr/bin/env python3
"""Run standalone UNLZH.COM on disposable stock CP/M 2.2/z80pack disks.

Verifies authenticated files from both historical CrLZH variants, binary/empty output, padded
header extensions/metadata, destination selection, collisions and bad-file
cleanup. Requires cpmtools/expect; user's emulator media are never accessed.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from build_unlzh import build
from test_unlzh import decode, fixture, header
from test_unlzh_com import compress, historical
from test_usq_com import padded
from test_usq_com_cpm import run

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    parser.add_argument('--z80pack', type=Path, default=Path.home() / 'projects/git/z80pack')
    parser.add_argument('--archives', type=Path, nargs=2, default=[ROOT / 'build/test-fixtures/crlzh' / n for n in ('crlzh11.lbr', 'crlzh20.lbr')])
    args = parser.parse_args()
    simulator = args.z80pack / 'cpmsim/cpmsim'
    template = args.z80pack / 'cpmsim/disks/library/cpm22-62khd.dsk'
    wrappers = [(n, r, sig) for n, r, sig in historical(args.archives) if (sig == 0x10 and n == 'CRLZH.SYR') or (sig == 0x20 and n == 'UCRLZH20.ZY0')]
    assert len(wrappers) == 2
    from test_unlzh import WRAPPER_HASHES
    for name, raw, sig in wrappers:
        if name in WRAPPER_HASHES:
            assert hashlib.sha256(decode(raw)[0]).hexdigest() == WRAPPER_HASHES[name]
    data = bytes(range(256)) * 4 + b'CP/M\0\x1a\x90\xff'
    bad = bytearray(compress(b'bad checksum' * 20, b'BAD.BIN')); bad[-1] ^= 1
    fixtures = {'GOOD.BZN': compress(data, b'OUT.BIN[STAMP]'),
                'BAD.BZN': bytes(bad), 'UNSAFE.BZN': compress(b'unsafe', b'B:EVIL.BIN'),
                'EMPTY.BZN': compress(b'', b'EMPTY.BIN'),
                'STAMP.AZ': compress(b'short extension', b'SHORT.A  [STAMP]'),
                'OLD.BZN': header(sig=0x21),
                'BROKEN.BZN': compress(bytes(range(256)) * 4, b'BROKEN.BIN')[:128],
                'OLDOK.BYN': compress(data, b'OLDOUT.BIN', sig=0x10)}
    fixtures.update({n: r for n, r, sig in wrappers})
    with tempfile.TemporaryDirectory(prefix='bettercpm-unlzh-real-cpm-') as temp:
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
        put('a', 'UNLZH.COM', (work / 'UNLZH.COM').read_bytes())
        before = {}
        for name, raw in fixtures.items():
            put('a', name, raw)
            before[name] = get('a', name)
        put('b', 'ULZ00000.$$$', b'KEEP TEMP')
        temp_before = get('b', 'ULZ00000.$$$')
        put('b', 'DRIVE.BZN', compress(b'logged drive', b'DRIVE.TXT'))
        drive_before = get('b', 'DRIVE.BZN')
        commands = [
            ('UNLZH GOOD.BZN B:', 'UNLZH: complete.'),
            ('UNLZH GOOD.BZN B:', 'UNLZH: output exists; nothing replaced.'),
            ('UNLZH BAD.BZN B:', 'UNLZH: checksum mismatch.'),
            ('UNLZH UNSAFE.BZN B:', 'UNLZH: unsafe embedded filename.'),
            ('UNLZH EMPTY.BZN B:', 'UNLZH: complete.'),
            ('UNLZH STAMP.AZ B:', 'UNLZH: complete.'),
            ('UNLZH OLD.BZN B:', 'UNLZH: unsupported CrLZH variant.'),
            ('UNLZH BROKEN.BZN B:', 'UNLZH: invalid or truncated CrLZH file.'),
            ('UNLZH B:DRIVE.BZN', 'UNLZH: complete.'),
            ('UNLZH OLDOK.BYN B:', 'UNLZH: complete.'),
            *[(f'UNLZH {n} B:', 'UNLZH: complete.') for n, r, sig in wrappers],
            ('UNLZH', 'Usage: UNLZH'),
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
                               ('OLDOUT.BIN', padded(data))):
            assert get('b', name) == expected, name
        for name, raw, sig in wrappers:
            embedded = raw[2:raw.index(0, 2)].decode()
            stem, _, ext = embedded.partition('.')
            assert get('b', stem + '.' + ext[:3].rstrip()) == padded(decode(raw)[0])
        assert get('a', 'DRIVE.TXT') == padded(b'logged drive')
        assert get('b', 'DRIVE.BZN') == drive_before
        assert get('b', 'ULZ00000.$$$') == temp_before
        listing = run('cpmls', '-f', 'ibm-3740', disks / 'driveb.dsk').stdout.upper()
        assert 'BAD.BIN' not in listing and 'EVIL.BIN' not in listing, listing
        assert listing.count('.$$$') == 1 and 'ULZ00000.$$$' in listing, listing
        for name in fixtures:
            assert get('a', name) == before[name], (name, 'source changed')
        assert get('a', 'UNLZH.COM') == (work / 'UNLZH.COM').read_bytes()
        print(f'PASS: {len(commands)} stock CP/M 2.2 commands; both historical CrLZH variants,')
        print('binary/empty output, metadata, drives, collisions, cleanup and sources checked.')


if __name__ == '__main__':
    main()
