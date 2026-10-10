#!/usr/bin/env python3
"""Public-prompt fixed A0 lookup checks on disposable platform disks."""
import argparse
import shutil
import subprocess
from pathlib import Path
from build_ccp import assemble
from test_disk_utilities import ROOT, medium, keys
from test_sysgen_install import screen
from test_z80pack_sysgen_install import session
from trs80gp_launch import run
from run_trs80_command import DEFAULT_EMULATOR
from fdf_format import select_fdf

p = argparse.ArgumentParser()
p.add_argument('--platform', choices=('model4', 'z80pack'), required=True)
p.add_argument('--report', type=Path, required=True)
p.add_argument('--image-dir', type=Path)
p.add_argument('--verify-existing', action='store_true')
a = p.parse_args()
w = a.report.resolve()
w.mkdir(parents=True, exist_ok=a.verify_existing)
assert not a.verify_existing or a.platform == 'model4'
drive = 0 if a.platform == 'model4' else 1
location = 'A3' if drive == 0 else 'B3'

def probe(label):
    source = '''        ORG 0100H
        LD C,25
        CALL 5
        CP %d
        JR NZ,BAD
        LD E,0FFH
        LD C,32
        CALL 5
        CP 3
        JR NZ,BAD
        LD DE,GOOD
        JR SHOW
BAD:    LD DE,FAIL
SHOW:   LD C,9
        CALL 5
        JP 0
GOOD:   DB '%s',13,10,'$'
FAIL:   DB 'CALLER DU WRONG',13,10,'$'
        END
''' % (drive, label)
    return assemble(Path('/Users/nathanael/bin/z80asm'), source,
                    w / (label + '.bin'), w / (label + '.lst'), 0x100)

fallback = probe('A0 FALLBACK PASS')
local = probe('LOCAL PRECEDENCE PASS')
commands = [('WHERE', 'A0 FALLBACK PASS'), (':WHERE', 'A0 FALLBACK PASS'),
            ('.WHERE', 'A0 FALLBACK PASS'), ('HERE', 'LOCAL PRECEDENCE PASS'),
            (location + ':WHERE', '?'), ('MISSING', '?')]
if a.platform == 'z80pack':
    assert a.image_dir
    shutil.copytree(a.image_dir / 'disks', w / 'disks')
    shutil.copy2(a.image_dir / 'diskdefs', w / 'diskdefs')
    disk = w / 'disks/drivea.dsk'
    fmt = select_fdf(ROOT / 'third_party/montezuma/DISK.FDF',
                    'California Computer Systems (40T, DS, DD, 332K)')
    mapping = fmt.raw_record_map()
    raw = bytearray(disk.read_bytes())
    carrier = (ROOT / 'build/ccp/ccp.rlm').read_bytes().ljust(13 * 512, b'\0')
    assert len(carrier) == 13 * 512
    for i in range(len(carrier) // 128):
        track, record = divmod(108 + i, len(mapping))
        offset = (track * len(mapping) + mapping[record]) * 128
        raw[offset:offset + 128] = carrier[i * 128:(i + 1) * 128]
    disk.write_bytes(raw)
    for diskname, user, name, data in [('a', 0, 'WHERE', fallback),
            ('a', 0, 'HERE', fallback), ('b', 3, 'HERE', local)]:
        path = w / (name + '.COM')
        path.write_bytes(data)
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default',
                        str(w / f'disks/drive{diskname}.dsk'), str(path),
                        f'{user}:{name}.COM'], cwd=w, check=True)
    for i, (command, marker) in enumerate(commands):
        text = session(Path.home() / 'projects/git/z80pack/cpmsim/cpmsim',
            w / 'disks', [(b'CPX UNLOAD RCP\r', b'A0>_ ', 60),
            ((location + ':\r').encode(), (location + '>_ ').encode(), 60),
            ((command + '\r').encode(), (location + '>_ ').encode(), 60)],
            w / f'case-{i}.txt').decode(errors='replace')
        output = text.rsplit(command + ' ', 1)[-1]
        assert marker in output and 'CALLER DU WRONG' not in output, text
        if i >= 4:
            assert 'A0 FALLBACK PASS' not in output, text
else:
    disk = w / 'a.dmk'
    if not a.verify_existing:
        disk.write_bytes(medium([('WHERE.COM', fallback), ('HERE.COM', fallback),
                                ('HERE.COM', local, 3, 0)]))
    invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo',
                  '-d0', str(disk), '-id', '3500']
    invocation += keys('CPX UNLOAD RCP\r') + ['-id', '3000']
    invocation += keys(location + ':\r') + ['-id', '3000']
    for command, marker in commands:
        invocation += keys(command + '\r') + ['-id', '12000', '-it']
    invocation += ['-ix']
    if not a.verify_existing:
        run(invocation, cwd=w, timeout=600)
    for i, (command, marker) in enumerate(commands):
        text = screen(w / f'trs80-text-{i}.bin')
        (w / f'case-{i}.txt').write_text(text)
        # Successful execution reconstructs the CCP and removes its edited
        # command line. Count cumulative probe output rather than that echo.
        if i < 3:
            assert text.count('A0 FALLBACK PASS') == i + 1, text
        elif i == 3:
            assert text.count('LOCAL PRECEDENCE PASS') == 1, text
        else:
            assert '>' + command in text, text
        output = text.rsplit('>' + command, 1)[-1]
        assert marker in output and 'CALLER DU WRONG' not in output, text
        assert text.rstrip().endswith(location + '>'), text
        if i >= 4:
            assert 'A0 FALLBACK PASS' not in output, text
print(a.platform, 'six public lookup/precedence/caller-DU/exact-qualifier cases passed')
