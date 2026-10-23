#!/usr/bin/env python3
"""Exercise SQ.COM and USQ.COM with full Z80 execution and BDOS fault injection.

The model poisons the input FCB after close, requiring a complete rewind reset.
Both commands execute for every success case; an independent decoder checks
header names, checksum, encoded EOF and final-record padding as well.
"""
import ctypes as C
import random
from pathlib import Path
import argparse
import shutil
import subprocess
import tempfile

from build_sq import build
from build_usq import build as build_usq
from test_usq import SHIM
from test_usq_com import Command, diskkey, padded
from test_sq import host_decode


class SqueezeCommand(Command):
    instruction_budget = 300000000

    def bdos(self, fn, de):
        if fn == 15 and de == self.symbols['UC_INPUT']:
            assert not any(self.mem[de + 12:de + 36]), 'rewind FCB state not reset'
            if self.attempts.get('open', 0) == 1 and getattr(self, 'changed', None) is not None:
                self.files[self.fcbkey(de)] = self.changed
        result = super().bdos(fn, de)
        if fn == 16 and de == self.symbols['UC_INPUT'] and result != 255:
            self.mem[de + 12:de + 36] = bytes([0xA5]) * 24
        return result


def tests(sq, usq):
    rng = random.Random(450)
    samples = [b'', b'A', b'\x1a', b'\x90', bytes(127), b'X' * 128,
               b'Y' * 129, bytes(range(256)) * 4, b'RUN' * 6000,
               bytes(rng.randrange(256) for _ in range(17001)),
               bytes(range(256)) * 260]
    names = [('EMPTY', 'EMPTY.QQQ'), ('ONE.A', 'ONE.AQ'), ('TWO.AB', 'TWO.AQ'),
             ('THREE.XYZ', 'THREE.XQZ'), ('A$B.BIN', 'A$B.BQN')]
    for i, data in enumerate(samples):
        source_name, squeezed = names[i % len(names)]
        src, dest = diskkey(1, source_name), diskkey(2, squeezed)
        text = sq.run(f' {source_name} B:', {src: data})
        assert 'complete' in text, (source_name, text)
        raw = sq.files[dest]
        assert host_decode(raw, record_padding=True) == (source_name.encode(), padded(data))
        assert sq.attempts['open'] == sq.attempts['close_input'] == 2
        assert not sq.opened and len(sq.renamed) == 1
        sq.intact()
        assert 'complete' in usq.run(f' B:{squeezed} C:', {dest: raw})
        assert usq.files[diskkey(3, source_name)] == padded(data)
        usq.intact()
    for command, logged, source_drive, target_drive, user in (
        (' B:TEST.TXT', 1, 2, 1, 0), (' B:TEST.TXT C:', 1, 2, 3, 0),
        (' test.txt a:', 2, 2, 1, 7), ('\tTEST.TXT\tP:\t', 1, 1, 16, 0)):
        src = diskkey(source_drive, 'TEST.TXT', user)
        assert 'complete' in sq.run(command, {src: b'drives'}, drive=logged, user=user)
        assert host_decode(sq.files[diskkey(target_drive, 'TEST.TQT', user)], True)[1] == padded(b'drives')
        sq.intact()
    src, dest = diskkey(1, 'TEST.TXT'), diskkey(1, 'TEST.TQT')
    data = bytes(rng.randrange(256) for _ in range(600))
    for command in ('', ' A:', ' Q:X', ' TEST.TXT Q:', ' *.TXT', ' X?.TXT',
                    ' TOOOLONG9.TXT', ' X.LONG', ' X/Y', ' 0/X', ' TEST.TXT B: EXTRA',
                    ' TEST.TXT B', ' A..B', ' .TXT', ' TEST.TXT B:NAME'):
        assert 'Usage:' in sq.run(command, {src: data}), command
        assert not sq.created and not sq.opened
        sq.intact()
    for name in ('TEST.TQT', 'X.QQ', 'X.AQ', 'X.AQZ'):
        assert 'already squeezed' in sq.run(f' {name}', {diskkey(1, name): data})
        assert not sq.created
        sq.intact()
    assert 'cannot open' in sq.run(' MISSING.TXT', {})
    assert 'output exists' in sq.run(' TEST.TXT', {src: data, dest: b'KEEP'})
    sq.intact()
    temp0, temp1 = diskkey(1, 'SQU00000.$$$'), diskkey(1, 'SQU00001.$$$')
    assert 'complete' in sq.run(' TEST.TXT', {src: data, temp0: b'KEEP0', temp1: b'KEEP1'})
    assert sq.created == [diskkey(1, 'SQU00002.$$$')]
    sq.intact()
    for op, nth, message in (
        ('open', 1, 'cannot open'), ('open', 2, 'cannot reopen'),
        ('close_input', 1, 'cannot reopen'), ('close_input', 2, 'close failed'),
        ('read', 1, 'read failed'), ('read', 7, 'read failed'),
        ('make', 1, 'cannot create'), ('write', 1, 'write failed'),
        ('write', 5, 'write failed'), ('close_output', 1, 'close failed'),
        ('rename', 1, 'cannot finalize')):
        text = sq.run(' TEST.TXT', {src: data, temp0: b'KEEP'}, failures={op: nth})
        assert message in text and 'complete' not in text, (op, nth, text)
        assert set(sq.files) == {src, temp0} and not sq.opened, (op, sq.files.keys())
        if (op, nth) in [('open', 2), ('close_input', 1), ('read', 1)]:
            assert not sq.created
        sq.intact()
    text = sq.run(' TEST.TXT', {src: data}, late_existing=(dest, b'LATE'))
    assert 'output exists' in text and sq.files[dest] == b'LATE'
    assert set(sq.files) == {src, dest} and not sq.renamed
    sq.intact()
    sq.changed = b'changed input'
    text = sq.run(' TEST.TXT', {src: data})
    assert 'input changed' in text and dest not in sq.files and not sq.opened, text
    sq.changed = None
    text = sq.run(' TEST.TXT', {src: data}, failures={'write': 1, 'delete': 1})
    assert 'cleanup failed' in text and temp0 in sq.files and dest not in sq.files
    sq.intact()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    parser.add_argument('--z80pack', type=Path, default=Path.home() / 'projects/git/z80pack')
    parser.add_argument('--cc', default='cc')
    args = parser.parse_args()
    core = args.z80pack / 'z80core'
    with tempfile.TemporaryDirectory(prefix='bettercpm-sq-com-') as temporary:
        work = Path(temporary)
        sq_image = build(args.assembler, work)
        usq_image = build_usq(args.assembler, work)
        (work / 'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h', 'simport.h'):
            shutil.copy2(args.z80pack / 'z80sim/srcsim' / name, work / name)
        (work / 'shim.c').write_text(SHIM)
        subprocess.run([args.cc, '-shared', '-fPIC', '-O2', f'-I{work}', f'-I{core}',
                        str(work / 'shim.c'), str(core / 'simglb.c'),
                        *map(str, sorted(core.glob('simz80*.c'))), '-o', str(work / 'core.so')], check=True)
        lib = C.CDLL(str(work / 'core.so'))
        sq = SqueezeCommand(lib, sq_image, (work / 'sq.lst').read_text(errors='replace'))
        usq = Command(lib, usq_image, (work / 'usq.lst').read_text(errors='replace'))
        usq.instruction_budget = 300000000
        tests(sq, usq)
        print(f'PASS: {sq.cases} SQ.COM cases, {usq.cases} USQ.COM round trips;')
        print('two-pass FCB reset, record I/O, names, drives, faults and safe publication checked.')


if __name__ == '__main__':
    main()
