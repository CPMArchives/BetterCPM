#!/usr/bin/env python3
"""Run assembled LZH and UNLZH on the full Z80 core, with a host model oracle.

The independent host encoder checks greedy matches and adaptive Huffman
updates against exact wire output. Both models check checksums and exact EOF.
No emulator media are modified. Requires z80pack sources/z80asm and host cc.
"""
import argparse
import ctypes as C
from pathlib import Path
import random
import shutil
import subprocess
import tempfile

from test_usq import Machine, SHIM
from test_unlzh import decode

ROOT = Path(__file__).resolve().parents[1]
SIZE = 11943
ENTRIES = ('UNLZH_INIT', 'UNLZH_HEAD', 'UNLZH_GET', 'UNLZH_RUN', 'UNLZH_END',
           'READ_CB', 'WRITE_CB', 'LZH_INIT', 'LZH_RUN', 'LE_SYMBOL', 'LE_POSITION')


class Codec(Machine):
    def __init__(self, library, image, encode=False):
        super().__init__(library, image)
        self.symbols = {name: self.word(0x100 + i * 2) for i, name in enumerate(ENTRIES)}
        self.encode = encode
        self.size = SIZE if encode else 6646

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

    def call(self, entry, budget=2000000000):
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
        assert self.call('LZH_INIT') == 0
        assert self.reads == self.writes == 0
        status = self.call('LZH_RUN')
        assert status == 0, (status, self.mem[self.ctx + 4], self.position, len(self.output))
        assert self.position == len(data) and self.reads == len(data) + 1
        assert int.from_bytes(bytes(self.mem[self.ctx + 24:self.ctx + 28]), 'little') == len(data)
        assert self.word(self.ctx + 20) == sum(data) & 65535
        events = self.reads, self.writes
        assert self.call('LZH_RUN') == 0 and events == (self.reads, self.writes)
        return bytes(self.output)


def reference(data, name=b'TEST.BIN'):
    from test_unlzh import fixture
    ring, cursor, i, tokens = bytearray(b' ' * 2048), 0, 0, []
    matches, overlaps, wraps = 0, 0, 0
    distances = set()
    while i < len(data):
        limit = min(60, len(data) - i)
        best, chosen = 0, 0
        # Enumerate every matching first-byte position using host byte search;
        # this is independent of the assembly's stale-link chain structure.
        positions, start = [], 0
        while True:
            try:
                start = ring.index(data[i], start)
            except ValueError:
                break
            positions.append((cursor - start - 1) % 2048 + 1)
            start += 1
        for distance in sorted(positions):
            n = 1
            while n < limit:
                b = (data[i+n-distance] if n >= distance else ring[(cursor-distance+n) % 2048])
                if b != data[i+n]:
                    break
                n += 1
            if n > best:
                best, chosen = n, distance
                if n == limit:
                    break
        n = best if best >= 3 else 1
        if best >= 3:
            tokens.append((n, chosen))
            matches += 1
            overlaps += n > chosen
            wraps += cursor + n >= 2048
            distances.add(chosen)
        else:
            tokens.append(data[i])
        for b in data[i:i+n]:
            ring[cursor] = b
            cursor = (cursor + 1) % 2048
        i += n
    raw, expected, rebuilds = fixture(tokens, name=name)
    assert expected == data
    return raw, (matches, overlaps, wraps, distances, rebuilds)


