#!/usr/bin/env python3
"""Execute CrLZH decoder on full Z80 core against both historical archives.

Uses original, unmodified CRLZH11.LBR and CRLZH20.LBR from the ignored
build/test-fixtures/crlzh cache, or paths supplied with --archives.
Download URLs: https://dflund.se/~pi/cpm/files/ftp.mayn.de/pub/cpm/archive/squsq/
Archive hashes are pinned below. Never modifies archives or emulator media.
Synthetic adaptive-Huffman encoder/model independently checks bit-level cases.
Requires z80asm, host cc and z80pack sources. No historical code vendored.
"""
import argparse
import ctypes as C
import hashlib
from pathlib import Path
import random
import shutil
import struct
import subprocess
import tempfile

from test_usq import Machine, SHIM

ROOT = Path(__file__).resolve().parents[1]
SIZE = 6646
ENTRIES = ('UNLZH_INIT', 'UNLZH_HEAD', 'UNLZH_GET', 'UNLZH_RUN', 'UNLZH_END',
           'READ_CB', 'WRITE_CB')
# Expanded wrappers checked against their separately published plain source,
# including CP/M 1Ah record padding. This adds an oracle outside our model.
WRAPPER_HASHES = {
    'UCRLZH11.ZY0': 'dac2b9c10a87db3838f4f87f856d73337b7ef3f1f97d09c98f832b7f50e4afea',
    'UCRLZH20.ZY0': '6d6ef9fd2a9a2db5551ea685e84fd844693ecd5b0e8e2c666df084bb57fe5fb1',
}
ARCHIVE_HASHES = {
    '866101fd15ca998cd4c022cc7050d2217a26bf558065b920279a953e5b4d08d4': (0x10, 21),
    '197aaec608e70b5d75390b31dec4956bde241c37f7ecc33f55f8ff5d8b5fd02e': (0x20, 26),
}


class Huffman:
    def __init__(self):
        self.freq = [1] * 315 + [0] * 315
        self.son = [629 + i for i in range(315)] + [0] * 314
        self.parent = [0] * 944
        self.rebuilds = 0
        for i in range(315):
            self.parent[629 + i] = i
        for j, i in enumerate(range(0, 628, 2), 315):
            self.freq[j] = self.freq[i] + self.freq[i + 1]
            self.son[j] = i
            self.parent[i] = self.parent[i + 1] = j
        self.freq[629] = 65535

    def reconstruct(self):
        leaves = [((self.freq[i] + 1) >> 1, self.son[i]) for i in range(629) if self.son[i] >= 629]
        for i, (freq, son) in enumerate(leaves):
            self.freq[i], self.son[i] = freq, son
        for j, i in enumerate(range(0, 628, 2), 315):
            value = self.freq[i] + self.freq[i + 1]
            k = j
            while k and self.freq[k - 1] > value:
                self.freq[k], self.son[k] = self.freq[k - 1], self.son[k - 1]
                k -= 1
            self.freq[k], self.son[k] = value, i
        for i, child in enumerate(self.son):
            self.parent[child] = i
            if child < 629:
                self.parent[child + 1] = i
        self.parent[628] = 0
        self.rebuilds += 1

    def update(self, symbol):
        if self.freq[628] == 0x8000:
            self.reconstruct()
        node = self.parent[symbol + 629]
        while True:
            self.freq[node] += 1
            weight = self.freq[node]
            last = node + 1
            if weight > self.freq[last]:
                while weight > self.freq[last]:
                    last += 1
                last -= 1
                self.freq[node], self.freq[last] = self.freq[last], weight
                a, b = self.son[node], self.son[last]
                self.son[node], self.son[last] = b, a
                for child, parent in ((a, last), (b, node)):
                    self.parent[child] = parent
                    if child < 629:
                        self.parent[child + 1] = parent
                node = last
            node = self.parent[node]
            if node == 0:
                break

    def encode(self, symbol):
        node = self.parent[symbol + 629]
        path = []
        while node != 628:
            path.append(node & 1)
            node = self.parent[node]
        self.update(symbol)
        return list(reversed(path))

    def read(self, bit):
        node = self.son[628]
        while node < 629:
            node = self.son[node + bit()]
        symbol = node - 629
        self.update(symbol)
        return symbol


