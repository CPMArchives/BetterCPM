#!/usr/bin/env python3
"""Execute UNCR on full z80pack Z80 core, with independent stream fixtures.

Historical CRUNCH 2.4 corpus is read-only from the sibling compatibility suite
(or --corpus). Tests build temporary code/core, never modify emulator media.
Requires z80asm, a C compiler and z80pack sources. No third-party code vendored.
"""
import argparse
import ctypes as C
import csv
import hashlib
from pathlib import Path
import random
import shutil
import struct
import subprocess
import tempfile

from test_usq import SHIM, Machine

ROOT = Path(__file__).resolve().parents[1]
SIZE = 26582
ENTRIES = ('UNCR_INIT', 'UNCR_HEAD', 'UNCR_GET', 'UNCR_RUN', 'UNCR_END',
           'READ_CB', 'WRITE_CB')


class Model:
    """Independent index/string model of CRUNCH-20 dictionary and hash slots."""
    def __init__(self):
        self.widths, self.resets, self.reassigned, self.special = set(), 0, 0, 0
        self.deepest = 0
        self.reset()

    def reset(self):
        self.width, self.previous = 9, None
        self.table, self.referenced = [], set()
        self.slots = {0: -1}
        for b in range(256):
            self.add(0xFFFF, b, bytes([b]), True)
        for _ in range(4):
            self.add(0x7FFF, 0, None, True)
        self.resets += 1

    def probes(self, pred, suffix):
        h = ((((pred >> 4) ^ suffix) & 255) | ((pred & 15) << 8)) + 1
        for i in range(5003):
            yield (h + i * h) % 5003
        raise ValueError('hash cycle')

    def add(self, pred, suffix, phrase, ref=False):
        code = len(self.table)
        slot = next(slot for slot in self.probes(pred, suffix) if slot not in self.slots)
        self.slots[slot] = code
        self.table.append(phrase)
        if ref:
            self.referenced.add(code)
        if self.width < 12 and len(self.table) >= (1 << self.width) - 1:
            self.width += 1

    def accept(self, code):
        self.widths.add(self.width)
        if code == 256:
            return None
        if code == 257:
            self.reset()
            return b''
        if code in (258, 259):
            return b''
        previous = self.previous
        special = code == len(self.table)
        if special:
            if previous is None or len(self.table) == 4096:
                raise ValueError('undefined code')
            phrase = self.table[previous] + self.table[previous][:1]
            self.add(previous, phrase[0], phrase, True)
            self.special += 1
        elif code >= len(self.table) or self.table[code] is None:
            raise ValueError('bad code')
        phrase = self.table[code]
        self.referenced.add(code)
        self.deepest = max(self.deepest, len(phrase))
        if previous is not None and not special:
            entry = self.table[previous] + phrase[:1]
            if len(self.table) < 4096:
                self.add(previous, phrase[0], entry)
            else:
                for slot in self.probes(previous, phrase[0]):
                    if slot not in self.slots:
                        break
                    candidate = self.slots[slot]
                    if candidate >= 0 and candidate not in self.referenced:
                        self.table[candidate] = entry
                        self.reassigned += 1
                        break
        self.previous = code
        return phrase


def expand(tokens):
    output = bytearray()
    escape, last = False, None
    for b in tokens:
        if escape:
            escape = False
            if b == 0:
                output.append(0x90)  # historical SEND preserves earlier history
            else:
                if b < 2 or last is None:
                    raise ValueError('invalid repeat')
                output.extend(bytes([last]) * (b - 1))
        elif b == 0x90:
            escape = True
        else:
            output.append(b)
            last = b
    if escape:
        raise ValueError('unfinished escape')
    return bytes(output)


def header(name=b'TEST.BIN', info=b'\x24\x20\0\x05'):
    return b'\x76\xfe' + name + b'\0' + info


def fixture(codes, name=b'TEST.BIN', validate=True):
    model = Model()
    bits, tokens = [], bytearray()
    for code in codes:
        bits.extend((code >> shift) & 1 for shift in reversed(range(model.width)))
        piece = model.accept(code)
        if piece is None:
            break
        tokens.extend(piece)
    bits.extend([0] * (-len(bits) % 8))
    body = bytes(sum(bits[i + j] << (7 - j) for j in range(8))
                 for i in range(0, len(bits), 8))
    data = expand(tokens) if validate else b''
    return header(name) + body + struct.pack('<H', sum(data) & 65535), data, model


