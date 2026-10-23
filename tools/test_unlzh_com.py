#!/usr/bin/env python3
"""Test UNLZH.COM on the full Z80 core with record-level CP/M fault injection.

Requires SHA-256 authenticated CrLZH 1.1/2.0 archives via --archives or build cache.
Checks original-source hashes, header metadata, safe publication and failures.
"""
import argparse
import ctypes as C
import hashlib
from pathlib import Path
import random
import shutil
import subprocess
import tempfile

from build_unlzh import build
from test_unlzh import fixture, decode, header
from test_usq import SHIM
from test_usq_com import Command, diskkey, padded

ROOT = Path(__file__).resolve().parents[1]


def compress(data, name=b'RESULT.BIN', sig=0x20):
    return fixture(list(data), sig=sig, name=name)[0]


def historical(archives):
    import struct
    from test_unlzh import ARCHIVE_HASHES
    for archive in archives:
        raw = archive.read_bytes()
        sig, count = ARCHIVE_HASHES[hashlib.sha256(raw).hexdigest()]
        found = 0
        for offset in range(32, struct.unpack_from('<H', raw, 14)[0] * 128, 32):
            e = raw[offset:offset+32]
            if e[0] != 0:
                continue
            sector, records = struct.unpack_from('<HH', e, 12)
            data = raw[sector*128:(sector+records)*128]
            if data[:2] != b'\x76\xfd':
                continue
            found += 1
            name = e[1:9].decode().rstrip() + '.' + e[9:12].decode().rstrip()
            yield name, data, sig
        assert found == count


