#!/usr/bin/env python3
"""Exercise the real Z80 LBR library with independent LUDEF fixtures and faults.

Builds a temporary z80pack core; never touches emulator disks. This checks the
read ABI, not archive CRC testing, write support or release qualification.
"""
import argparse
import ctypes as C
from pathlib import Path
import shutil
import random
import struct
import subprocess
import tempfile

from test_usq import SHIM, Machine

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = ('LBR_OPEN', 'LBR_NEXT', 'LBR_READ', 'LBR_CLOSE', 'READ_CB', 'WRITE_CB')
SIZE = 138


def entry(name=b'FILE    BIN', start=1, records=1, pad=0, status=0):
    return (bytes([status]) + name + struct.pack('<HHH', start, records, 0)
            + bytes(8) + bytes([pad]) + bytes(5))


def archive(entries=(), payload=b'', sectors=1):
    assert len(entries) < sectors * 4
    control = entry(b' ' * 11, 0, sectors)
    directory = control + b''.join(entries)
    directory += (b'\xff' + bytes([0xA5]) * 31) * (sectors * 4 - len(entries) - 1)
    return directory + payload


class Reader(Machine):
    def __init__(self, core, image):
        super().__init__(core, image)
        self.symbols = {n: self.word(0x100 + 2 * i) for i, n in enumerate(ENTRIES)}
        core.set_hooks(self.symbols['READ_CB'], self.symbols['WRITE_CB'], self.hook)

    def configure(self, raw, size=SIZE, address=0x8003):
        self.ctx = address
        self.raw, self.reads, self.calls = raw, 0, 0
        self.read_error = None
        self.short = None
        self.callback_exception = None
        self.mem[address - 1:address + SIZE + 1] = bytes([0xA5]) * (SIZE + 2)
        self.mem[address:address + SIZE] = bytes(SIZE)
        self.mem[address] = 1
        self.putword(address + 2, self.symbols['READ_CB'])
        self.putword(address + 4, 0x7123)
        self.mem[address + 6:address + 10] = len(raw).to_bytes(4, 'little')
        self.putword(address + 10, size)
        self.regs['IX'].value = address
        self.regs['IY'].value = 0xBEEF
        self.regs['SP'].value = 0xF000
        for i, n in enumerate(('A_', 'B_', 'C_', 'D_', 'E_', 'H_', 'L_', 'F_')):
            self.regs[n].value = 0x31 + i
        self.cases += 1

    def callback(self, kind):
        try:
            assert kind == 0
            self.reads += 1
            offset = int.from_bytes(bytes(self.mem[self.ctx + 16:self.ctx + 20]), 'little')
            buffer = self.word(self.ctx + 20)
            count = self.word(self.ctx + 22)
            if self.read_error == offset:
                value, carry = 0xE7, True
            else:
                data = self.raw[offset:offset + count]
                if self.short == offset and data:
                    data = data[:-1]
                self.mem[buffer:buffer + len(data)] = data
                self.putword(self.ctx + 24, len(data))
                value, carry = 0x77, False
            self.regs['A'].value = value
            self.regs['F'].value = int(carry)
            for i, n in enumerate(('B', 'C', 'D', 'E', 'H', 'L')):
                self.regs[n].value = 0xD1 + i
        except BaseException as error:
            self.callback_exception = error
            self.regs['A'].value = 255
            self.regs['F'].value = 1

    def call(self, name, capacity=0, destination=0x6001):
        self.regs['B'].value, self.regs['C'].value = capacity >> 8, capacity & 255
        self.regs['D'].value, self.regs['E'].value = destination >> 8, destination & 255
        names = ('IX', 'IY', 'SP', 'A_', 'B_', 'C_', 'D_', 'E_', 'H_', 'L_', 'F_')
        before = [self.regs[n].value for n in names]
        config = bytes(self.mem[self.ctx:self.ctx + 12])
        steps = self.core.test_run(self.symbols[name], 3000000)
        assert steps >= 0, (name, steps, hex(self.regs['PC'].value))
        assert not self.callback_exception, self.callback_exception
        assert before == [self.regs[n].value for n in names], name
        assert config == bytes(self.mem[self.ctx:self.ctx + 12]), name
        assert self.mem[self.ctx - 1] == self.mem[self.ctx + SIZE] == 0xA5, name
        assert bytes(self.mem[0x100:0x100 + len(self.image)]) == self.image, name
        self.calls += 1
        return self.regs['A'].value if self.regs['F'].value & 1 else 0

    def member(self):
        return bytes(self.mem[self.ctx + 74:self.ctx + 138])