def decode(raw):
    assert raw[:2] == b'\x76\xfe'
    end = raw.index(0, 2)
    assert raw[end + 2:end + 4] == b'\x20\0'
    model = Model()
    bit, tokens = (end + 5) * 8, bytearray()
    while True:
        code = 0
        for _ in range(model.width):
            code = code * 2 + ((raw[bit // 8] >> (7 - bit % 8)) & 1)
            bit += 1
        piece = model.accept(code)
        if piece is None:
            break
        tokens.extend(piece)
    used = (bit + 7) // 8
    data = expand(tokens)
    assert struct.unpack_from('<H', raw, used)[0] == sum(data) & 65535
    return data, used + 2, model


class Decoder(Machine):
    def __init__(self, library, image):
        super().__init__(library, image)
        self.symbols = {name: self.word(0x100 + 2 * i) for i, name in enumerate(ENTRIES)}

    def configure(self, raw, write=True, size=SIZE, address=0x7003):
        super().configure(raw, write, size, address)
        self.mem[address - 1:address + SIZE + 1] = bytes([0xA5]) * (SIZE + 2)
        self.mem[address:address + 16] = bytes(16)
        self.mem[address] = 1
        self.putword(address + 6, self.symbols['READ_CB'])
        self.putword(address + 8, self.symbols['WRITE_CB'] if write else 0)
        self.putword(address + 12, 0x6000)
        self.putword(address + 14, size)
        self.regs['SP'].value = 0xE800
        self.core.set_hooks(self.symbols['READ_CB'], self.symbols['WRITE_CB'], self.hook)

    def call(self, entry, budget=1000000000):
        # Base harness checks USQ-sized canary; explicitly check UNCR boundary
        # and entire configuration/code here instead.
        names = ('IX', 'IY', 'SP', 'A_', 'B_', 'C_', 'D_', 'E_', 'H_', 'L_', 'F_')
        saved = [self.regs[n].value for n in names]
        config = bytes(self.mem[self.ctx:self.ctx + 2]) + bytes(self.mem[self.ctx + 5:self.ctx + 16])
        steps = self.core.test_run(self.symbols[entry], budget)
        assert steps >= 0, (entry, steps, hex(self.regs['PC'].value))
        assert not self.callback_exception, self.callback_exception
        assert saved == [self.regs[n].value for n in names], entry
        assert config == bytes(self.mem[self.ctx:self.ctx + 2]) + bytes(self.mem[self.ctx + 5:self.ctx + 16])
        assert self.mem[self.ctx - 1] == self.mem[self.ctx + SIZE] == 0xA5
        assert bytes(self.mem[0x100:0x100 + len(self.image)]) == self.image
        self.calls += 1
        return self.regs['A'].value if self.regs['F'].value & 1 else 0

    def open(self, raw, **kwargs):
        self.configure(raw, **kwargs)
        assert self.call('UNCR_INIT') == 0
        return self.call('UNCR_HEAD')

    def error(self, entry, status, detail=None):
        got = self.call(entry)
        assert got == status, (entry, got, status, self.mem[self.ctx + 4])
        assert self.mem[self.ctx + 2] == 4
        if detail is not None:
            assert self.mem[self.ctx + 4] == detail
        state = bytes(self.mem[self.ctx:self.ctx + SIZE])
        counts = self.reads, self.writes
        for e in ENTRIES[1:5]:
            assert self.call(e) == status
            assert state == bytes(self.mem[self.ctx:self.ctx + SIZE])
            assert counts == (self.reads, self.writes)


def tests(m, corpus):
    # Hand-packed codes independently fix the MSB-first on-disk convention.
    for body, expected in ((bytes.fromhex('80000000'), b''),
                           (bytes.fromhex('20c0004100'), b'A')):
        assert m.open(header() + body) == 0
        assert m.call('UNCR_RUN') == 0 and m.output == expected
    rng = random.Random(452)
    vectors = [[256], [65, 256], [65, 260, 261, 256],
               [144, 0, 256], [65, 144, 255, 256],
               [65, 258, 259, 257, 66, 256],
               [65, 144, 257, 3, 256], [65, 144, 0, 144, 3, 256],
               [rng.randrange(128) for _ in range(10000)] + [256],
               list(range(128)) * 600 + [256]]
    # Reset at/beside each width transition, saturation and reassignment.
    for length in (250, 252, 764, 1788, 3837, 4500):
        vectors.append([rng.randrange(128) for _ in range(length)]
                       + [257, 144, 0, 65, 260, 256])
    # A growing phrase chain exercises expansion without processor recursion.
    vectors.append([65] + list(range(260, 1500)) + [256])
    for codes in vectors:
        raw, data, model = fixture(codes)
        assert decode(raw)[:2] == (data, len(raw))
        for mode in ('run', 'get', 'end', 'mixed') if len(data) < 5000 else ('run',):
            assert m.open(raw + b'UNREAD') == 0
            assert not m.writes
            output = bytearray()
            if mode == 'get':
                while True:
                    status = m.call('UNCR_GET')
                    if status:
                        assert status == 1
                        break
                    output.append(m.regs['A'].value)
            elif mode == 'end':
                assert m.call('UNCR_END') == 0
            else:
                if mode == 'mixed' and data:
                    assert m.call('UNCR_GET') == 0
                    output.append(m.regs['A'].value)
                status = m.call('UNCR_RUN')
                assert status == 0, (status, m.mem[m.ctx + 4], len(data), len(m.output))
                output.extend(m.output)
            if mode != 'end':
                assert output == data, (len(output), len(data))
            assert m.position == len(raw), (m.position, len(raw))
            assert int.from_bytes(bytes(m.mem[m.ctx + 40:m.ctx + 44]), 'little') == len(data)
            assert m.call('UNCR_GET') == 1
            assert m.call('UNCR_RUN') == m.call('UNCR_END') == 0
        if len(codes) == 10001:
            assert model.widths == {9, 10, 11, 12} and model.reassigned > 0
    assert corpus.is_dir(), f'historical corpus missing: {corpus}; use --corpus'
    historical = list(sorted(corpus.glob('*.MZC')))
    assert historical, 'empty historical corpus'
    with (corpus / 'MANIFEST.tsv').open() as stream:
        manifest = {row['utility']: row for row in csv.DictReader(stream, delimiter='\t')}
    totals = [0, 0]
    for path in historical:
        raw = path.read_bytes()
        data, used, model = decode(raw)
        row = manifest[path.stem]
        assert len(raw) == int(row['mzc_size'])
        assert hashlib.sha256(raw).hexdigest() == row['mzc_sha256']
        original_size = int(row['mac_size'])
        assert hashlib.sha256(data[:original_size]).hexdigest() == row['mac_sha256']
        assert data[original_size:] == bytes(-original_size % 128)
        assert m.open(raw) == 0
        status = m.call('UNCR_RUN')
        assert status == 0 and m.output == data, (path.name, status, len(m.output), len(data))
        assert m.position == used
        totals[0] += model.reassigned
        totals[1] += model.resets - 1
    raw, data, _ = fixture([65, 66, 260, 256])
    for end in range(len(raw)):
        assert m.open(raw[:end]) in (0, 4)
        m.error('UNCR_RUN', 4)
    bad = bytearray(raw); bad[-1] ^= 1
    assert m.open(bad) == 0
    m.error('UNCR_RUN', 6, 0)
    for name in (b'A' * 127, b'X.TXT[01/01/87]'):
        valid, _, _ = fixture([256], name)
        assert m.open(valid) == 0 and m.call('UNCR_RUN') == 0
    assert m.open(header(b'A' * 128)) == 11
    for info, detail in ((b'\x24\x10\0\x05', 0x10), (b'\x28\x21\0\0', 0x21),
                         (b'\x24\x20\1\0', 1)):
        assert m.open(header(info=info)) == 3
        m.error('UNCR_GET', 3, detail)
    assert m.open(b'\x76\xff') == 2
    m.error('UNCR_GET', 2)
    # Raw illegal first code: 104h is undefined; 105h is beyond NEXT.
    for code in (260, 261, 511):
        body = bytes([code >> 1, (code & 1) << 7])
        assert m.open(header() + body + b'\0\0') == 0
        m.error('UNCR_RUN', 5, 1)
    for codes in ([144, 256], [144, 2, 256], [65, 144, 1, 256]):
        bad, _, _ = fixture(codes, validate=False)
        assert m.open(bad) == 0
        m.error('UNCR_RUN', 5, 4)
    for offset in (0, 2, len(header()), len(raw) - 1):
        m.configure(raw)
        m.read_error = (offset, 0x37)
        assert m.call('UNCR_INIT') == 0
        if offset < len(header()):
            m.error('UNCR_HEAD', 7, 0x37)
        else:
            assert m.call('UNCR_HEAD') == 0
            m.error('UNCR_RUN', 7, 0x37)
    for reason in (0, 0x73):
        assert m.open(raw) == 0
        m.write_error = (1, reason)
        m.error('UNCR_RUN', 8, reason)
    assert m.open(raw, write=False) == 0
    reads = m.reads
    m.error('UNCR_RUN', 13, 5)
    assert m.reads == reads
    for size in (0, 15, 16, SIZE - 1):
        m.configure(raw, size=size)
        assert m.call('UNCR_INIT') == 11
    for offset, value in ((0, 2), (1, 1), (5, 1), (6, 0)):
        m.configure(raw)
        m.mem[m.ctx + offset] = value
        if offset == 6:
            m.mem[m.ctx + 7] = 0
        assert m.call('UNCR_INIT') == 13
    m.configure(raw)
    assert m.call('UNCR_INIT') == 0
    m.error('UNCR_GET', 12, 1)
    # Malicious/corrupted internal structures must have bounded traversals.
    assert m.open(fixture([65, 260, 256])[0]) == 0
    assert m.call('UNCR_GET') == 0
    # Force a self-referencing entry and make NEXT regard it as defined.
    m.putword(m.ctx + 24, 261)
    m.putword(m.ctx + 192 + 520, 260)
    m.error('UNCR_RUN', 5, 2)
    # Two contexts share immutable emitted code, interleaving within phrases
    # and pending RLE runs. Neither may rely on caller-saved register values.
    states = []
    fields = ('ctx', 'raw', 'position', 'output', 'reads', 'writes',
              'read_error', 'write_error', 'callback_exception')
    for address, codes in ((0x1003, [65, 260, 261, 144, 20, 256]),
                           (0x8003, [66, 260, 144, 30, 257, 67, 256])):
        vector, expected, _ = fixture(codes)
        assert m.open(vector, address=address) == 0
        states.append(({n: getattr(m, n) for n in fields}, expected, bytearray()))
    m.regs['SP'].value = 0xFF00
    for _ in range(12):
        for state, expected, out in states:
            for n, value in state.items():
                setattr(m, n, value)
            m.regs['IX'].value = m.ctx
            assert m.call('UNCR_GET') == 0
            out.append(m.regs['A'].value)
            state.update({n: getattr(m, n) for n in fields})
    for state, expected, out in states:
        for n, value in state.items():
            setattr(m, n, value)
        m.regs['IX'].value = m.ctx
        assert m.call('UNCR_RUN') == 0
        assert out + m.output == expected
    print(f'Historical corpus: {len(historical)} files; {totals[0]} reassignments, {totals[1]} resets.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    parser.add_argument('--z80pack', type=Path, default=Path.home() / 'projects/git/z80pack')
    parser.add_argument('--corpus', type=Path, default=ROOT.parent / 'cpm-2.2-compatibility-suite/suite/crunched-source')
    parser.add_argument('--cc', default='cc')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='bettercpm-uncr-') as temp:
        work = Path(temp)
        for name in ('codec.inc', 'codec.mac', 'uncr.inc', 'uncr.mac'):
            shutil.copy2(ROOT / 'src/codec' / name, work / name)
        definitions = '        ORG 100H\n' + ''.join(
            f'        INCLUDE {n}\n' for n in ('codec.inc', 'codec.mac', 'uncr.inc', 'uncr.mac'))
        (work / 'definitions.mac').write_text(definitions + '        DB 05AH\n        END\n')
        subprocess.run([str(args.assembler), '-e32', '-fb', '-odefinitions.bin',
                        'definitions.mac'], cwd=work, check=True)
        assert (work / 'definitions.bin').read_bytes() == b'\x5a', 'definitions emitted code'
        source = '        ORG 100H\n'
        source += ''.join(f'        INCLUDE {n}\n' for n in ('codec.inc', 'codec.mac', 'uncr.inc', 'uncr.mac'))
        source += '        DW ' + ','.join(ENTRIES) + '\n'
        source += 'READ_CB: RET\nWRITE_CB: RET\n        CODEC_CODE\n        UNCR_CODE\n        END\n'
        (work / 'test.mac').write_text(source)
        subprocess.run([str(args.assembler), '-e32', '-fb', '-otest.bin', 'test.mac'], cwd=work, check=True)
        image = (work / 'test.bin').read_bytes()
        (work / 'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h', 'simport.h'):
            shutil.copy2(args.z80pack / 'z80sim/srcsim' / name, work / name)
        (work / 'shim.c').write_text(SHIM)
        core = args.z80pack / 'z80core'
        subprocess.run([args.cc, '-shared', '-fPIC', '-O2', f'-I{work}', f'-I{core}',
                        str(work / 'shim.c'), str(core / 'simglb.c'),
                        *map(str, sorted(core.glob('simz80*.c'))), '-o', str(work / 'core.so')], check=True)
        m = Decoder(C.CDLL(str(work / 'core.so')), image)
        tests(m, args.corpus)
        print(f'PASS: {m.cases} UNCR cases, {m.calls} assembled entry calls;')
        print(f'code {len(image) - 16} bytes; context {SIZE} bytes; ABI/canaries/immutable code checked.')


if __name__ == '__main__':
    main()