def tests(m, corpus):
    src, dest = diskkey(1, 'TEST.BZN'), diskkey(1, 'RESULT.BIN')
    rng = random.Random(453)
    for data in (b'', b'A', b'\x1a', b'\x90', bytes(127), bytes(128), bytes(129),
                 bytes(range(256)) * 4, b'X' * 18000):
        assert 'complete' in m.run(' TEST.BZN', {src: compress(data)})
        assert m.files[dest] == padded(data)
        assert not m.opened and len(m.renamed) == 1
        m.intact()
    # Historical OUTFIL pads extensions to three slots before any metadata.
    for name, target in ((b'FILE.TXT[01/01/87]', 'FILE.TXT'),
                         (b'FILE.A  [STAMP]', 'FILE.A'),
                         (b'FILE.   [STAMP]', 'FILE'), (b'FILE.AB [STAMP]', 'FILE.AB'),
                         (b'NOEXT', 'NOEXT'), (b'file.bin', 'FILE.BIN'),
                         (b'A$B.XYZarbitrary metadata', 'A$B.XYZ')):
        assert 'complete' in m.run(' TEST.BZN', {src: compress(b'names', name)})
        assert m.files[diskkey(1, target)] == padded(b'names')
        m.intact()
    for name in (b'', b'.BIN', b'TOOLONG99.BIN', b'A..B', b'../A', b'B:OUT.BIN',
                 b'0/OUT.BIN', b'A B.BIN', b'*.BIN', b'A?.BIN', b'A\\B',
                 b'\xffNAME.BIN', b'A\x1aBIN', b'FILE.A B[STAMP]'):
        assert 'unsafe embedded filename' in m.run(' TEST.BZN', {src: compress(b'bad', name)}), name
        assert not m.created and not m.opened
        m.intact()
    for command, drive, source_drive, target_drive, user in (
        (' B:TEST.BZN', 1, 2, 1, 0), (' B:TEST.BZN C:', 1, 2, 3, 0),
        (' test.bzn a:', 2, 2, 1, 7), ('\tTEST.BZN\tP:\t', 1, 1, 16, 0)):
        source = diskkey(source_drive, 'TEST.BZN', user)
        assert 'complete' in m.run(command, {source: compress(b'drives')}, drive=drive, user=user)
        assert m.files[diskkey(target_drive, 'RESULT.BIN', user)] == padded(b'drives')
        m.intact()
    for command in ('', ' A:', ' Q:TEST.BZN', ' TEST.BZN Q:', ' *.BZN', ' X?.BZN',
                    ' TOOLONG99.BZN', ' X.LONG', ' X/Y', ' 0/X', ' TEST.BZN B: EXTRA',
                    ' TEST.BZN B', ' A..B', ' .BZN', ' TEST.BZN B:NAME'):
        assert 'Usage:' in m.run(command, {src: compress(b'parser')})
        assert not m.created
        m.intact()
    assert 'cannot open' in m.run(' MISSING.BZN', {})
    assert 'replace input' in m.run(' TEST.BZN', {src: compress(b'same', b'TEST.BZN')})
    m.intact()
    data = bytes(rng.randrange(256) for _ in range(600))
    raw = compress(data)
    assert 'output exists' in m.run(' TEST.BZN', {src: raw, dest: b'KEEP'})
    m.intact()
    temp0, temp1 = diskkey(1, 'ULZ00000.$$$'), diskkey(1, 'ULZ00001.$$$')
    assert 'complete' in m.run(' TEST.BZN', {src: raw, temp0: b'KEEP0', temp1: b'KEEP1'})
    assert m.created == [diskkey(1, 'ULZ00002.$$$')]
    m.intact()
    assert 'complete' in m.run(' TEST.BZN', {src: compress(data, b'ULZ00000.$$$')})
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
    for sig, check in ((0, 0), (0x21, 0), (0x10, 1), (0x20, 1)):
        assert 'unsupported CrLZH variant' in m.run(' TEST.BZN', {src: header(sig=sig, check=check)})
        assert not m.created
        m.intact()
    assert 'invalid or truncated' in m.run(' TEST.BZN', {src: b'not compressed'})
    assert not m.created
    # Full records of zero bits are malformed input; no output may be published.
    bad = header() + bytes(256 - len(header()))
    text = m.run(' TEST.BZN', {src: bad})
    assert 'invalid or truncated' in text or 'checksum mismatch' in text
    assert set(m.files) == {src} and not m.opened
    m.intact()
    assert 'header exceeds 127 bytes' in m.run(' TEST.BZN', {src: header(name=b'A' * 128)})
    assert not m.created
    m.intact()
    count = 0
    for name, raw, sig in historical(corpus):
        expected, _, _ = decode(raw)
        source = diskkey(1, name)
        text = m.run(f' {name} B:', {source: raw})
        embedded_raw = raw[2:raw.index(0, 2)]
        if any(b >= 128 for b in embedded_raw.split(b'.', 1)[0] + embedded_raw.split(b'.', 1)[-1][:3]):
            assert 'unsafe embedded filename' in text, (name, text)
            assert not m.created and set(m.files) == {source}
            m.intact()
            count += 1
            continue
        assert 'complete' in text, (name, text, embedded_raw)
        embedded = raw[2:raw.index(0, 2)].decode('latin1')
        stem, dot, extension = embedded.partition('.')
        target = stem + ('.' + extension[:3].rstrip() if dot and extension[:3].rstrip() else '')
        assert m.files[diskkey(2, target)] == padded(expected), name
        assert not m.opened
        m.intact()
        count += 1
    for sig in (0x10, 0x20):
        raw, expected, _ = fixture([65, (60, 1)] * 1200, sig=sig, name=b'RESULT.BIN')
        assert 'complete' in m.run(' TEST.BZN', {src: raw})
        assert m.files[dest] == padded(expected)
        m.intact()
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    parser.add_argument('--z80pack', type=Path, default=Path.home() / 'projects/git/z80pack')
    parser.add_argument('--archives', type=Path, nargs=2, default=[ROOT / 'build/test-fixtures/crlzh' / n for n in ('crlzh11.lbr', 'crlzh20.lbr')])
    parser.add_argument('--cc', default='cc')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='bettercpm-unlzh-com-') as temp:
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
                    (work / 'unlzh.lst').read_text(errors='replace'))
        m.instruction_budget = 1000000000
        count = tests(m, args.archives)
        print(f'PASS: {m.cases} UNLZH.COM cases, including {count} historical files (unsafe names refused);')
        print('record I/O, metadata, drives, faults, cleanup and original-file preservation checked.')


if __name__ == '__main__':
    main()
