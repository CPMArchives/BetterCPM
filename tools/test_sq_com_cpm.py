#!/usr/bin/env python3
"""Round-trip SQ.COM -> USQ.COM on stock CP/M 2.2, using disposable disks.

Exercises sequential extent rollover, >64 KiB inputs, binary/record boundaries,
historical names, destination drives, output collisions and preexisting temps.
Requires z80pack, cpmtools and expect. Never uses the user's emulator disks.
"""
import argparse
import os
from pathlib import Path
import random
import shutil
import subprocess
import tempfile

from build_sq import build
from build_usq import build as build_usq
from test_sq import host_decode
from test_usq_com import padded
from test_usq_com_cpm import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    parser.add_argument('--z80pack', type=Path, default=Path.home() / 'projects/git/z80pack')
    args = parser.parse_args()
    simulator = args.z80pack / 'cpmsim/cpmsim'
    template = args.z80pack / 'cpmsim/disks/library/cpm22-62khd.dsk'
    rng = random.Random(451)
    fixtures = [
        ('EMPTY', 'EMPTY.QQQ', b''), ('ONE.A', 'ONE.AQ', b'A'),
        ('TWO.AB', 'TWO.AQ', b'\x90\x1a\0'),
        ('TEXT.TXT', 'TEXT.TQT', b'CP/M squeezed text\r\n' * 50),
        ('R127.BIN', 'R127.BQN', bytes(range(127))),
        ('R128.BIN', 'R128.BQN', bytes(range(128))),
        ('R129.BIN', 'R129.BQN', bytes(range(129))),
        ('RUNS.DAT', 'RUNS.DQT', b'\x90' * 2048 + b'A' * 18000),
        ('EXTENT.BIN', 'EXTENT.BQN', bytes(rng.randrange(256) for _ in range(17001))),
        ('BIG.BIN', 'BIG.BQN', bytes(range(256)) * 260),
    ]
    with tempfile.TemporaryDirectory(prefix='bettercpm-sq-real-cpm-') as temporary:
        work = Path(temporary)
        build(args.assembler, work)
        build_usq(args.assembler, work)
        disks = work / 'disks'
        disks.mkdir()
        for letter in 'abc':
            shutil.copy2(template, disks / f'drive{letter}.dsk')
            if letter != 'a':
                run('mkfs.cpm', '-f', 'ibm-3740', disks / f'drive{letter}.dsk')
        def put(letter, name, raw):
            host = work / 'import.bin'
            host.write_bytes(raw)
            run('cpmcp', '-f', 'ibm-3740', disks / f'drive{letter}.dsk', host, f'0:{name}')
        def get(letter, name):
            host = work / 'export.bin'
            host.unlink(missing_ok=True)
            run('cpmcp', '-f', 'ibm-3740', disks / f'drive{letter}.dsk', f'0:{name}', host)
            assert host.exists(), (letter, name)
            return host.read_bytes()
        for name in ('SQ.COM', 'USQ.COM'):
            put('a', name, (work / name).read_bytes())
        originals = {}
        for name, _, data in fixtures:
            # Explicit physical-record contents, including padding, are the
            # portable CP/M 2.2 contract (no byte-exact host length metadata).
            put('a', name, padded(data))
            originals[name] = get('a', name)
        put('b', 'SQU00000.$$$', b'KEEP EXISTING TEMP')
        temp_before = get('b', 'SQU00000.$$$')
        put('b', 'DEFAULT.TXT', padded(b'logged-drive destination'))
        default_before = get('b', 'DEFAULT.TXT')
        commands = []
        for name, squeezed, _ in fixtures:
            commands += [(f'SQ {name} B:', 'SQ: complete.'),
                         (f'USQ B:{squeezed} C:', 'USQ: complete.')]
        commands += [('SQ TEXT.TXT B:', 'SQ: output exists; nothing replaced.'),
                     ('USQ B:TEXT.TQT C:', 'USQ: output exists; nothing replaced.'),
                     ('SQ B:TEXT.TQT', 'SQ: input name already squeezed.'),
                     ('SQ B:DEFAULT.TXT', 'SQ: complete.'),
                     ('USQ DEFAULT.TQT C:', 'USQ: complete.'),
                     ('SQ', 'Usage: SQ')]
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
        for name, squeezed, data in fixtures:
            assert get('a', name) == originals[name], (name, 'source changed')
            assert get('c', name) == padded(data), (name, 'round trip changed record bytes')
            assert host_decode(get('b', squeezed), True) == (name.encode(), padded(data))
        assert get('b', 'SQU00000.$$$') == temp_before
        assert get('b', 'DEFAULT.TXT') == default_before
        assert get('c', 'DEFAULT.TXT') == padded(b'logged-drive destination')
        assert host_decode(get('a', 'DEFAULT.TQT'), True)[0] == b'DEFAULT.TXT'
        listing = run('cpmls', '-f', 'ibm-3740', disks / 'driveb.dsk').stdout.upper()
        assert listing.count('.$$$') == 1 and 'SQU00000.$$$' in listing, listing
        for name in ('SQ.COM', 'USQ.COM'):
            assert get('a', name) == (work / name).read_bytes()
        print(f'PASS: {len(commands)} stock CP/M 2.2 commands; 11 SQ.COM -> USQ.COM round trips;')
        print('empty/binary/record boundaries/extents/>64 KiB, names, drives and collisions checked.')


if __name__ == '__main__':
    main()