LENGTHS = [3] + [4] * 3 + [5] * 8 + [6] * 12 + [7] * 24 + [8] * 16
CODES = []
code, previous = 0, 3
for i, length in enumerate(LENGTHS):
    if i:
        code = (code + 1) << (length - previous)
    CODES.append(code)
    previous = length


def header(sig=0x20, name=b'TEST.BIN', check=0):
    return b'\x76\xfd' + name + bytes([0, sig, sig, check, 5])


def fixture(tokens, sig=0x20, name=b'TEST.BIN'):
    """Token is a literal or (length, distance), distance allowed 1..4096 old."""
    tree, bits, output = Huffman(), [], bytearray()
    ring, cursor = bytearray(b' ' * 2048), 0
    def emit(value):
        nonlocal cursor
        output.append(value)
        ring[cursor] = value
        cursor = (cursor + 1) % 2048
    for token in tokens:
        if isinstance(token, int):
            bits.extend(tree.encode(token))
            emit(token)
        else:
            length, distance = token
            assert 3 <= length <= 60 and 1 <= distance <= (4096 if sig == 0x10 else 2048)
            bits.extend(tree.encode(length + 254))
            lowbits = 6 if sig == 0x10 else 5
            offset = distance - 1
            upper, lower = offset >> lowbits, offset & ((1 << lowbits) - 1)
            bits.extend((CODES[upper] >> shift) & 1 for shift in reversed(range(LENGTHS[upper])))
            bits.extend((lower >> shift) & 1 for shift in reversed(range(lowbits)))
            for _ in range(length):
                emit(ring[(cursor - distance) % 2048])
    bits.extend(tree.encode(256))
    bits.extend([0] * (-len(bits) % 8))
    body = bytes(sum(bits[i + j] << (7 - j) for j in range(8)) for i in range(0, len(bits), 8))
    return header(sig, name) + body + struct.pack('<H', sum(output) & 65535), bytes(output), tree.rebuilds


