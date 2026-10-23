#!/usr/bin/env python3
"""Round-trip LZH.COM -> UNLZH.COM on stock CP/M 2.2, using disposable disks.

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

from build_lzh import build
from build_unlzh import build as build_unlzh
from test_lzh_com import checked
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
        ('EMPTY', 'EMPTY.YYY', b''), ('ONE.A', 'ONE.AY', b'A'),
        ('TWO.AB', 'TWO.AY', b'\x90\x1a\0'),
        ('MIDDLE.AYC', 'MIDDLE.AYY', b'existing middle Y'),
        ('SHORT.YY', 'SHORT.YYY', b'two extension Ys'),
        ('NEXT.AYY', 'NEXT.YYY', b'fallback YYY'),
        ('LAST.YYA', 'LAST.YYY', b'last character becomes Y'),
        ('TEXT.TXT', 'TEXT.TYT', b'CP/M compressed text\r\n' * 50),
        ('R127.BIN', 'R127.BYN', bytes(range(127))),
        ('R128.BIN', 'R128.BYN', bytes(range(128))),
        ('R129.BIN', 'R129.BYN', bytes(range(129))),
        ('RUNS.DAT', 'RUNS.DYT', b'\x90' * 2048 + b'A' * 18000),
        ('EXTENT.BIN', 'EXTENT.BYN', bytes(rng.randrange(256) for _ in range(17001))),
        ('BIG.BIN', 'BIG.BYN', bytes(rng.randrange(256) for _ in range(70001))),
    ]
    with tempfile.TemporaryDirectory(prefix='bettercpm-lzh-real-cpm-') as temporary:
        work = Path(temporary)
        build(args.assembler, work)
        build_unlzh(args.assembler, work)
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
        for name in ('LZH.COM', 'UNLZH.COM'):
            put('a', name, (work / name).read_bytes())
        originals = {}
        for name, _, data in fixtures:
            # Explicit physical-record contents, including padding, are the
            # portable CP/M 2.2 contract (no byte-exact host length metadata).
            put('a', name, padded(data))
            originals[name] = get('a', name)
        put('b', 'LZU00000.$$$', b'KEEP EXISTING TEMP')
        temp_before = get('b', 'LZU00000.$$$')
        put('b', 'DEFAULT.TXT', padded(b'logged-drive destination'))
        default_before = get('b', 'DEFAULT.TXT')
        put('a', 'REFUSE.YYY', b'KEEP REFUSED INPUT')
        refused_before = get('a', 'REFUSE.YYY')
        commands = []
        for name, compressed, _ in fixtures:
            commands += [(f'LZH {name} B:', 'LZH: complete.'),
                         (f'UNLZH B:{compressed} C:', 'UNLZH: complete.')]
        commands += [('LZH TEXT.TXT B:', 'LZH: output exists; nothing replaced.'),
                     ('UNLZH B:TEXT.TYT C:', 'UNLZH: output exists; nothing replaced.'),
                     ('LZH REFUSE.YYY', 'LZH: cannot compress .YYY names.'),
                     ('LZH B:DEFAULT.TXT', 'LZH: complete.'),
                     ('UNLZH DEFAULT.TYT C:', 'UNLZH: complete.'),
                     ('LZH', 'Usage: LZH')]
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
        rebuilds = 0
        for name, compressed, data in fixtures:
            assert get('a', name) == originals[name], (name, 'source changed')
            assert get('c', name) == padded(data), (name, 'round trip changed record bytes')
            rebuilds += checked(get('b', compressed), name, data)
        assert get('b', 'LZU00000.$$$') == temp_before
        assert get('b', 'DEFAULT.TXT') == default_before
        assert get('c', 'DEFAULT.TXT') == padded(b'logged-drive destination')
        checked(get('a', 'DEFAULT.TYT'), 'DEFAULT.TXT', b'logged-drive destination')
        assert get('a', 'REFUSE.YYY') == refused_before
        assert rebuilds > 0
        listing = run('cpmls', '-f', 'ibm-3740', disks / 'driveb.dsk').stdout.upper()
        assert listing.count('.$$$') == 1 and 'LZU00000.$$$' in listing, listing
        for name in ('LZH.COM', 'UNLZH.COM'):
            assert get('a', name) == (work / name).read_bytes()
        print(f'PASS: {len(commands)} stock CP/M 2.2 commands; {len(fixtures) + 1} LZH.COM -> UNLZH.COM round trips;')
        print('empty/binary/record boundaries/extents/>64 KiB, names, drives and collisions checked.')


if __name__ == '__main__':
    main()
