#!/usr/bin/env python3
"""NOAH LBR TEST/extraction smoke on stock CP/M 2.2, disposable disks only.

Requires z80pack, cpmtools and expect. Reads the template, copies it to a fresh
private directory, and never touches daily emulator media/host endpoints.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from build_noah import build
from test_lbr import archive, entry, with_crcs
from test_usq_com import padded
from test_usq_com_cpm import run


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    p.add_argument('--z80pack', type=Path, default=Path.home() / 'projects/git/z80pack')
    a = p.parse_args()
    simulator = a.z80pack / 'cpmsim/cpmsim'
    template = a.z80pack / 'cpmsim/disks/library/cpm22-62khd.dsk'
    with tempfile.TemporaryDirectory(prefix='bettercpm-noah-real-cpm-') as temp:
        work = Path(temp)
        build(a.assembler, work)
        disks = work / 'disks'
        disks.mkdir()
        for drive in 'ab':
            shutil.copy2(template, disks / f'drive{drive}.dsk')
        run('mkfs.cpm', '-f', 'ibm-3740', disks / 'driveb.dsk')
        def put(drive, name, data):
            path = work / 'import.bin'
            path.write_bytes(data)
            run('cpmcp', '-f', 'ibm-3740', disks / f'drive{drive}.dsk', path, f'0:{name}')
        def get(drive, name):
            path = work / 'export.bin'
            path.unlink(missing_ok=True)
            run('cpmcp', '-f', 'ibm-3740', disks / f'drive{drive}.dsk', f'0:{name}', path)
            return path.read_bytes()
        put('a', 'NOAH.COM', (work / 'NOAH.COM').read_bytes())
        good = with_crcs(archive([entry(b'README  TXT', pad=3),
                                 entry(b'EMPTY      ', records=0)], bytes(range(128))))
        large = bytes(range(256)) * 273 + b'\x1a\0\xffEND'
        storage = padded(large)
        big = with_crcs(archive([entry(b'BIG     BIN', records=len(storage) // 128,
                                      pad=len(storage) - len(large))], storage))
        bad = bytearray(good)
        bad[-1] ^= 1
        fixtures = {'GOOD.LBR': good, 'BAD.LBR': bytes(bad), 'BIG.LBR': big}
        for name, data in fixtures.items():
            put('a', name, data)
        put('b', 'README00.BAK', b'KEEP RECOVERY FILE')
        recovery = get('b', 'README00.BAK')
        originals = {name: get('a', name) for name in fixtures}
        commands = [('NOAH /TEST GOOD.LBR', 'Structure/readability checked.'),
                    ('NOAH /X GOOD.LBR B:', 'Unprocessed (hex): 00000000'),
                    ('NOAH /X GOOD.LBR B:', 'skipped: 00000002'),
                    ('NOAH /TEST BAD.LBR', 'NOAH: Archive/read error 08'),
                    ('NOAH /X BAD.LBR B:', 'NOAH: Archive/read error 08'),
                    ('NOAH /TEST BIG.LBR', 'Structure/readability checked.'),
                    ('NOAH /X BIG.LBR B:', 'Unprocessed (hex): 00000000')]
        script = '''set timeout 60
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
        for command, text in commands:
            script += f'send -- "{command}\\r"\nawait "{text}"\nawait "A>"\n'
        script += 'send -- "\\034"\nexpect eof\n'
        (work / 'test.exp').write_text(script)
        env = dict(os.environ)
        env['PATH'] = str(simulator.parent / 'srctools') + os.pathsep + env['PATH']
        result = subprocess.run(['expect', str(work / 'test.exp'), str(simulator), str(disks)],
                                cwd=work, env=env, capture_output=True, text=True, timeout=180)
        assert result.returncode == 0, result.stdout + result.stderr
        assert get('b', 'README.TXT') == bytes(range(125)) + b'\x1a' * 3
        assert get('b', 'EMPTY') == b''
        assert get('b', 'BIG.BIN') == storage
        assert get('b', 'README00.BAK') == recovery
        for name, data in originals.items():
            assert get('a', name) == data, ('archive modified', name)
        listing = run('cpmls', '-f', 'ibm-3740', disks / 'driveb.dsk').stdout.upper()
        assert '.TMP' not in listing and listing.count('.BAK') == 1, listing
        print('PASS: 7 stock CP/M 2.2 NOAH commands; >64K/extent extraction, binary/pad bytes,')
        print('CRC rejection, empty output, collisions, recovery-file and source preservation verified.')


if __name__ == '__main__':
    main()
