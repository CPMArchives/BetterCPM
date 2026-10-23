#!/usr/bin/env python3
"""Execute LZH.COM -> UNLZH.COM with record-level CP/M BDOS fault injection.

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

from build_lzh import build
from build_unlzh import build as build_unlzh
from test_unlzh import decode
from test_usq import SHIM
from test_usq_com import Command, diskkey, padded


def embedded(name):
    stem, _, ext = name.partition('.')
    return (stem + '.' + ext.ljust(3)).encode()


def checked(raw, name, data):
    expected, used, rebuilds = decode(raw)
    assert expected == padded(data)
    end = raw.index(0, 2)
    assert raw[2:end] == embedded(name)
    assert raw[end:end+5] == b'\0\x20\x20\0\x05'
    assert len(raw) % 128 == 0 and raw[used:] == b'\x1a' * (-used % 128)
    return rebuilds


class LzhCommand(Command):
    def bdos(self, fn, de):
        result = super().bdos(fn, de)
        if fn == 15 and result != 255:
            # OPEN may return attribute bits in the FCB name. The command
            # must construct its embedded original name before that call.
            self.mem[de + 9] |= 0x80
        return result


def tests(lzh, unlzh):
    rng = random.Random(455)
    samples = [b'', b'A', b'\x1a', b'\x90', bytes(127), bytes(128), bytes(129),
               bytes(range(256)) * 4, b'RUN' * 6000,
               bytes(rng.randrange(256) for _ in range(17001)),
               bytes(rng.randrange(256) for _ in range(70001))]
    names = [('EMPTY', 'EMPTY.YYY'), ('ONE.A', 'ONE.AY'), ('TWO.AB', 'TWO.AY'),
             ('THREE.ABC', 'THREE.AYC'), ('A$B.BIN', 'A$B.BYN'),
             ('MID.AYC', 'MID.AYY'), ('SHORT.YY', 'SHORT.YYY'), ('NEXT.AYY', 'NEXT.YYY'),
             ('LAST.YYA', 'LAST.YYY')]
    rebuilds = 0
    for i, data in enumerate(samples):
        name, compressed = names[i % len(names)]
        src, dest = diskkey(1, name), diskkey(2, compressed)
        text = lzh.run(f' {name} B:', {src: data})
        assert 'complete' in text, (name, text)
        raw = lzh.files[dest]
        rebuilds += checked(raw, name, data)
        assert lzh.attempts['open'] == lzh.attempts['close_input'] == 1
        assert lzh.attempts['read'] == (len(data) + 127) // 128 + 1
        assert not lzh.opened and len(lzh.renamed) == 1
        lzh.intact()
        assert 'complete' in unlzh.run(f' B:{compressed} C:', {dest: raw})
        assert unlzh.files[diskkey(3, name)] == padded(data)
        assert not unlzh.opened
        unlzh.intact()
    assert rebuilds > 0
    for command, logged, source_drive, target_drive, user in (
        (' B:TEST.TXT', 1, 2, 1, 0), (' B:TEST.TXT C:', 1, 2, 3, 0),
        (' test.txt a:', 2, 2, 1, 7), ('\tTEST.TXT\tP:\t', 1, 1, 16, 0)):
        source = diskkey(source_drive, 'TEST.TXT', user)
        assert 'complete' in lzh.run(command, {source: b'drives'}, drive=logged, user=user)
        checked(lzh.files[diskkey(target_drive, 'TEST.TYT', user)], 'TEST.TXT', b'drives')
        lzh.intact()
    src, dest = diskkey(1, 'TEST.TXT'), diskkey(1, 'TEST.TYT')
    data = bytes(rng.randrange(256) for _ in range(600))
    for command in ('', ' A:', ' Q:X', ' TEST.TXT Q:', ' *.TXT', ' X?.TXT',
                    ' TOOOLONG9.TXT', ' X.LONG', ' X/Y', ' 0/X', ' TEST.TXT B: EXTRA',
                    ' TEST.TXT B', ' A..B', ' .TXT', ' TEST.TXT B:NAME'):
        assert 'Usage:' in lzh.run(command, {src: data}), command
        assert not lzh.created and not lzh.opened
        lzh.intact()
    for command in (' X.YYY', ' X.YYY B:', ' x.yyy'):
        assert 'cannot compress .YYY' in lzh.run(command, {diskkey(1, 'X.YYY'): data})
        assert not lzh.created
        lzh.intact()
    assert 'cannot open' in lzh.run(' MISSING.TXT', {})
    assert 'output exists' in lzh.run(' TEST.TXT', {src: data, dest: b'KEEP'})
    assert not lzh.created
    lzh.intact()
    temp0, temp1 = diskkey(1, 'LZU00000.$$$'), diskkey(1, 'LZU00001.$$$')
    assert 'complete' in lzh.run(' TEST.TXT', {src: data, temp0: b'KEEP0', temp1: b'KEEP1'})
    assert lzh.created == [diskkey(1, 'LZU00002.$$$')]
    lzh.intact()
    for op, nth, message in (
        ('open', 1, 'cannot open'), ('read', 1, 'read failed'), ('read', 4, 'read failed'),
        ('make', 1, 'cannot create'), ('write', 1, 'write failed'),
        ('write', 5, 'write failed'), ('close_output', 1, 'close failed'),
        ('close_input', 1, 'close failed'), ('rename', 1, 'cannot finalize')):
        text = lzh.run(' TEST.TXT', {src: data, temp0: b'KEEP'}, failures={op: nth})
        assert message in text and 'complete' not in text, (op, text)
        assert set(lzh.files) == {src, temp0} and not lzh.opened, (op, lzh.files.keys())
        lzh.intact()
    text = lzh.run(' TEST.TXT', {src: data}, late_existing=(dest, b'LATE'))
    assert 'output exists' in text and lzh.files[dest] == b'LATE'
    assert set(lzh.files) == {src, dest} and not lzh.renamed
    lzh.intact()
    text = lzh.run(' TEST.TXT', {src: data}, failures={'write': 1, 'delete': 1})
    assert 'cleanup failed' in text and temp0 in lzh.files and dest not in lzh.files
    lzh.intact()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    parser.add_argument('--z80pack', type=Path, default=Path.home() / 'projects/git/z80pack')
    parser.add_argument('--cc', default='cc')
    args = parser.parse_args()
    core = args.z80pack / 'z80core'
    with tempfile.TemporaryDirectory(prefix='bettercpm-lzh-com-') as temp:
        work = Path(temp)
        lzh_image = build(args.assembler, work)
        unlzh_image = build_unlzh(args.assembler, work)
        (work / 'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h', 'simport.h'):
            shutil.copy2(args.z80pack / 'z80sim/srcsim' / name, work / name)
        (work / 'shim.c').write_text(SHIM)
        subprocess.run([args.cc, '-shared', '-fPIC', '-O2', f'-I{work}', f'-I{core}',
                        str(work / 'shim.c'), str(core / 'simglb.c'),
                        *map(str, sorted(core.glob('simz80*.c'))), '-o', str(work / 'core.so')], check=True)
        lib = C.CDLL(str(work / 'core.so'))
        lzh = LzhCommand(lib, lzh_image, (work / 'lzh.lst').read_text(errors='replace'))
        unlzh = Command(lib, unlzh_image, (work / 'unlzh.lst').read_text(errors='replace'))
        lzh.instruction_budget = unlzh.instruction_budget = 1000000000
        tests(lzh, unlzh)
        print(f'PASS: {lzh.cases} LZH.COM cases, {unlzh.cases} UNLZH.COM round trips;')
        print('single-pass records, header/name/drive rules, faults and safe publication checked.')


if __name__ == '__main__':
    main()
