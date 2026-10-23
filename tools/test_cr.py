#!/usr/bin/env python3
"""Run assembled CR and UNCR on the full Z80 core, with a host model oracle.

CR uses capacity resets, not historical reassignment/ratio heuristics. The
independent decoder validates width timing, checksum, reset and exact EOF.
No emulator media are modified. Requires z80pack sources/z80asm and host cc.
"""
import argparse
import ctypes as C
from pathlib import Path
import random
import shutil
import struct
import subprocess
import tempfile

from test_usq import Machine, SHIM
from test_uncr import decode

ROOT = Path(__file__).resolve().parents[1]
SIZE = 25207
ENTRIES = ('UNCR_INIT', 'UNCR_HEAD', 'UNCR_GET', 'UNCR_RUN', 'UNCR_END',
           'READ_CB', 'WRITE_CB', 'CR_INIT', 'CR_RUN', 'CR_RESET', 'CR_PUT_DATA')


class Codec(Machine):
    def __init__(self, library, image, encode=False):
        super().__init__(library, image)
        self.symbols = {name: self.word(0x100 + i * 2) for i, name in enumerate(ENTRIES)}
        self.encode = encode
        self.size = SIZE if encode else 26582

    def configure(self, raw, name=b'TEST.BIN', write=True, size=None, address=0x7003):
        self.ctx = address
        self.raw, self.position, self.output = raw, 0, bytearray()
        self.reads = self.writes = 0
        self.read_error = self.write_error = self.callback_exception = None
        self.mem[address - 1:address + self.size + 1] = bytes([0xA5]) * (self.size + 2)
        self.mem[address:address + 16] = bytes(16)
        self.mem[address] = 1
        self.putword(address + 6, self.symbols['READ_CB'])
        self.putword(address + 8, self.symbols['WRITE_CB'] if write else 0)
        self.putword(address + 12, 0x6000)
        self.putword(address + 14, self.size if size is None else size)
        if self.encode:
            self.mem[address + 64:address + 192] = (name + bytes(128))[:128]
        self.regs['IX'].value = address
        self.regs['SP'].value = 0xE800
        self.regs['IY'].value = 0xBEEF
        for i, n in enumerate(('A_', 'B_', 'C_', 'D_', 'E_', 'H_', 'L_', 'F_')):
            self.regs[n].value = 31 + i
        self.core.set_hooks(self.symbols['READ_CB'], self.symbols['WRITE_CB'], self.hook)
        self.cases += 1

    def call(self, entry, budget=1000000000):
        names = ('IX', 'IY', 'SP', 'A_', 'B_', 'C_', 'D_', 'E_', 'H_', 'L_', 'F_')
        saved = [self.regs[n].value for n in names]
        config = bytes(self.mem[self.ctx:self.ctx + 2]) + bytes(self.mem[self.ctx + 5:self.ctx + 16])
        name = bytes(self.mem[self.ctx + 64:self.ctx + 192]) if self.encode else None
        steps = self.core.test_run(self.symbols[entry], budget)
        assert steps >= 0, (entry, steps, hex(self.regs['PC'].value))
        assert not self.callback_exception, self.callback_exception
        assert saved == [self.regs[n].value for n in names], entry
        assert config == bytes(self.mem[self.ctx:self.ctx + 2]) + bytes(self.mem[self.ctx + 5:self.ctx + 16])
        if self.encode:
            assert name == bytes(self.mem[self.ctx + 64:self.ctx + 192])
        assert self.mem[self.ctx - 1] == self.mem[self.ctx + self.size] == 0xA5
        assert bytes(self.mem[0x100:0x100 + len(self.image)]) == self.image
        self.calls += 1
        return self.regs['A'].value if self.regs['F'].value & 1 else 0

    def error(self, entry, status, detail=None):
        actual = self.call(entry)
        assert actual == status, (entry, actual, status, self.mem[self.ctx + 4])
        assert self.mem[self.ctx + 2] == 4
        if detail is not None:
            assert self.mem[self.ctx + 4] == detail
        state = bytes(self.mem[self.ctx:self.ctx + self.size])
        events = self.reads, self.writes
        for _ in range(2):
            assert self.call(entry) == status
            assert state == bytes(self.mem[self.ctx:self.ctx + self.size])
            assert events == (self.reads, self.writes)

    def compress(self, data, **kwargs):
        self.configure(data, **kwargs)
        assert self.call('CR_INIT') == 0
        assert self.reads == self.writes == 0
        status = self.call('CR_RUN')
        assert status == 0, (status, self.mem[self.ctx + 4], self.position, len(self.output))
        assert self.position == len(data) and self.reads == len(data) + 1
        assert int.from_bytes(bytes(self.mem[self.ctx + 18:self.ctx + 22]), 'little') == len(data)
        assert self.word(self.ctx + 16) == sum(data) & 65535
        events = self.reads, self.writes
        assert self.call('CR_RUN') == 0 and events == (self.reads, self.writes)
        return bytes(self.output)


