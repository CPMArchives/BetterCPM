#!/usr/bin/env python3
"""Execute CR.COM -> UNCR.COM with record-level CP/M BDOS fault injection.

Checks single-pass reads, historical naming and padded embedded names, drives,
existing-file protection, temporary ownership, returned errors and publication.
Both commands run on the full Z80 core; host decoder checks the wire stream.
"""
import argparse
import ctypes as C
from pathlib import Path
import random
import shutil
import subprocess
import tempfile

from build_cr import build
from build_uncr import build as build_uncr
from test_uncr import decode
from test_usq import SHIM
from test_usq_com import Command, diskkey, padded


def embedded(name):
    stem, _, ext = name.partition('.')
    return (stem + '.' + ext.ljust(3)).encode()


def checked(raw, name, data):
    expected, used, model = decode(raw)
    assert expected == padded(data)
    assert raw[2:raw.index(0, 2)] == embedded(name)
    assert len(raw) % 128 == 0 and raw[used:] == b'\x1a' * (-used % 128)
    return model


class CrunchCommand(Command):
    def bdos(self, fn, de):
        result = super().bdos(fn, de)
        if fn == 15 and result != 255:
            # OPEN may return attribute bits in the FCB name. The command
            # must construct its embedded original name before that call.
            self.mem[de + 9] |= 0x80
        return result


def tests(cr, uncr):
    rng = random.Random(455)
    samples = [b'', b'A', b'\x1a', b'\x90', bytes(127), bytes(128), bytes(129),
               bytes(range(256)) * 4, b'RUN' * 6000,
               bytes(rng.randrange(256) for _ in range(17001)),
               bytes(rng.randrange(256) for _ in range(70001))]
    names = [('EMPTY', 'EMPTY.ZZZ'), ('ONE.A', 'ONE.AZ'), ('TWO.AB', 'TWO.AZ'),
             ('THREE.ABC', 'THREE.AZC'), ('A$B.BIN', 'A$B.BZN'),
             ('MID.AZC', 'MID.ZZZ'), ('SHORT.ZZ', 'SHORT.ZZZ')]
    resets = 0
    for i, data in enumerate(samples):
        name, crunched = names[i % len(names)]
        src, dest = diskkey(1, name), diskkey(2, crunched)
        text = cr.run(f' {name} B:', {src: data})
        assert 'complete' in text, (name, text)
        raw = cr.files[dest]
        resets += checked(raw, name, data).resets - 1
        assert cr.attempts['open'] == cr.attempts['close_input'] == 1
        assert cr.attempts['read'] == (len(data) + 127) // 128 + 1
        assert not cr.opened and len(cr.renamed) == 1
        cr.intact()
        assert 'complete' in uncr.run(f' B:{crunched} C:', {dest: raw})
        assert uncr.files[diskkey(3, name)] == padded(data)
        assert not uncr.opened
        uncr.intact()
    assert resets > 1
    for command, logged, source_drive, target_drive, user in (
        (' B:TEST.TXT', 1, 2, 1, 0), (' B:TEST.TXT C:', 1, 2, 3, 0),
        (' test.txt a:', 2, 2, 1, 7), ('\tTEST.TXT\tP:\t', 1, 1, 16, 0)):
        source = diskkey(source_drive, 'TEST.TXT', user)
        assert 'complete' in cr.run(command, {source: b'drives'}, drive=logged, user=user)
        checked(cr.files[diskkey(target_drive, 'TEST.TZT', user)], 'TEST.TXT', b'drives')
        cr.intact()
    src, dest = diskkey(1, 'TEST.TXT'), diskkey(1, 'TEST.TZT')
    data = bytes(rng.randrange(256) for _ in range(600))
    for command in ('', ' A:', ' Q:X', ' TEST.TXT Q:', ' *.TXT', ' X?.TXT',
                    ' TOOOLONG9.TXT', ' X.LONG', ' X/Y', ' 0/X', ' TEST.TXT B: EXTRA',
                    ' TEST.TXT B', ' A..B', ' .TXT', ' TEST.TXT B:NAME'):
        assert 'Usage:' in cr.run(command, {src: data}), command
        assert not cr.created and not cr.opened
        cr.intact()
    for command in (' X.ZZZ', ' X.ZZZ B:', ' x.zzz'):
        assert 'cannot crunch .ZZZ' in cr.run(command, {diskkey(1, 'X.ZZZ'): data})
        assert not cr.created
        cr.intact()
    assert 'cannot open' in cr.run(' MISSING.TXT', {})
    assert 'output exists' in cr.run(' TEST.TXT', {src: data, dest: b'KEEP'})
    assert not cr.created
    cr.intact()
    temp0, temp1 = diskkey(1, 'CRU00000.$$$'), diskkey(1, 'CRU00001.$$$')
    assert 'complete' in cr.run(' TEST.TXT', {src: data, temp0: b'KEEP0', temp1: b'KEEP1'})
    assert cr.created == [diskkey(1, 'CRU00002.$$$')]
    cr.intact()
    for op, nth, message in (
        ('open', 1, 'cannot open'), ('read', 1, 'read failed'), ('read', 4, 'read failed'),
        ('make', 1, 'cannot create'), ('write', 1, 'write failed'),
        ('write', 5, 'write failed'), ('close_output', 1, 'close failed'),
        ('close_input', 1, 'close failed'), ('rename', 1, 'cannot finalize')):
        text = cr.run(' TEST.TXT', {src: data, temp0: b'KEEP'}, failures={op: nth})
        assert message in text and 'complete' not in text, (op, text)
        assert set(cr.files) == {src, temp0} and not cr.opened, (op, cr.files.keys())
        cr.intact()
    text = cr.run(' TEST.TXT', {src: data}, late_existing=(dest, b'LATE'))
    assert 'output exists' in text and cr.files[dest] == b'LATE'
    assert set(cr.files) == {src, dest} and not cr.renamed
    cr.intact()
    text = cr.run(' TEST.TXT', {src: data}, failures={'write': 1, 'delete': 1})
    assert 'cleanup failed' in text and temp0 in cr.files and dest not in cr.files
    cr.intact()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    parser.add_argument('--z80pack', type=Path, default=Path.home() / 'projects/git/z80pack')
    parser.add_argument('--cc', default='cc')
    args = parser.parse_args()
    core = args.z80pack / 'z80core'
    with tempfile.TemporaryDirectory(prefix='bettercpm-cr-com-') as temp:
        work = Path(temp)
        cr_image = build(args.assembler, work)
        uncr_image = build_uncr(args.assembler, work)
        (work / 'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h', 'simport.h'):
            shutil.copy2(args.z80pack / 'z80sim/srcsim' / name, work / name)
        (work / 'shim.c').write_text(SHIM)
        subprocess.run([args.cc, '-shared', '-fPIC', '-O2', f'-I{work}', f'-I{core}',
                        str(work / 'shim.c'), str(core / 'simglb.c'),
                        *map(str, sorted(core.glob('simz80*.c'))), '-o', str(work / 'core.so')], check=True)
        lib = C.CDLL(str(work / 'core.so'))
        cr = CrunchCommand(lib, cr_image, (work / 'cr.lst').read_text(errors='replace'))
        uncr = Command(lib, uncr_image, (work / 'uncr.lst').read_text(errors='replace'))
        cr.instruction_budget = uncr.instruction_budget = 1000000000
        tests(cr, uncr)
        print(f'PASS: {cr.cases} CR.COM cases, {uncr.cases} UNCR.COM round trips;')
        print('single-pass records, header/name/drive rules, faults and safe publication checked.')


if __name__ == '__main__':
    main()
