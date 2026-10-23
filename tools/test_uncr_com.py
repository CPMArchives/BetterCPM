#!/usr/bin/env python3
"""Test UNCR.COM on the full Z80 core with record-level CP/M fault injection.

Historical corpus requires the compatibility suite sibling or --corpus.
Checks original-source hashes, header metadata, safe publication and failures.
"""
import argparse
import csv
import ctypes as C
import hashlib
from pathlib import Path
import random
import shutil
import subprocess
import tempfile

from build_uncr import build
from test_uncr import fixture, decode, header
from test_usq import SHIM
from test_usq_com import Command, diskkey, padded

ROOT = Path(__file__).resolve().parents[1]


def crunch(data, name=b'RESULT.BIN'):
    codes = []
    for b in data:
        codes.extend([144, 0] if b == 144 else [b])
    return fixture(codes + [256], name)[0]


def tests(m, corpus):
    src, dest = diskkey(1, 'TEST.BZN'), diskkey(1, 'RESULT.BIN')
    rng = random.Random(453)
    for data in (b'', b'A', b'\x1a', b'\x90', bytes(127), bytes(128), bytes(129),
                 bytes(range(256)) * 4, b'X' * 18000):
        assert 'complete' in m.run(' TEST.BZN', {src: crunch(data)})
        assert m.files[dest] == padded(data)
        assert not m.opened and len(m.renamed) == 1
        m.intact()
    # Historical OUTFIL pads extensions to three slots before any metadata.
    for name, target in ((b'FILE.TXT[01/01/87]', 'FILE.TXT'),
                         (b'FILE.A  [STAMP]', 'FILE.A'),
                         (b'FILE.   [STAMP]', 'FILE'), (b'FILE.AB [STAMP]', 'FILE.AB'),
                         (b'NOEXT', 'NOEXT'), (b'file.bin', 'FILE.BIN'),
                         (b'A$B.XYZarbitrary metadata', 'A$B.XYZ')):
        assert 'complete' in m.run(' TEST.BZN', {src: crunch(b'names', name)})
        assert m.files[diskkey(1, target)] == padded(b'names')
        m.intact()
    for name in (b'', b'.BIN', b'TOOLONG99.BIN', b'A..B', b'../A', b'B:OUT.BIN',
                 b'0/OUT.BIN', b'A B.BIN', b'*.BIN', b'A?.BIN', b'A\\B',
                 b'\xffNAME.BIN', b'A\x1aBIN', b'FILE.A B[STAMP]'):
        assert 'unsafe embedded filename' in m.run(' TEST.BZN', {src: crunch(b'bad', name)}), name
        assert not m.created and not m.opened
        m.intact()
    for command, drive, source_drive, target_drive, user in (
        (' B:TEST.BZN', 1, 2, 1, 0), (' B:TEST.BZN C:', 1, 2, 3, 0),
        (' test.bzn a:', 2, 2, 1, 7), ('\tTEST.BZN\tP:\t', 1, 1, 16, 0)):
        source = diskkey(source_drive, 'TEST.BZN', user)
        assert 'complete' in m.run(command, {source: crunch(b'drives')}, drive=drive, user=user)
        assert m.files[diskkey(target_drive, 'RESULT.BIN', user)] == padded(b'drives')
        m.intact()
    for command in ('', ' A:', ' Q:TEST.BZN', ' TEST.BZN Q:', ' *.BZN', ' X?.BZN',
                    ' TOOLONG99.BZN', ' X.LONG', ' X/Y', ' 0/X', ' TEST.BZN B: EXTRA',
                    ' TEST.BZN B', ' A..B', ' .BZN', ' TEST.BZN B:NAME'):
        assert 'Usage:' in m.run(command, {src: crunch(b'parser')})
        assert not m.created
        m.intact()
    assert 'cannot open' in m.run(' MISSING.BZN', {})
    assert 'replace input' in m.run(' TEST.BZN', {src: crunch(b'same', b'TEST.BZN')})
    m.intact()
    data = bytes(rng.randrange(256) for _ in range(600))
    raw = crunch(data)
    assert 'output exists' in m.run(' TEST.BZN', {src: raw, dest: b'KEEP'})
    m.intact()
    temp0, temp1 = diskkey(1, 'UCR00000.$$$'), diskkey(1, 'UCR00001.$$$')
    assert 'complete' in m.run(' TEST.BZN', {src: raw, temp0: b'KEEP0', temp1: b'KEEP1'})
    assert m.created == [diskkey(1, 'UCR00002.$$$')]
    m.intact()
    assert 'complete' in m.run(' TEST.BZN', {src: crunch(data, b'UCR00000.$$$')})
    assert m.created == [temp1] and m.files[temp0] == padded(data)
    for op, nth, message in (
        ('open', 1, 'cannot open'), ('make', 1, 'cannot create'),
        ('read', 1, 'read failed'), ('read', 4, 'read failed'),
        ('write', 1, 'write failed'), ('write', 5, 'write failed'),
        ('close_input', 1, 'close failed'), ('close_output', 1, 'close failed'),
        ('rename', 1, 'cannot finalize')):
        text = m.run(' TEST.BZN', {src: raw, temp0: b'KEEP'}, failures={op: nth})
        assert message in text and 'complete' not in text, (op, text)
        assert set(m.files) == {src, temp0} and not m.opened
        m.intact()
    bad = bytearray(raw); bad[-1] ^= 1
    assert 'checksum mismatch' in m.run(' TEST.BZN', {src: bytes(bad)})
    assert set(m.files) == {src} and not m.opened
    m.intact()
    text = m.run(' TEST.BZN', {src: bytes(bad)}, failures={'delete': 1})
    assert 'cleanup failed' in text and set(m.files) == {src, temp0}
    m.intact()
    text = m.run(' TEST.BZN', {src: raw}, late_existing=(dest, b'LATE'))
    assert 'output exists' in text and m.files[dest] == b'LATE'
    assert set(m.files) == {src, dest} and not m.renamed
    m.intact()
    for info in (b'\x24\x10\0\x05', b'\x28\x21\0\0', b'\x24\x20\1\0'):
        assert 'unsupported crunch variant' in m.run(' TEST.BZN', {src: header(info=info)})
        assert not m.created
        m.intact()
    for bad in (b'not crunched', header() + b'\xff\xff',
                fixture([144, 256], validate=False)[0]):
        assert 'invalid or truncated crunched file' in m.run(' TEST.BZN', {src: bad})
        assert set(m.files) == {src}
        m.intact()
    # Whole records with zero bits encode only NUL bytes, no encoded EOF.
    bad = header() + bytes(256 - len(header()))
    assert 'invalid or truncated' in m.run(' TEST.BZN', {src: bad})
    assert set(m.files) == {src} and not m.opened
    m.intact()
    assert 'header exceeds 127 bytes' in m.run(' TEST.BZN', {src: header(b'A' * 128)})
    assert not m.created
    m.intact()
    with (corpus / 'MANIFEST.tsv').open() as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    for row in rows:
        name = row['utility'] + '.MZC'
        raw = (corpus / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['mzc_sha256']
        expected, _, _ = decode(raw)
        source = diskkey(1, name)
        assert 'complete' in m.run(f' {name} B:', {source: raw})
        decoded_name = raw[2:raw.index(0, 2)].decode().rstrip()
        result = m.files[diskkey(2, decoded_name)]
        assert result == padded(expected)
        size = int(row['mac_size'])
        assert hashlib.sha256(result[:size]).hexdigest() == row['mac_sha256']
        assert not m.opened
        m.intact()
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    parser.add_argument('--z80pack', type=Path, default=Path.home() / 'projects/git/z80pack')
    parser.add_argument('--corpus', type=Path, default=ROOT.parent / 'cpm-2.2-compatibility-suite/suite/crunched-source')
    parser.add_argument('--cc', default='cc')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='bettercpm-uncr-com-') as temp:
        work = Path(temp)
        image = build(args.assembler, work)
        (work / 'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h', 'simport.h'):
            shutil.copy2(args.z80pack / 'z80sim/srcsim' / name, work / name)
        (work / 'shim.c').write_text(SHIM)
        core = args.z80pack / 'z80core'
        subprocess.run([args.cc, '-shared', '-fPIC', '-O2', f'-I{work}', f'-I{core}',
                        str(work / 'shim.c'), str(core / 'simglb.c'),
                        *map(str, sorted(core.glob('simz80*.c'))), '-o', str(work / 'core.so')], check=True)
        m = Command(C.CDLL(str(work / 'core.so')), image,
                    (work / 'uncr.lst').read_text(errors='replace'))
        m.instruction_budget = 1000000000
        count = tests(m, args.corpus)
        print(f'PASS: {m.cases} UNCR.COM cases, including {count} historical files;')
        print('record I/O, metadata, drives, faults, cleanup and original-file preservation checked.')


if __name__ == '__main__':
    main()