def tests(enc, dec):
    from test_unlzh import CODES, LENGTHS
    enc.configure(b'')
    assert enc.call('LZH_INIT') == 0
    for distance in range(1,2049):
        enc.putword(enc.ctx+60,distance)
        enc.mem[enc.ctx+33:enc.ctx+35] = b'\0\0'
        enc.output = bytearray()
        assert enc.call('LE_POSITION') == 0
        upper, lower = divmod(distance-1,32)
        bits = f'{CODES[upper]:0{LENGTHS[upper]}b}' + f'{lower:05b}'
        actual = ''.join(f'{b:08b}' for b in enc.output)
        tail = enc.mem[enc.ctx+34]
        if tail:
            actual += f'{enc.mem[enc.ctx+33]:0{tail}b}'
        assert actual == bits, (distance,actual,bits)
    rng = random.Random(457)
    samples = [b'', b'A', b'\0', b'\x1a', b'\x90', b'\xff', b' ' * 200,
               b'A' * 2, b'A' * 3, b'ABABABA', b'A' * 61, b'A' * 5000,
               bytes(range(256)) * 12, b'CP/M\r\n' * 1500,
               bytes(rng.randrange(256) for _ in range(4000))]
    # Order-3 de Bruijn sequence over bytes 0..31: unique triples mean
    # every data token is literal. Stop tests straddle the exact root-weight
    # reconstruction boundary (initial root weight is 315).
    a, sequence = [0] * 97, []
    def debruijn(t, period):
        if t > 3:
            if 3 % period == 0:
                sequence.extend(a[1:period+1])
        else:
            a[t] = a[t-period]
            debruijn(t+1,period)
            for j in range(a[t-period]+1,32):
                a[t] = j
                debruijn(t+1,t)
    debruijn(1,1)
    sequence = bytes(sequence + sequence[:2])
    assert len({sequence[i:i+3] for i in range(32768)}) == 32768
    samples += [sequence[:n] for n in (32452,32453,32454)]
    samples += [bytes(rng.randrange(256) for _ in range(70001))]
    samples += [bytes(rng.randrange(alphabet) for _ in range(rng.randrange(500,2500)))
                for alphabet in (1,2,3,4,16,32,128,256)]
    # Exact maximum distance and matches crossing ring boundaries.
    base = bytes(rng.randrange(256) for _ in range(2048))
    samples += [base + base[:60], base + base + base[:59]]
    for n in (1, 2, 3, 59, 60, 61, 127, 128, 129, 2047, 2048, 2049):
        samples.append((b'ABCDE' * 500)[:n])
    totals = [0, 0, 0, set(), 0]
    for data in samples:
        raw = enc.compress(data)
        expected, stats = reference(data)
        assert raw == expected, (len(data), 'wire mismatch', next((i for i,(a,b) in enumerate(zip(raw,expected)) if a!=b), None))
        out, used, rebuilds = decode(raw)
        assert out == data and used == len(raw) and rebuilds == stats[4]
        assert enc.word(enc.ctx+58) == rebuilds
        if data == sequence[:32452]:
            assert rebuilds == 0
        if data in (sequence[:32453],sequence[:32454]):
            assert rebuilds == 1
        dec.configure(raw+b'UNREAD')
        assert dec.call('UNLZH_INIT') == dec.call('UNLZH_HEAD') == dec.call('UNLZH_RUN') == 0
        assert dec.output == data and dec.position == len(raw)
        for i in (0,1,2,4):
            totals[i] += stats[i]
        totals[3].update(stats[3])
    assert totals[0] and totals[1] and totals[2] and totals[4] and 2048 in totals[3], totals
    assert len(enc.compress(b'A'*10000)) < 512
    for name in (b'', b'FILE.A  [STAMP]', b'A'*127, b'$DATA.BIN'):
        raw = enc.compress(b'names', name=name)
        assert raw == reference(b'names', name)[0]
        dec.configure(raw)
        assert dec.call('UNLZH_INIT') == dec.call('UNLZH_HEAD') == dec.call('UNLZH_RUN') == 0
        assert dec.output == b'names'
    for size in (0,15,16,SIZE-1):
        enc.configure(b'data',size=size)
        assert enc.call('LZH_INIT') == 11 and not enc.reads and not enc.writes
    for offset,value,detail in ((0,2,1),(1,1,2),(5,1,3),(6,0,4)):
        enc.configure(b'data')
        enc.mem[enc.ctx+offset] = value
        if offset == 6:
            enc.mem[enc.ctx+7] = 0
        assert enc.call('LZH_INIT') == 13 and enc.mem[enc.ctx+4] == detail
    enc.configure(b'data',write=False)
    assert enc.call('LZH_INIT') == 13 and enc.mem[enc.ctx+4] == 5
    enc.configure(b'data',name=b'A'*128)
    assert enc.call('LZH_INIT') == 13 and enc.mem[enc.ctx+4] == 128
    enc.configure(b'data')
    enc.error('LZH_RUN',12,0)
    data = bytes(range(256))*2
    raw = enc.compress(data)
    for offset in (0,1,8,15,32,len(raw)-3,len(raw)-2,len(raw)-1):
        for reason in (0,0x73):
            enc.configure(data)
            assert enc.call('LZH_INIT') == 0
            enc.write_error = offset, reason
            enc.error('LZH_RUN',8,reason)
            assert len(enc.output) == offset
    for offset in (0,1,59,60,61,250,len(data)):
        enc.configure(data)
        assert enc.call('LZH_INIT') == 0
        enc.read_error = offset,0x37
        enc.error('LZH_RUN',7,0x37)
    enc.configure(b'A')
    assert enc.call('LZH_INIT') == 0
    enc.mem[enc.ctx+24:enc.ctx+28] = b'\xff'*4
    enc.error('LZH_RUN',11,0x81)
    assert enc.call('LZH_INIT') == 0
    enc.raw,enc.position,enc.output = b'B',0,bytearray()
    assert enc.call('LZH_RUN') == 0
    assert decode(bytes(enc.output))[0] == b'B'
    # Corrupt a parent to form a cycle. The encoder must reject it without
    # reading/writing past its bounded context or recursing on the stack.
    enc.configure(b'A')
    assert enc.call('LZH_INIT') == 0
    node = enc.word(enc.ctx+4758+(629+65)*2)
    enc.putword(enc.ctx+4758+node*2,node)
    enc.error('LZH_RUN',5,1)
    # Two initialized contexts coexist, with callbacks selected by the caller.
    other = Codec(enc.core,enc.image,True)
    enc.configure(b'context one'*100,address=0x6003)
    assert enc.call('LZH_INIT') == 0
    other.configure(b'context two'*200,address=0xA003)
    assert other.call('LZH_INIT') == 0
    for codec, expected in ((enc,b'context one'*100),(other,b'context two'*200)):
        codec.regs['IX'].value = codec.ctx
        codec.core.set_hooks(codec.symbols['READ_CB'],codec.symbols['WRITE_CB'],codec.hook)
        assert codec.call('LZH_RUN') == 0
        assert decode(bytes(codec.output))[0] == expected
    print(f'Round trips: {len(samples)+4}; {totals[0]} matches, {totals[1]} overlaps, {totals[2]} wraps, {totals[4]} reconstructions.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    parser.add_argument('--z80pack',type=Path,default=Path.home()/'projects/git/z80pack')
    parser.add_argument('--cc',default='cc')
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='bettercpm-lzh-') as temp:
        work=Path(temp)
        includes=tuple(f'{c}.{s}' for c in ('codec','usq','sq','uncr','cr','unlzh','lzh') for s in ('inc','mac'))
        for name in includes:
            shutil.copy2(ROOT/'src/codec'/name,work/name)
        definitions='        ORG 100H\n'+''.join(f'        INCLUDE {n}\n' for n in includes)
        (work/'definitions.mac').write_text(definitions+'        DB 05AH\n        END\n')
        subprocess.run([str(args.assembler),'-e32','-fb','-odefinitions.bin','definitions.mac'],cwd=work,check=True)
        assert (work/'definitions.bin').read_bytes()==b'\x5a'
        coexist=definitions+''.join(f'        {macro}\n' for macro in
                    ('CODEC_CODE','USQ_CODE','SQ_CODE','UNCR_CODE','CR_CODE','UNLZH_CODE','LZH_CODE'))
        (work/'coexist.mac').write_text(coexist+'        END\n')
        subprocess.run([str(args.assembler),'-e32','-fb','-ocoexist.bin','coexist.mac'],cwd=work,check=True)
        source=definitions+'        DW '+','.join(ENTRIES)+'\nREAD_CB: RET\nWRITE_CB: RET\n        CODEC_CODE\n        LZH_CODE\n        UNLZH_CODE\n        END\n'
        (work/'test.mac').write_text(source)
        subprocess.run([str(args.assembler),'-e32','-fb','-otest.bin','-ltest.lst','test.mac'],cwd=work,check=True)
        image=(work/'test.bin').read_bytes()
        (work/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h','simport.h'):
            shutil.copy2(args.z80pack/'z80sim/srcsim'/name,work/name)
        (work/'shim.c').write_text(SHIM)
        core=args.z80pack/'z80core'
        subprocess.run([args.cc,'-shared','-fPIC','-O2',f'-I{work}',f'-I{core}',str(work/'shim.c'),str(core/'simglb.c'),*map(str,sorted(core.glob('simz80*.c'))),'-o',str(work/'core.so')],check=True)
        lib=C.CDLL(str(work/'core.so'))
        enc,dec=Codec(lib,image,True),Codec(lib,image)
        tests(enc,dec)
        print(f'PASS: {enc.cases} LZH cases, {enc.calls} encoder calls; {dec.cases} assembled UNLZH round trips;')
        print(f'LZH code {enc.symbols["UNLZH_INIT"]-enc.symbols["LZH_INIT"]} bytes; context {SIZE} bytes;')
        print('callbacks/EOF/checksum/ABI/canaries/immutable code checked.')


if __name__=='__main__':
    main()
