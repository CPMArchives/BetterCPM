#!/usr/bin/env python3
"""Focused NOAH launch/PATH regressions on disposable BetterCP/M media."""
import argparse
from pathlib import Path
import shutil
import subprocess

from build_noah import build
from test_lbr import archive, entry, with_crcs
from test_ark import member as arc_member
from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system-image', type=Path, required=True)
    p.add_argument('--diskdefs', type=Path, required=True)
    p.add_argument('--simulator', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    work = a.output.resolve()
    work.mkdir(parents=True, exist_ok=False)
    image = build(Path.home() / 'bin/z80asm', work / 'binary')
    raw = with_crcs(archive([entry(b'README  TXT')], b'X'*128))
    # local valid, remote valid/missing, local/path invalid before later valid,
    # cross-user PATH and a codec operation that reloads multiple phases.
    cases = (
        ('current', 0, 'C0: B0:', 'a', 0, None, 'README.TXT', '/L TEST.LBR'),
        ('remote', 0, 'C0: B0:', 'c', 0, None, 'README.TXT', '/L TEST.LBR'),
        ('missing', 0, 'C0: B0:', None, 0, None, 'NOAH.OVL not found', '/L TEST.LBR'),
        ('invalid-path', 0, 'C0: B0:', 'b', 0, 'c', 'invalid or incompatible', '/L TEST.LBR'),
        ('invalid-local', 0, 'C0: B0:', 'c', 0, 'a', 'invalid or incompatible', '/L TEST.LBR'),
        ('cross-user', 7, 'C3: B0:', 'c', 3, None, 'README.TXT', '/L TEST.LBR'),
        ('ark-list', 7, 'C3: B0:', 'c', 3, None, 'listed.', '/L TEST.ARC'),
        ('ark-extract', 7, 'C3: B0:', 'c', 3, None, 'extracted.', '/X TEST.ARC D4:'),
        ('codec-reload', 7, 'C3: B0:', 'c', 3, None, 'published', '/SQ TEXT.DAT A7:'),
    )
    for name, user, path, overlay_drive, overlay_user, bad_drive, wanted, tail in cases:
        case = work / name
        disks = case / 'disks'
        disks.mkdir(parents=True)
        shutil.copy2(a.diskdefs, case / 'diskdefs')
        shutil.copy2(a.system_image, disks / 'drivea.dsk')
        # Make room only on the disposable boot copy. These unrelated tools
        # are not used by the test; PATH and all boot/CCP carriers stay intact.
        subprocess.run(['cpmrm', '-T', 'raw', '-f', 'bettercpm-default',
                        str(disks/'drivea.dsk'), '0:ED.COM', '0:FDB.COM'],
                       cwd=case, check=True)
        for drive in 'bcd':
            (disks / f'drive{drive}.dsk').write_bytes(b'\xe5' * a.system_image.stat().st_size)

        def put(drive, user_area, filename, data):
            source = case / filename
            source.write_bytes(data)
            subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default',
                            str(disks/f'drive{drive}.dsk'), str(source),
                            f'{user_area}:{filename}'], cwd=case, check=True)

        put('c', 3 if user else 0, 'NOAH.COM', image)
        if name == 'current':
            put('a', user, 'NOAH.COM', image)
        put('a', user, 'TEST.LBR', raw)
        arc = arc_member(b'archive bytes', name=b'README.TXT') + b'\x1a\0'
        put('a', user, 'TEST.ARC', arc)
        put('a', user, 'TEXT.DAT', b'hello'*25 + b'END')
        if overlay_drive:
            put(overlay_drive, overlay_user, 'NOAH.OVL', image.overlay)
        if bad_drive:
            put(bad_drive, user if bad_drive == 'a' else 0, 'NOAH.OVL', b'bad overlay')
        commands = [(f'A0:PATH {path}\r'.encode(), b'A0>_ ', 10)]
        if user:
            commands.append((f'USER {user}\r'.encode(), f'A{user}>_ '.encode(), 10))
        commands += [(f'NOAH {tail}\r'.encode(), wanted.encode(), 30),
                     (b'', f'A{user}>_ '.encode(), 10)]
        text = session(a.simulator.resolve(), disks, commands, case/'transcript.txt')
        if 'invalid' in name or name == 'missing':
            assert b'README.TXT   ' not in text and b'operation stopped' in text, text
        else:
            assert b'operation stopped' not in text, text
        if name == 'ark-extract':
            source = case / 'extracted.txt'
            subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default',
                            str(disks/'drived.dsk'), '4:README.TXT', str(source)],
                           cwd=case, check=True)
            assert source.read_bytes() == b'archive bytes'+b'\x1a'*115
        if name == 'codec-reload':
            from test_sq import host_decode
            source = case / 'output.sq'
            subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default',
                            str(disks/'drivea.dsk'), '7:TEXT.DQT', str(source)],
                           cwd=case, check=True)
            assert host_decode(source.read_bytes(), record_padding=True)[1] == b'hello'*25+b'END'
        print(f'PASS: guest {name}; returned to A{user}')
    print(f'PASS: {len(cases)} real CCP/BDOS NOAH PATH cases')


if __name__ == '__main__':
    main()