def reference(data, name=b'TEST.BIN'):
    """Independent phrase-string LZW encoder; emits capacity resets."""
    tokens = []
    i = 0
    while i < len(data):
        b = data[i]
        n = 1
        while i + n < len(data) and data[i + n] == b and n < 255:
            n += 1
        if b == 144:
            tokens.extend([144, 0] * n)
        elif n >= 3:
            tokens.extend([b, 144, n])
        else:
            tokens.extend([b] * n)
        i += n
    dictionary = {bytes([b]): b for b in range(256)}
    next_code, phrase = 260, b''
    from test_uncr import Model
    decoder = Model()
    bits = []
    def emit(code):
        bits.extend((code >> shift) & 1 for shift in reversed(range(decoder.width)))
        decoder.accept(code)
    for b in tokens:
        candidate = phrase + bytes([b])
        if candidate in dictionary:
            phrase = candidate
        else:
            dictionary[candidate] = next_code
            next_code += 1
            emit(dictionary[phrase])
            if next_code == 4096:
                emit(257)
                dictionary = {bytes([x]): x for x in range(256)}
                next_code = 260
            phrase = bytes([b])
    if phrase:
        emit(dictionary[phrase])
    emit(256)
    bits += [0] * (-len(bits) % 8)
    body = bytes(sum(bits[i + j] << (7 - j) for j in range(8)) for i in range(0, len(bits), 8))
    return b'\x76\xfe' + name + b'\0\x24\x20\0\x05' + body + struct.pack('<H', sum(data) & 65535)


