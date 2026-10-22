#!/usr/bin/env python3
"""Execute assembled USQ with the independent z80pack CPU core.

Requires a host C compiler, z80pack's z80asm and a z80pack source checkout.
Builds a temporary test-only shared core; does not modify/vendor z80pack.
The Python encoder creates fixtures independently of the assembly decoder.
"""
import argparse
import ctypes as C
import heapq
from pathlib import Path
import random
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/codec"
ENTRIES = ("USQ_INIT", "USQ_HEAD", "USQ_GET", "USQ_RUN", "USQ_END",
           "READ_CB", "WRITE_CB")
SIZE = 1440
BASE = 0x100

SHIM = r'''
#include "simdefs.h"
#include "simglb.h"
#include "simz80.h"
BYTE memory[65536];
BYTE io_in(BYTE l, BYTE h) { return 0; }
void io_out(BYTE l, BYTE h, BYTE d) {}
void end_bus_request(void) { bus_mode=0; }
void sleep_for_us(unsigned long n) {}
void sleep_for_ms(unsigned n) {}
uint64_t get_clock_us(void) { return 1; }
static void (*hook)(int);
static WORD readpc, writepc;
void set_hooks(WORD r, WORD w, void (*h)(int)) {
 readpc=r; writepc=w; hook=h;
}
int test_run(WORD address, int budget) {
 PC=address; SP-=2; memory[SP]=255; memory[(SP+1)&65535]=255;
 cpu_error=0; tmax=100000000;
 for(int i=0;i<budget;i++) {
  if(PC==65535) return i;
  if(hook && PC==readpc) hook(0);
  if(hook && PC==writepc) hook(1);
  cpu_state=ST_SINGLE_STEP; cpu_z80();
  if(cpu_error) return -cpu_error;
 }
 return -1000;
}
'''


def header(nodes, checksum=0, name=b"TEST.BIN", payload=b""):
    return (b"\x76\xff" + struct.pack("<H", checksum) + name + b"\0"
            + struct.pack("<H", len(nodes))
            + b"".join(struct.pack("<hh", *node) for node in nodes) + payload)