def decode(raw):
    assert raw[:2] == b'\x76\xfd'
    end = raw.index(0, 2)
    sig, checking = raw[end + 2:end + 4]
    assert sig in (0x10, 0x20) and checking == 0
    cursor = (end + 5) * 8
    tree, ring, write, output = Huffman(), bytearray(b' ' * 2048), 0, bytearray()
    def bit():
        nonlocal cursor
        value = raw[cursor // 8] >> (7 - cursor % 8) & 1
        cursor += 1
        return value
    def emit(value):
        nonlocal write
        output.append(value)
        ring[write] = value
        write = (write + 1) % 2048
    while True:
        symbol = tree.read(bit)
        if symbol == 256:
            break
        if symbol < 256:
            emit(symbol)
        else:
            prefix = 0
            for n in range(1, 9):
                prefix = prefix * 2 + bit()
                upper = next((i for i in range(64) if LENGTHS[i] == n and CODES[i] == prefix), None)
                if upper is not None:
                    break
            assert upper is not None
            low = 0
            lowbits = 6 if sig == 0x10 else 5
            for _ in range(lowbits):
                low = low * 2 + bit()
            distance = (upper << lowbits) + low + 1
            for _ in range(symbol - 254):
                emit(ring[(write - distance) % 2048])
    used = (cursor + 7) // 8
    assert struct.unpack_from('<H', raw, used)[0] == sum(output) & 65535
    return bytes(output), used + 2, tree.rebuilds


class Decoder(Machine):
    def __init__(self, library, image):
        super().__init__(library, image)
        self.symbols = {name: self.word(0x100 + i * 2) for i, name in enumerate(ENTRIES)}

    def configure(self, raw, write=True, size=SIZE, address=0x8003):
        super().configure(raw, write, size, address)
        self.mem[address - 1:address + SIZE + 1] = bytes([0xA5]) * (SIZE + 2)
        self.mem[address:address + 16] = bytes(16)
        self.mem[address] = 1
        self.putword(address + 6, self.symbols['READ_CB'])
        self.putword(address + 8, self.symbols['WRITE_CB'] if write else 0)
        self.putword(address + 12, 0x7000)
        self.putword(address + 14, size)
        self.core.set_hooks(self.symbols['READ_CB'], self.symbols['WRITE_CB'], self.hook)

    def call(self, entry, budget=1500000000):
        names = ('IX', 'IY', 'SP', 'A_', 'B_', 'C_', 'D_', 'E_', 'H_', 'L_', 'F_')
        saved = [self.regs[n].value for n in names]
        config = bytes(self.mem[self.ctx:self.ctx + 2]) + bytes(self.mem[self.ctx + 5:self.ctx + 16])
        result = self.core.test_run(self.symbols[entry], budget)
        assert result >= 0, (entry, result, hex(self.regs['PC'].value))
        assert not self.callback_exception, self.callback_exception
        assert saved == [self.regs[n].value for n in names]
        assert config == bytes(self.mem[self.ctx:self.ctx + 2]) + bytes(self.mem[self.ctx + 5:self.ctx + 16])
        assert self.mem[self.ctx - 1] == self.mem[self.ctx + SIZE] == 0xA5
        assert bytes(self.mem[0x100:0x100 + len(self.image)]) == self.image
        self.calls += 1
        return self.regs['A'].value if self.regs['F'].value & 1 else 0

    def open(self, raw, **kwargs):
        self.configure(raw, **kwargs)
        assert self.call('UNLZH_INIT') == 0
        return self.call('UNLZH_HEAD')

    def error(self, entry, status, detail=None):
        actual = self.call(entry)
        assert actual == status, (entry, actual, status, self.mem[self.ctx + 4])
        assert self.mem[self.ctx + 2] == 4
        if detail is not None:
            assert self.mem[self.ctx + 4] == detail
        state = bytes(self.mem[self.ctx:self.ctx + SIZE])
        events = self.reads, self.writes
        for repeated in ENTRIES[1:5]:
            assert self.call(repeated) == status
            assert state == bytes(self.mem[self.ctx:self.ctx + SIZE])
            assert events == (self.reads, self.writes)


def tests(m, archives):
    rng = random.Random(456)
    patterns = [[], [0], [144], [(60, 1)], [65, (60, 1), (60, 1)],
                [65, 66, (60, 2)], list(range(256)) * 9 + [(60, 2048)],
                list(range(256)) * 270,
                [rng.randrange(256) for _ in range(33000)],
                [rng.randrange(256) for _ in range(2047)] + [(60, 1), (60, 2048)]]
    # EOF immediately before, at and after the first root-weight rebuild.
    # Initial root frequency is 315; each symbol, including EOF, adds one.
    for n in (32452, 32453, 32454):
        patterns.append([i % 251 for i in range(n)])
    synthetic_rebuilds = 0
    # Cover every position prefix, low-bit extremes, and old 4 KiB distances
    # wrapping into the 2 KiB ring. Literal streams cross reconstruction.
    for sig in (0x10, 0x20):
        distances = [(3, (upper << (6 if sig == 0x10 else 5)) + low + 1)
                     for upper in range(64) for low in (0, 63 if sig == 0x10 else 31)]
        seeded_distances = [rng.randrange(256) for _ in range(2048)] + distances
        for tokens in patterns + [seeded_distances]:
            raw, expected, rebuilds = fixture(tokens, sig)
            assert decode(raw) == (expected, len(raw), rebuilds)
            if len(tokens) in (32452, 32453, 32454):
                assert rebuilds == int(len(tokens) >= 32453)
            synthetic_rebuilds += rebuilds
            for mode in ('run', 'get', 'end', 'mixed') if len(expected) < 5000 else ('run',):
                assert m.open(raw + b'UNREAD', write=mode not in ('get', 'end')) == 0
                assert not m.writes
                out = bytearray()
                if mode == 'get':
                    while True:
                        status = m.call('UNLZH_GET')
                        if status:
                            assert status == 1
                            break
                        out.append(m.regs['A'].value)
                elif mode == 'end':
                    assert m.call('UNLZH_END') == 0
                else:
                    if mode == 'mixed' and expected:
                        for _ in range(min(4, len(expected))):
                            assert m.call('UNLZH_GET') == 0
                            out.append(m.regs['A'].value)
                    status = m.call('UNLZH_RUN')
                    assert status == 0, (sig, len(expected), status, m.mem[m.ctx + 4], len(m.output))
                    out.extend(m.output)
                assert mode == 'end' or out == expected, (sig, mode, len(out), len(expected))
                assert m.position == len(raw)
                assert m.word(m.ctx + 58) == rebuilds
                assert int.from_bytes(bytes(m.mem[m.ctx + 24:m.ctx + 28]), 'little') == len(expected)
                assert m.call('UNLZH_GET') == 1
                assert m.call('UNLZH_RUN') == m.call('UNLZH_END') == 0
    assert synthetic_rebuilds > 0
    historical, rebuild_total, versions = 0, 0, set()
    for archive in archives:
        raw = archive.read_bytes()
        sig, count = ARCHIVE_HASHES[hashlib.sha256(raw).hexdigest()]
        versions.add(sig)
        found = 0
        directory = struct.unpack_from('<H', raw, 14)[0] * 128
        for offset in range(32, directory, 32):
            entry = raw[offset:offset + 32]
            if len(entry) != 32 or entry[0] != 0:
                continue
            sector, records = struct.unpack_from('<HH', entry, 12)
            data = raw[sector * 128:(sector + records) * 128]
            if data[:2] != b'\x76\xfd':
                continue
            expected, used, rebuilds = decode(data)
            name = entry[1:9].decode().rstrip() + '.' + entry[9:12].decode().rstrip()
            if name in WRAPPER_HASHES:
                assert hashlib.sha256(expected).hexdigest() == WRAPPER_HASHES[name]
            assert m.open(data) == 0
            result = m.call('UNLZH_RUN')
            assert result == 0 and m.output == expected, (name, result, len(m.output), len(expected))
            assert m.position == used and m.word(m.ctx + 58) == rebuilds
            historical += 1
            found += 1
            rebuild_total += rebuilds
        assert found == count
    assert versions == {0x10, 0x20}
    for sig in (0x10, 0x20):
        raw, expected, _ = fixture([65, (60, 1), 144, (3, 2048)], sig)
        for end in range(len(raw)):
            assert m.open(raw[:end]) in (0, 4)
            m.error('UNLZH_RUN', 4)
        bad = bytearray(raw); bad[-1] ^= 1
        assert m.open(bad) == 0
        m.error('UNLZH_RUN', 6, 0)
        assert m.open(bad, write=False) == 0
        m.error('UNLZH_END', 6)
    for sig in (0, 0x11, 0x21, 0xff):
        assert m.open(header(sig)) == 3
        m.error('UNLZH_GET', 3, sig)
    for check in (1, 0x10, 0xff):
        assert m.open(header(check=check)) == 3
        m.error('UNLZH_GET', 3, check)
    assert m.open(b'\x76\xfe') == 2
    m.error('UNLZH_GET', 2)
    assert m.open(header(name=b'A' * 128)) == 11
    m.error('UNLZH_GET', 11, 3)
    for name in (b'', b'FILE.A  [STAMP]', b'A' * 127):
        raw, _, _ = fixture([65], name=name)
        assert m.open(raw) == 0 and m.call('UNLZH_RUN') == 0
    raw, _, _ = fixture([65, (60, 1), 66])
    for offset in (0, 2, len(header()), len(raw) - 1):
        m.configure(raw)
        m.read_error = (offset, 0x37)
        assert m.call('UNLZH_INIT') == 0
        if offset < len(header()):
            m.error('UNLZH_HEAD', 7, 0x37)
        else:
            assert m.call('UNLZH_HEAD') == 0
            m.error('UNLZH_RUN', 7, 0x37)
    for reason in (0, 0x73):
        assert m.open(raw) == 0
        m.write_error = (2, reason)
        m.error('UNLZH_RUN', 8, reason)
    assert m.open(raw, write=False) == 0
    events = m.reads
    m.error('UNLZH_RUN', 13, 5)
    assert m.reads == events
    for size in (0, 15, 16, SIZE - 1):
        m.configure(raw, size=size)
        assert m.call('UNLZH_INIT') == 11
    for offset, value, detail in ((0, 2, 1), (1, 1, 2), (5, 1, 3), (6, 0, 4)):
        m.configure(raw)
        m.mem[m.ctx + offset] = value
        if offset == 6:
            m.mem[m.ctx + 7] = 0
        assert m.call('UNLZH_INIT') == 13 and m.mem[m.ctx + 4] == detail
    m.configure(raw)
    assert m.call('UNLZH_INIT') == 0
    m.error('UNLZH_GET', 12, 1)
    # Corrupted internal tree states must be bounded before any table escape.
    assert m.open(header() + bytes(256)) == 0
    for index in (0, 1, 628):
        m.putword(m.ctx + 3500 + index * 2, 0)
    m.error('UNLZH_GET', 5, 1)
    raw, _, _ = fixture([65])
    assert m.open(raw) == 0
    m.putword(m.ctx + 3500 + 628 * 2, 944)
    m.error('UNLZH_GET', 5, 2)
    assert m.open(raw) == 0
    m.putword(m.ctx + 4758 + (629 + 65) * 2, 0xffff)
    m.error('UNLZH_GET', 5, 1)
    assert m.open(raw) == 0
    m.putword(m.ctx + 2240 + 628 * 2, 0x8001)
    m.error('UNLZH_GET', 5, 1)
    # Interleave distinct contexts during pending overlapping copies.
    fields = ('ctx', 'raw', 'position', 'output', 'reads', 'writes',
              'read_error', 'write_error', 'callback_exception')
    states = []
    for address, sig, value in ((0x4003, 0x10, 65), (0x8003, 0x20, 66)):
        raw, expected, _ = fixture([value, (60, 1), (60, 1)], sig)
        assert m.open(raw, address=address) == 0
        states.append(({name: getattr(m, name) for name in fields}, expected, bytearray()))
    for _ in range(12):
        for state, expected, output in states:
            for name, value in state.items():
                setattr(m, name, value)
            m.regs['IX'].value = m.ctx
            assert m.call('UNLZH_GET') == 0
            output.append(m.regs['A'].value)
            state.update({name: getattr(m, name) for name in fields})
    for state, expected, output in states:
        for name, value in state.items():
            setattr(m, name, value)
        m.regs['IX'].value = m.ctx
        assert m.call('UNLZH_RUN') == 0
        assert output + m.output == expected
    print(f'Historical: {historical} files, both variants, {rebuild_total} reconstructions.')
    print(f'Synthetic streams: {synthetic_rebuilds} reconstructions, including exact root-weight boundaries.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archives', type=Path, nargs=2,
                        default=[ROOT / 'build/test-fixtures/crlzh' / f'crlzh{v}.lbr' for v in ('11', '20')],
                        metavar=('CRLZH11.LBR', 'CRLZH20.LBR'))
    parser.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    parser.add_argument('--z80pack', type=Path, default=Path.home() / 'projects/git/z80pack')
    parser.add_argument('--cc', default='cc')
    args = parser.parse_args()
    for archive in args.archives:
        if not archive.is_file():
            parser.error(f'missing historical archive {archive}; supply originals with --archives (URL in docstring)')
    with tempfile.TemporaryDirectory(prefix='bettercpm-unlzh-') as temp:
        work = Path(temp)
        includes = tuple(f'{codec}.{suffix}' for codec in ('codec', 'usq', 'sq', 'uncr', 'cr', 'unlzh')
                         for suffix in ('inc', 'mac'))
        for name in includes:
            shutil.copy2(ROOT / 'src/codec' / name, work / name)
        definitions = '        ORG 100H\n' + ''.join(f'        INCLUDE {n}\n' for n in includes)
        (work / 'definitions.mac').write_text(definitions + '        DB 05AH\n        END\n')
        subprocess.run([str(args.assembler), '-e32', '-fb', '-odefinitions.bin', 'definitions.mac'], cwd=work, check=True)
        assert (work / 'definitions.bin').read_bytes() == b'\x5a'
        coexist = definitions + ''.join(f'        {name}\n' for name in
                    ('CODEC_CODE', 'USQ_CODE', 'SQ_CODE', 'UNCR_CODE', 'CR_CODE', 'UNLZH_CODE'))
        (work / 'coexist.mac').write_text(coexist + '        END\n')
        subprocess.run([str(args.assembler), '-e32', '-fb', '-ocoexist.bin', 'coexist.mac'], cwd=work, check=True)
        source = definitions + '        DW ' + ','.join(ENTRIES) + '\n'
        source += 'READ_CB: RET\nWRITE_CB: RET\n        CODEC_CODE\n        UNLZH_CODE\n        END\n'
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
        tests(m, args.archives)
        print(f'PASS: {m.cases} UNLZH cases, {m.calls} assembled calls;')
        print(f'code {len(image) - 16} bytes including common helpers; context {SIZE} bytes;')
        print('overlap/wrap/reconstruction/truncation/checksum/callbacks/ABI/code immutability checked.')


if __name__ == '__main__':
    main()