def tests(cr, uncr):
    rng = random.Random(454)
    samples = [b'', b'A', b'\0', b'\x1a', b'\x90', b'\xff', b'ABABABA',
               b'A' * 2, b'B' * 3, b'Z' * 254, b'Z' * 255, b'Z' * 256,
               b'\x90' * 512, b'A' * 10000, bytes(range(256)) * 2,
               b'CP/M\r\n' * 2000, bytes(rng.randrange(256) for _ in range(9000)),
               bytes(rng.randrange(256) for _ in range(70001))]
    # Stop next to decoder width transitions and reset boundaries. A fixed
    # deterministic random prefix lets the host model establish exact timing.
    transition_data = bytes(rng.randrange(128) for _ in range(7000))
    for n in (0, 1, 2, 249, 250, 251, 252, 253, 760, 800, 1800, 2000, 3900, 4100):
        samples.append(transition_data[:n])
    # Order-2 de Bruijn sequence: each adjacent pair is new, so each
    # physical byte is one emitted data code, with no three-byte RLE runs.
    # These cutoffs place EOF exactly on either side of each width change
    # and the capacity reset, independently of compression coincidences.
    a, sequence = [0] * 129, []
    def debruijn(t, period):
        if t > 2:
            if 2 % period == 0:
                sequence.extend(a[1:period + 1])
        else:
            a[t] = a[t - period]
            debruijn(t + 1, period)
            for j in range(a[t - period] + 1, 64):
                a[t] = j
                debruijn(t + 1, t)
    debruijn(1, 1)
    sequence = bytes(sequence + sequence[:1])
    assert len({sequence[i:i + 2] for i in range(4096)}) == 4096
    for n in (251, 252, 253, 763, 764, 765, 1787, 1788, 1789,
              3835, 3836, 3837, 3838):
        samples.append(sequence[:n])
    resets, widths, special = 0, set(), 0
    for data in samples:
        raw = cr.compress(data)
        assert raw == reference(data), (len(data), 'independent encoder mismatch')
        decoded, used, model = decode(raw)
        assert decoded == data and used == len(raw)
        assert model.reassigned == 0
        resets += model.resets - 1
        widths.update(model.widths)
        special += model.special
        uncr.configure(raw + b'UNREAD')
        assert uncr.call('UNCR_INIT') == uncr.call('UNCR_HEAD') == 0
        assert uncr.call('UNCR_RUN') == 0
        assert uncr.output == data and uncr.position == len(raw)
    assert resets > 1 and widths == {9, 10, 11, 12} and special > 0
    assert len(cr.compress(b'A' * 10000)) < 256
    # Hand-packed one-byte and empty streams independently fix wire bit order.
    assert cr.compress(b'') == b'\x76\xfeTEST.BIN\0\x24\x20\0\x05' + bytes.fromhex('80000000')
    assert cr.compress(b'A') == b'\x76\xfeTEST.BIN\0\x24\x20\0\x05' + bytes.fromhex('20c0004100')
    for name in (b'', b'FILE.A  [STAMP]', b'A' * 127, b'$DATA.BIN'):
        raw = cr.compress(b'names', name=name)
        assert raw == reference(b'names', name)
        uncr.configure(raw)
        assert uncr.call('UNCR_INIT') == uncr.call('UNCR_HEAD') == uncr.call('UNCR_RUN') == 0
        assert uncr.output == b'names'
    for size in (0, 15, 16, SIZE - 1):
        cr.configure(b'data', size=size)
        assert cr.call('CR_INIT') == 11 and not cr.reads and not cr.writes
    for offset, value, detail in ((0, 2, 1), (1, 1, 2), (5, 1, 3), (6, 0, 4)):
        cr.configure(b'data')
        cr.mem[cr.ctx + offset] = value
        if offset == 6:
            cr.mem[cr.ctx + 7] = 0
        assert cr.call('CR_INIT') == 13 and cr.mem[cr.ctx + 4] == detail
    cr.configure(b'data', write=False)
    assert cr.call('CR_INIT') == 13 and cr.mem[cr.ctx + 4] == 5
    cr.configure(b'data', name=b'A' * 128)
    assert cr.call('CR_INIT') == 13 and cr.mem[cr.ctx + 4] == 128
    cr.configure(b'data')
    cr.error('CR_RUN', 12, 0)
    # Failures while writing header, packed data, padded final byte and trailer.
    data = bytes(range(256)) * 2
    raw = cr.compress(data)
    for offset in (0, 1, 8, 15, 32, len(raw) - 3, len(raw) - 2, len(raw) - 1):
        for reason in (0, 0x73):
            cr.configure(data)
            assert cr.call('CR_INIT') == 0
            cr.write_error = (offset, reason)
            cr.error('CR_RUN', 8, reason)
            assert len(cr.output) == offset
    for offset in (0, 1, 3, 250, len(data)):
        cr.configure(data)
        assert cr.call('CR_INIT') == 0
        cr.read_error = (offset, 0x37)
        cr.error('CR_RUN', 7, 0x37)
    cr.configure(b'A')
    assert cr.call('CR_INIT') == 0
    cr.mem[cr.ctx + 18:cr.ctx + 22] = b'\xff' * 4
    cr.error('CR_RUN', 11, 0x81)
    # Reinitialize after failure, preserve name/config and reset operation.
    assert cr.call('CR_INIT') == 0
    cr.raw, cr.position, cr.output = b'B', 0, bytearray()
    assert cr.call('CR_RUN') == 0
    assert decode(bytes(cr.output))[0] == b'B'
    print(f'Round trips: {len(samples) + 4}; widths {sorted(widths)}; {resets} capacity resets; {special} next-code cases.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    parser.add_argument('--z80pack', type=Path, default=Path.home() / 'projects/git/z80pack')
    parser.add_argument('--cc', default='cc')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='bettercpm-cr-') as temp:
        work = Path(temp)
        includes = ('codec.inc', 'codec.mac', 'cr.inc', 'cr.mac', 'uncr.inc', 'uncr.mac')
        for name in includes:
            shutil.copy2(ROOT / 'src/codec' / name, work / name)
        definitions = '        ORG 100H\n' + ''.join(f'        INCLUDE {n}\n' for n in includes)
        (work / 'definitions.mac').write_text(definitions + '        DB 05AH\n        END\n')
        subprocess.run([str(args.assembler), '-e32', '-fb', '-odefinitions.bin', 'definitions.mac'], cwd=work, check=True)
        assert (work / 'definitions.bin').read_bytes() == b'\x5a'
        source = definitions + '        DW ' + ','.join(ENTRIES) + '\n'
        source += 'READ_CB: RET\nWRITE_CB: RET\n        CODEC_CODE\n        CR_CODE\n        UNCR_CODE\n        END\n'
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
        lib = C.CDLL(str(work / 'core.so'))
        cr, uncr = Codec(lib, image, True), Codec(lib, image)
        tests(cr, uncr)
        print(f'PASS: {cr.cases} CR cases, {cr.calls} encoder calls; {uncr.cases} assembled UNCR round trips;')
        print(f'CR code {cr.symbols["UNCR_INIT"] - cr.symbols["CR_INIT"]} bytes; context {SIZE} bytes;')
        print('callbacks/EOF/checksum/ABI/canaries/immutable code checked.')


if __name__ == '__main__':
    main()
