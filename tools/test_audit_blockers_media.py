#!/usr/bin/env python3
"""Verify BCPM-AUD-001/002 on private cpmsim media, retaining evidence.

Requires a freshly built default-layout RAM System image and common builders.
Never writes the supplied image. Run the boundary-value host tests separately.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module
from build_system_package import compose
from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('image', 'diskdefs', 'simulator', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    a = p.parse_args()
    image, out = a.image.resolve(), a.output.resolve()
    original = sha(image)
    out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(a.diskdefs, out / 'diskdefs')
    disks = out / 'disks'
    disks.mkdir()
    disk = disks / 'drivea.dsk'
    shutil.copy2(image, disk)
    for letter in 'bcd':
        (disks / f'drive{letter}.dsk').write_bytes(b'\xE5' * image.stat().st_size)

    source = '''        ORG 100H
        LD C,13
        CALL 5
        LD DE,FCB
        LD C,19
        CALL 5
        CP 255
        LD DE,BAD
        JR NZ,PRINT
        LD DE,OK
PRINT:  LD C,9
        CALL 5
        JP 0
FCB:    DB 5,'TARGET  DAT'
        DS 24
OK:     DB 'Unsupported E: DELETE rejected',13,10,'$'
BAD:    DB 'FAIL: unsupported E: DELETE accepted',13,10,'$'
        END
'''
    (out / 'drive5.mac').write_text(source)
    assemble(a.assembler, source, out / 'DRIVE5.COM', out / 'drive5.lst', 0x100)
    target = out / 'TARGET.DAT'
    target.write_bytes(b'INVALID DRIVE MUST NOT DELETE THIS FILE\r\n'.ljust(128, b'\x1A'))
    code = (ROOT / 'build/rsx/hello.bin').read_bytes()
    alternate = (ROOT / 'build/rsx/hello-alt.bin').read_bytes()
    # Same supported stateless carrier as HELLO; only its reserved size grows.
    # Default layout places the resulting protected gateway at 8001h.
    (out / 'BIGMEM.RSX').write_bytes(make_module(
        name='BIGMEM', version=(0, 1), services=[198], linked_base=0x8000,
        code=code, relocations=relocation_offsets(code, alternate, 0x101),
        allocation=0x5100))
    for name, path in [('DRIVE5.COM', out / 'DRIVE5.COM'),
                       ('TARGET.DAT', target), ('BIGMEM.RSX', out / 'BIGMEM.RSX'),
                       ('SYSBUILD.COM', ROOT / 'build/utilities/SYSBUILD.COM'),
                       ('RLMBUILD.COM', ROOT / 'build/utilities/RLMBUILD.COM')]:
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(disk),
                        str(path), '0:' + name], cwd=out, check=True)
    before = sha(disk)
    commands = []

    def command(text, expected):
        commands.extend([(text.encode() + b'\r', expected, 30),
                         (b'', b'\r\nA0>', 30)])

    command('DRIVE5', b'Unsupported E: DELETE rejected')
    command('RSX LOAD BIGMEM', b'BIGMEM')
    command('STAT MEM', b'8001')
    command('SYSBUILD', b'SYSBUILD: insufficient active TPA.')
    command('RLMBUILD', b'RLMBUILD: insufficient active TPA.')
    command('SYSBUILD /VER', b'SYSBUILD 1.0')
    command('RLMBUILD /HELP', b'RLMBUILD')
    command('RSX LIST', b'BIGMEM')
    command('STAT MEM', b'8001')
    trace = session(a.simulator.resolve(), disks, commands, out / 'transcript.bin')
    (out / 'transcript.txt').write_text(trace.decode('latin1'))
    assert b'FAIL:' not in trace, trace
    subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(disk),
                    '0:TARGET.DAT', str(out / 'retained.dat')], cwd=out, check=True)
    assert (out / 'retained.dat').read_bytes() == target.read_bytes()
    assert sha(disk) == before, 'unexpected writes to disposable System disk'
    # A fresh boot restores the ordinary TPA. Exercise both complete successful
    # builders on expendable B:, comparing output to independent host packers.
    package, parts = compose()
    parts.update({
        'CCPBASE.BIN': (ROOT / 'build/ccp/ccp.bin').read_bytes(),
        'CCPALT.BIN': (ROOT / 'build/ccp/ccp-alt.bin').read_bytes(),
        'CCPCHK.BIN': (ROOT / 'build/ccp/ccp-check.bin').read_bytes(),
    })
    for name, data in parts.items():
        path = out / name
        path.write_bytes(data)
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default',
                        str(disks / 'driveb.dsk'), str(path), '0:' + name],
                       cwd=out, check=True)
    positive = session(a.simulator.resolve(), disks, [
        (b'B:\r', b'\r\nB0>', 30),
        (b'A:RLMBUILD\r', b'CCP.RLM created and verified.', 30),
        (b'', b'\r\nB0>', 30),
        (b'A:SYSBUILD\r', b'SYSTEM.SYS created and verified', 30),
        (b'', b'\r\nB0>', 30),
    ], out / 'positive-transcript.bin')
    (out / 'positive-transcript.txt').write_text(positive.decode('latin1'))
    for name, expected in [('CCP.RLM', parts['CCP.RLM']), ('SYSTEM.SYS', package)]:
        actual = out / ('created-' + name)
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(disks / 'driveb.dsk'),
                        '0:' + name, str(actual)], cwd=out, check=True)
        # Native sequential output is padded to a complete CP/M record.
        assert actual.read_bytes() == expected.ljust((len(expected) + 127) // 128 * 128, b'\0'), name
    assert sha(disk) == before, 'successful builders unexpectedly modified A:'
    assert sha(image) == original, 'input image changed'
    report = {'status': 'PASS', 'input_sha256': original,
              'fixture_disk_sha256': before, 'after_sha256': sha(disk),
              'target_retained': True, 'disk_unchanged': True,
              'normal_tpa_outputs_match_host': ['CCP.RLM', 'SYSTEM.SYS'],
              'commands': [x[0].decode().strip() for x in commands if x[0]],
              'scope': 'default-layout RAM cpmsim, invalid E: delete and admitted low-TPA RSX; not Model 4 runtime qualification'}
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: invalid E: delete rejected; low-TPA builders/queries return; RSX and disk intact')


if __name__ == '__main__':
    main()