def squeeze_tokens(tokens, checksum, name=b"TEST.BIN", shuffle=False):
    """Frequency Huffman encoder, explicit tree, least-significant-bit first."""
    freq = {}
    for token in tokens + [256]:
        freq[token] = freq.get(token, 0) + 1
    heap = [(count, serial, token) for serial, (token, count)
            in enumerate(sorted(freq.items()))]
    heapq.heapify(heap)
    serial = len(heap)
    while len(heap) > 1:
        wa, _, a = heapq.heappop(heap)
        wb, _, b = heapq.heappop(heap)
        heapq.heappush(heap, (wa + wb, serial, (a, b)))
        serial += 1
    root = heap[0][2]
    nodes, codes = [], {}

    def visit(tree, path):
        if isinstance(tree, int):
            codes[tree] = path
            return -tree - 1
        index = len(nodes)
        nodes.append(None)
        nodes[index] = (visit(tree[0], path + [0]), visit(tree[1], path + [1]))
        return index

    visit(root, [])
    if shuffle and len(nodes) > 2:
        order = list(range(1, len(nodes)))
        random.Random(42).shuffle(order)
        order = [0] + order
        mapping = {old: new for new, old in enumerate(order)}
        nodes = [tuple(mapping[c] if c >= 0 else c for c in nodes[old])
                 for old in order]
    bits = [bit for token in tokens + [256] for bit in codes[token]]
    payload = bytearray((len(bits) + 7) // 8)
    for index, bit in enumerate(bits):
        payload[index // 8] |= bit << (index % 8)
    return header(nodes, checksum, name, payload)


def squeeze(data, **kwargs):
    tokens = []
    i = 0
    while i < len(data):
        byte = data[i]
        count = 1
        while i + count < len(data) and data[i + count] == byte and count < 255:
            count += 1
        if byte == 0x90:
            tokens.extend([0x90, 0] * count)
        elif count >= 3:
            tokens.extend([byte, 0x90, count])
        else:
            tokens.extend([byte] * count)
        i += count
    return squeeze_tokens(tokens, sum(data) & 65535, **kwargs)


class Machine:
    def __init__(self, library, image):
        self.core = library
        self.mem = (C.c_ubyte * 65536).in_dll(library, "memory")
        self.regs = {}
        for name in ("A", "B", "C", "D", "E", "H", "L", "A_", "B_", "C_",
                     "D_", "E_", "H_", "L_"):
            self.regs[name] = C.c_ubyte.in_dll(library, name)
        for name in ("IX", "IY", "SP", "PC"):
            self.regs[name] = C.c_ushort.in_dll(library, name)
        for name in ("F", "F_"):
            self.regs[name] = C.c_int.in_dll(library, name)
        self.image = image
        self.mem[BASE:BASE + len(image)] = image
        self.symbols = {name: self.word(BASE + 2 * i) for i, name in enumerate(ENTRIES)}
        self.hook = C.CFUNCTYPE(None, C.c_int)(self.callback)
        library.set_hooks.argtypes = [C.c_ushort, C.c_ushort, C.CFUNCTYPE(None, C.c_int)]
        library.test_run.argtypes = [C.c_ushort, C.c_int]
        library.test_run.restype = C.c_int
        library.set_hooks(self.symbols["READ_CB"], self.symbols["WRITE_CB"], self.hook)
        self.calls = 0
        self.cases = 0

    def word(self, address):
        return self.mem[address] | self.mem[address + 1] << 8

    def putword(self, address, value):
        self.mem[address] = value & 255
        self.mem[address + 1] = value >> 8

    def configure(self, raw, write=True, size=SIZE, address=0x8003):
        self.ctx = address
        self.raw, self.position, self.output = raw, 0, bytearray()
        self.reads = self.writes = 0
        self.read_error = self.write_error = None
        self.callback_exception = None
        self.mem[address - 1:address + SIZE + 1] = bytes([0xA5]) * (SIZE + 2)
        self.mem[address:address + 16] = bytes(16)
        self.mem[address] = 1
        self.putword(address + 6, self.symbols["READ_CB"])
        self.putword(address + 8, self.symbols["WRITE_CB"] if write else 0)
        self.putword(address + 12, 0x7000)
        self.putword(address + 14, size)
        self.regs["IX"].value = address
        self.regs["SP"].value = 0xF000
        self.regs["IY"].value = 0xBEEF
        for i, name in enumerate(("A_", "B_", "C_", "D_", "E_", "H_", "L_", "F_")):
            self.regs[name].value = 0x31 + i
        self.cases += 1

    def callback(self, kind):
        try:
            # Hooks supply stream events at real RET callbacks. Deliberately
            # destroy all caller-saved work registers on each invocation.
            if kind == 0:
                self.reads += 1
                if self.read_error and self.position == self.read_error[0]:
                    value, carry = self.read_error[1], True
                elif self.position == len(self.raw):
                    value, carry = 0, True
                else:
                    value, carry = self.raw[self.position], False
                    self.position += 1
            else:
                self.writes += 1
                if self.write_error and len(self.output) == self.write_error[0]:
                    value, carry = self.write_error[1], True
                else:
                    self.output.append(self.regs["A"].value)
                    value, carry = 0xEE, False
            self.regs["A"].value = value
            self.regs["F"].value = 0x40 | int(carry)
            for i, name in enumerate(("B", "C", "D", "E", "H", "L")):
                self.regs[name].value = 0xD1 + i
        except BaseException as error:
            self.callback_exception = error
            self.regs["A"].value = 255
            self.regs["F"].value = 1

    def call(self, entry, budget=3000000):
        names = ("IX", "IY", "SP", "A_", "B_", "C_", "D_", "E_", "H_", "L_", "F_")
        preserved = [self.regs[name].value for name in names]
        configuration = bytes(self.mem[self.ctx:self.ctx + 2]) + bytes(
            self.mem[self.ctx + 5:self.ctx + 16])
        steps = self.core.test_run(self.symbols[entry], budget)
        assert steps >= 0, (entry, "CPU error/budget", steps, hex(self.regs["PC"].value))
        assert not self.callback_exception, self.callback_exception
        assert preserved == [self.regs[name].value for name in names], entry
        assert configuration == (bytes(self.mem[self.ctx:self.ctx + 2]) + bytes(
            self.mem[self.ctx + 5:self.ctx + 16])), entry
        assert self.mem[self.ctx - 1] == self.mem[self.ctx + SIZE] == 0xA5, entry
        assert bytes(self.mem[BASE:BASE + len(self.image)]) == self.image, entry
        self.calls += 1
        return (self.regs["A"].value if self.regs["F"].value & 1 else 0)

    def open(self, raw, **kwargs):
        self.configure(raw, **kwargs)
        assert self.call("USQ_INIT") == 0
        return self.call("USQ_HEAD")

    def expect_error(self, entry, status, detail=None):
        assert self.call(entry) == status, (entry, status, self.mem[self.ctx + 3])
        assert self.mem[self.ctx + 2] == 4
        assert self.mem[self.ctx + 3] == status
        if detail is not None:
            assert self.mem[self.ctx + 4] == detail, (status, detail, self.mem[self.ctx + 4])
        before = bytes(self.mem[self.ctx:self.ctx + SIZE])
        counts = self.reads, self.writes
        for repeated in ("USQ_GET", "USQ_RUN", "USQ_END", "USQ_HEAD"):
            assert self.call(repeated) == status
            assert bytes(self.mem[self.ctx:self.ctx + SIZE]) == before
            assert (self.reads, self.writes) == counts

    def count(self):
        return int.from_bytes(bytes(self.mem[self.ctx + 28:self.ctx + 32]), "little")


def tests(m):
    # Hand-encoded vectors do not pass through the fixture encoder. One A:
    # root children -66/-257, bits 0 then 1 -> 02h. Literal DLE: root
    # -145/1, node 1 -1/-257, bits 0,10,11 -> 1Ah (LSB first).
    for raw, output in (
        (bytes.fromhex("76ff4100412e545854000100befffffe02"), b"A"),
        (bytes.fromhex("76ff9000444c450002006fff0100fffffffe1a"), b"\x90"),
    ):
        assert m.open(raw) == 0
        assert m.call("USQ_RUN") == 0 and m.output == output
    rng = random.Random(12345)
    samples = [b"", b"A", b"\0", b"\x1a", b"\x90", b"\xff",
               b"ABABABA", b"hello\r\nworld\n", bytes(range(256)),
               bytes(range(256)) * 4, b"A" * 1000, b"\x90" * 512,
               b"B" * 2 + b"C" * 3 + b"D" * 254 + b"E" * 255 + b"F" * 256,
               bytes(rng.randrange(256) for _ in range(2048))]
    for data in samples:
        raw = squeeze(data, shuffle=True)
        for mode in ("run", "get", "end", "mixed"):
            assert m.open(raw + b"UNREAD-PADDING", write=mode != "end") == 0
            assert m.reads > 0 and m.writes == 0
            if mode == "get":
                result = bytearray()
                while True:
                    status = m.call("USQ_GET")
                    if status:
                        assert status == 1
                        break
                    result.append(m.regs["A"].value)
                assert result == data
            elif mode == "end":
                assert m.call("USQ_END") == 0
                assert not m.output
            elif mode == "mixed":
                first = bytearray()
                for _ in range(min(3, len(data))):
                    assert m.call("USQ_GET") == 0
                    first.append(m.regs["A"].value)
                assert m.call("USQ_RUN") == 0
                assert first + m.output == data
            else:
                assert m.call("USQ_RUN") == 0
                assert m.output == data
            assert m.count() == len(data)
            assert m.word(m.ctx + 18) == sum(data) & 65535
            assert m.position == len(raw), (len(data), m.position, len(raw))
            counts = m.reads, m.writes
            assert m.call("USQ_GET") == m.call("USQ_GET") == 1
            assert m.call("USQ_RUN") == m.call("USQ_END") == 0
            assert (m.reads, m.writes) == counts

    # Header edge cases, zero-node representation, bounded filename bytes.
    for name in (b"", b"X" * 127, b"\x80\xffNAME.BIN"):
        assert m.open(squeeze(b"abc", name=name)) == 0
        assert m.mem[m.ctx + 27] == len(name)
        assert bytes(m.mem[m.ctx + 32:m.ctx + 33 + len(name)]) == name + b"\0"
        assert m.call("USQ_RUN") == 0
    m.configure(header([], name=b"X" * 128))
    assert m.call("USQ_INIT") == 0
    m.expect_error("USQ_HEAD", 5, 5)
    assert m.open(header([], checksum=1)) == 0
    m.expect_error("USQ_GET", 6, 0)

    malformed = [
        (header([(-1, -257)]).replace(b"\x76\xff", b"\x76\x00", 1), 2, 0),
        (header([(0, -257)]), 5, 3),                 # root cycle
        (header([(1, 1), (-1, -257)]), 5, 3),       # shared internal child
        (header([(1, -257)]), 5, 2),               # out-of-range child
        (header([(-258, -257)]), 5, 2),            # invalid negative leaf
        (header([(-1, -2)]), 5, 3),                # no EOF
        (header([(-1, -257), (-2, -257)]), 5, 3),   # unreachable node
        (header([(1, -257), (2, -1), (1, -2)]), 5, 3),  # deeper cycle
        (header([(-1, -257)] * 257), 5, 1),
    ]
    for raw, status, detail in malformed:
        m.configure(raw)
        assert m.call("USQ_INIT") == 0
        m.expect_error("USQ_HEAD", status, detail)
        assert m.writes == 0

    # Every byte-boundary truncation of a real stream, including all header
    # fields and the payload. No substituted physical EOF may pass as SPEOF.
    raw = squeeze(bytes(range(256)) * 2)
    for end in range(len(raw)):
        m.configure(raw[:end])
        assert m.call("USQ_INIT") == 0
        status = m.call("USQ_HEAD")
        if status:
            assert status == 4, (end, status)
            m.expect_error("USQ_HEAD", 4)
        else:
            m.expect_error("USQ_RUN", 4)

    # Malformed repetition count or history. Encoded EOF cannot be a count.
    for tokens in ([0x90, 2], [65, 0x90, 1], [65, 0x90]):
        assert m.open(squeeze_tokens(list(tokens), 0)) == 0
        m.expect_error("USQ_RUN", 5, 4)
    # Count 2 is accepted; a literal DLE establishes valid repeat history.
    for tokens, output in (([65, 0x90, 2], b"AA"),
                           ([0x90, 0, 0x90, 3], b"\x90" * 3)):
        assert m.open(squeeze_tokens(tokens, sum(output))) == 0
        assert m.call("USQ_RUN") == 0 and m.output == output

    # Checksum mismatch must be detected by all three consumption paths.
    raw = bytearray(squeeze(b"checksum"))
    raw[2] ^= 1
    for mode in ("USQ_RUN", "USQ_END"):
        assert m.open(raw) == 0
        m.expect_error(mode, 6, 0)
    assert m.open(raw) == 0
    for _ in b"checksum":
        assert m.call("USQ_GET") == 0
    m.expect_error("USQ_GET", 6, 0)

    raw = squeeze(b"callback errors" * 30)
    # Inject errors in the signature, checksum, name, tree and payload.
    assert m.open(raw) == 0
    header_end = m.position
    for position in (0, 2, 5, 16, header_end, header_end + 1):
        m.configure(raw)
        m.read_error = (position, 0xE7)
        assert m.call("USQ_INIT") == 0
        if position < header_end:
            m.expect_error("USQ_HEAD", 7, 0xE7)
        else:
            assert m.call("USQ_HEAD") == 0
            m.expect_error("USQ_RUN", 7, 0xE7)
    for reason in (0, 255):
        assert m.open(raw) == 0
        m.write_error = (3, reason)
        m.expect_error("USQ_RUN", 8, reason)
        assert len(m.output) == 3 and m.count() == 4
    assert m.open(raw, write=False) == 0
    before = m.position
    m.expect_error("USQ_RUN", 13, 5)
    assert m.position == before

    # Configuration and state boundaries do not consume any input.
    for size in (0, 15, 16, SIZE - 1):
        m.configure(raw, size=size)
        before = bytes(m.mem[m.ctx:m.ctx + SIZE])
        assert m.call("USQ_INIT") == 11
        assert not m.reads
        if size < 16:
            assert bytes(m.mem[m.ctx:m.ctx + SIZE]) == before
        else:
            assert bytes(m.mem[m.ctx + 16:m.ctx + SIZE]) == before[16:]
    for entry in ("USQ_GET", "USQ_RUN", "USQ_END"):
        m.configure(raw)
        assert m.call("USQ_INIT") == 0
        m.expect_error(entry, 12, 1)
        assert not m.reads

    # Reinitialize after failure and reuse the same allocation.
    assert m.call("USQ_INIT") == 0
    assert m.call("USQ_HEAD") == m.call("USQ_RUN") == 0
    assert m.output == b"callback errors" * 30

    # Full 256-node tree and pathological depth (256 edges to EOF).
    nodes = [(i + 1, -(i + 1)) for i in range(255)] + [(-256, -257)]
    # Use a generated maximum-node Huffman tree for successful full alphabet.
    assert m.open(squeeze(bytes(range(256)), shuffle=True)) == 0
    assert m.word(m.ctx + 20) == 256
    assert m.call("USQ_RUN") == 0
    # Deepest EOF requires 255 zero edges followed by one right edge.
    assert m.open(header(nodes, payload=bytes(31) + b"\x80")) == 0
    assert m.call("USQ_END") == 0

    # Counter carries independently of checksum and pending repeats.
    assert m.open(squeeze(b"A")) == 0
    m.mem[m.ctx + 28:m.ctx + 32] = b"\xff\xff\xff\xff"
    assert m.call("USQ_GET") == 0 and m.count() == 0
    assert m.call("USQ_GET") == 1

    # A short preview followed by END still checks all remaining bytes.
    raw = squeeze(b"preview and verify" * 30)
    assert m.open(raw, write=False) == 0
    for _ in range(4):
        assert m.call("USQ_GET") == 0
    assert m.call("USQ_END") == 0
    assert m.count() == len(b"preview and verify" * 30) and m.writes == 0

    # Two interleaved contexts use one immutable decoder. Stream adapters
    # switch their caller state together with IX, as CX_USER adapters would.
    states = []
    for address, data in ((0x8003, b"first stream" * 4),
                          (0x9005, b"second stream" * 5)):
        assert m.open(squeeze(data), address=address) == 0
        assert m.call("USQ_GET") == 0
        assert m.regs["A"].value == data[0]
        states.append((address, m.raw, m.position, m.reads, m.writes, m.output, data))
    for address, raw, position, reads, writes, output, data in states:
        m.ctx = address
        m.regs["IX"].value = address
        m.raw, m.position, m.reads, m.writes, m.output = raw, position, reads, writes, output
        assert m.call("USQ_RUN") == 0
        assert m.output == data[1:] and m.count() == len(data)

    # Deterministic malformed mutations must terminate without context writes
    # outside bounds, CPU traps, stack damage or alternate-register damage.
    raw = squeeze(b"mutation corpus" * 4)
    for _ in range(100):
        mutated = bytearray(raw)
        pos = rng.randrange(len(mutated))
        mutated[pos] ^= 1 << rng.randrange(8)
        m.configure(mutated)
        assert m.call("USQ_INIT") == 0
        if m.call("USQ_HEAD") == 0:
            m.call("USQ_RUN")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembler", type=Path, default=Path.home() / "bin/z80asm")
    parser.add_argument("--z80pack", type=Path,
                        default=Path.home() / "projects/git/z80pack")
    parser.add_argument("--cc", default="cc")
    args = parser.parse_args()
    core = args.z80pack / "z80core"
    with tempfile.TemporaryDirectory(prefix="bettercpm-usq-") as directory:
        work = Path(directory)
        (work / "sim.h").write_text("#define DEF_CPU Z80\n#define EXCLUDE_I8080\n")
        for name in ("simmem.h", "simport.h"):
            shutil.copy2(args.z80pack / "z80sim/srcsim" / name, work / name)
        (work / "shim.c").write_text(SHIM)
        subprocess.run([args.cc, "-shared", "-fPIC", "-O2", f"-I{work}", f"-I{core}",
                        str(work / "shim.c"), str(core / "simglb.c"),
                        *map(str, sorted(core.glob("simz80*.c"))),
                        "-o", str(work / "core.so")], check=True)
        for name in ("codec.inc", "codec.mac", "usq.inc", "usq.mac"):
            shutil.copy2(SOURCE / name, work / name)
        text = "        ORG 100H\n"
        text += "".join(f"        INCLUDE {name}\n" for name in
                        ("codec.inc", "codec.mac", "usq.inc", "usq.mac"))
        text += "".join(f"        DW {name}\n" for name in ENTRIES)
        text += "        CODEC_CODE\n        USQ_CODE\nREAD_CB: RET\nWRITE_CB: RET\n        END\n"
        (work / "test.mac").write_text(text)
        subprocess.run([str(args.assembler), "-e32", "-fb", "-otest.bin", "-ltest.lst",
                        "test.mac"], cwd=work, check=True)
        image = (work / "test.bin").read_bytes()
        if image[:BASE] == bytes(BASE):
            image = image[BASE:]
        machine = Machine(C.CDLL(str(work / "core.so")), image)
        tests(machine)
        print(f"PASS: {machine.cases} USQ cases, {machine.calls} assembled entry calls.")
        print(f"Code: {len(image) - len(ENTRIES) * 2 - 2} bytes including common helpers;")
        print("context: 1440 bytes; IX/IY/alternate banks/SP/canaries/code immutability checked.")


if __name__ == "__main__":
    main()