def tests(m):
    m.configure(archive())
    assert m.call('LBR_OPEN') == 0
    assert m.call('LBR_NEXT') == 1
    reads = m.reads
    assert m.call('LBR_NEXT') == 1 and m.reads == reads
    assert m.call('LBR_CLOSE') == 0
    assert m.call('LBR_NEXT') == 6

    # Empty members ignore index; zero time is preserved, not invented.
    for index in (0, 0xFFFF):
        m.configure(archive([entry(start=index, records=0)]))
        assert m.call('LBR_OPEN') == m.call('LBR_NEXT') == 0
        meta = m.member()
        assert meta[:11] == b'FILE    BIN' and meta[11] == 1
        assert meta[16:28] == bytes(12)
        reads = m.reads
        assert m.call('LBR_READ', 0) == 0
        assert m.call('LBR_READ', 1) == 1 and m.reads == reads

    # Full binary range including 1Ah, short last sector, chunked member reads.
    data = bytes(range(256)) * 2
    for pad in (0, 1, 127):
        m.configure(archive([entry(records=4, pad=pad)], data))
        assert m.call('LBR_OPEN') == m.call('LBR_NEXT') == 0
        meta = m.member()
        assert int.from_bytes(meta[12:16], 'little') == 32
        assert int.from_bytes(meta[16:20], 'little') == 128
        assert int.from_bytes(meta[20:24], 'little') == 512
        assert int.from_bytes(meta[24:28], 'little') == 512 - pad
        result = bytearray()
        while True:
            status = m.call('LBR_READ', 73)
            if status:
                assert status == 1
                break
            count = m.regs['B'].value * 256 + m.regs['C'].value
            assert 0 < count <= 73
            result.extend(m.mem[0x6001:0x6001 + count])
        assert result == data[:512 - pad]
        assert m.call('LBR_NEXT') == 1

    # No whole-directory allocation: cross record boundary; deleted bytes opaque.
    deleted = b'\xfe' + bytes([0xFF]) * 31
    raw = archive([deleted, entry(b'one     txt', 2), deleted,
                   entry(b'TWO     BIN', 3)], b'A' * 128 + b'B' * 128, sectors=2)
    m.configure(raw)
    assert m.call('LBR_OPEN') == m.call('LBR_NEXT') == 0
    assert m.member()[:11] == b'ONE     TXT'
    assert m.call('LBR_NEXT') == 0 and m.member()[:11] == b'TWO     BIN'
    assert m.call('LBR_READ', 128) == 0
    assert bytes(m.mem[0x6001:0x6081]) == b'B' * 128
    assert m.call('LBR_NEXT') == 1

    # Member offsets above 64K and record-count arithmetic above 16 bits.
    raw = archive([entry(start=600, records=1)], bytes(599 * 128) + b'Z' * 128)
    m.configure(raw)
    assert m.call('LBR_OPEN') == m.call('LBR_NEXT') == 0
    assert m.call('LBR_READ', 128) == 0
    assert bytes(m.mem[0x6001:0x6081]) == b'Z' * 128

    # Boundary arithmetic beyond record 65535 must not wrap to record zero.
    m.configure(archive([entry(start=65535, records=2)], bytes(65536 * 128)))
    assert m.call('LBR_OPEN') == m.call('LBR_NEXT') == 0
    assert int.from_bytes(m.member()[16:20], 'little') == 65535 * 128
    assert m.call('LBR_READ', 256) == 0
    assert bytes(m.mem[0x6001:0x6101]) == bytes(256)

    # Independent fixtures/random chunk sizes catch byte-order and carry bugs.
    rng = random.Random(471)
    for _ in range(30):
        sectors = rng.randrange(1, 12)
        pad = rng.randrange(128)
        payload = bytes(rng.randrange(256) for _ in range(sectors * 128))
        m.configure(archive([entry(records=sectors, pad=pad)], payload))
        assert m.call('LBR_OPEN') == m.call('LBR_NEXT') == 0
        result = bytearray()
        while True:
            capacity = rng.randrange(1, 301)
            status = m.call('LBR_READ', capacity)
            if status:
                assert status == 1
                break
            count = m.regs['B'].value * 256 + m.regs['C'].value
            assert 0 < count <= capacity
            result.extend(m.mem[0x6001:0x6001 + count])
        assert result == payload[:len(payload) - pad]

    # Header truncation and all mandatory control fields.
    for n in range(32):
        m.configure(archive()[:n])
        assert m.call('LBR_OPEN') == 3
    for offset in (0, 1, 11, 12, 13, 14):
        raw = bytearray(archive())
        raw[offset] = 1 if offset != 14 else 0
        m.configure(raw)
        assert m.call('LBR_OPEN') == 2, offset
    m.configure(archive(sectors=2)[:128])
    assert m.call('LBR_OPEN') == 3

    for bad in (entry(start=0), entry(records=2), entry(records=0, pad=1),
                entry(pad=128), entry(b'BAD?    BIN'), entry(b'        BIN'),
                entry(b'A B     BIN'), entry(b'FILE    B N')):
        m.configure(archive([bad], b'A' * 128))
        assert m.call('LBR_OPEN') == 0
        assert m.call('LBR_NEXT') in (2, 3)
        reads = m.reads
        assert m.call('LBR_NEXT') in (2, 3) and m.reads == reads

    # Unknown nonzero states are deleted; occupied after FF is malformed.
    for status in (1, 0xFE):
        m.configure(archive([entry(status=status)]))
        assert m.call('LBR_OPEN') == 0 and m.call('LBR_NEXT') == 1
    m.configure(archive([entry(status=0xFF), entry(records=0)]))
    assert m.call('LBR_OPEN') == 0 and m.call('LBR_NEXT') == 2

    # I/O failures and short callback responses must never become clean EOF.
    for offset, operation in ((0, 'LBR_OPEN'), (32, 'LBR_NEXT'), (128, 'LBR_READ')):
        for fault in ('read_error', 'short'):
            m.configure(archive([entry()], b'A' * 128))
            setattr(m, fault, offset)
            if operation != 'LBR_OPEN':
                assert m.call('LBR_OPEN') == 0
            if operation == 'LBR_READ':
                assert m.call('LBR_NEXT') == 0
            assert m.call(operation, 32) == (4 if fault == 'read_error' else 3)
            if fault == 'read_error':
                assert m.mem[m.ctx + 14] == 0xE7
            reads = m.reads
            if operation != 'LBR_OPEN':
                assert m.call(operation, 32) in (3, 4)
                assert m.reads == reads
    m.configure(archive(), size=65535)
    assert m.call('LBR_OPEN') == 5 and m.reads == 0
    for offset, value in ((0, 2), (1, 1), (2, 0), (10, 10)):
        m.configure(archive())
        m.mem[m.ctx + offset] = value
        if offset == 2:
            m.putword(m.ctx + 2, 0)
        assert m.call('LBR_OPEN') == 5 and m.reads == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    parser.add_argument('--z80pack', type=Path, default=Path.home() / 'projects/git/z80pack')
    parser.add_argument('--cc', default='cc')
    args = parser.parse_args()
    core = args.z80pack / 'z80core'
    with tempfile.TemporaryDirectory(prefix='bettercpm-lbr-') as temp:
        work = Path(temp)
        (work / 'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h', 'simport.h'):
            shutil.copy2(args.z80pack / 'z80sim/srcsim' / name, work / name)
        (work / 'shim.c').write_text(SHIM)
        subprocess.run([args.cc, '-shared', '-fPIC', '-O2', f'-I{work}', f'-I{core}',
                        str(work / 'shim.c'), str(core / 'simglb.c'),
                        *map(str, sorted(core.glob('simz80*.c'))), '-o', str(work / 'core.so')], check=True)
        for name in ('archive.inc', 'lbr.mac'):
            shutil.copy2(ROOT / 'src/archive' / name, work / name)
        (work / 'test.mac').write_text('        ORG 100H\n        INCLUDE archive.inc\n'
            '        INCLUDE lbr.mac\n' + ''.join(f'        DW {n}\n' for n in ENTRIES)
            + '        LBR_CODE\nREAD_CB: RET\nWRITE_CB: RET\n        END\n')
        subprocess.run([str(args.assembler), '-e32', '-fb', '-otest.bin', '-ltest.lst', 'test.mac'], cwd=work, check=True)
        image = (work / 'test.bin').read_bytes()
        if image[:0x100] == bytes(0x100):
            image = image[0x100:]
        m = Reader(C.CDLL(str(work / 'core.so')), image)
        tests(m)
        print(f'PASS: {m.cases} LBR cases; {len(image) - 14} library bytes; {SIZE}-byte context.')
        print('Read ABI, metadata, bounds, faults, register preservation and canaries checked.')


if __name__ == '__main__':
    main()
