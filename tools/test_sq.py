#!/usr/bin/env python3
"""Execute real SQ code on z80pack and round-trip through real USQ code.

Requires z80pack sources, a host C compiler and z80asm. Temporary CPU core
is built without modifying/vendoring z80pack. Host decoding also checks the
format independently; encoded trees need not match a historical encoder.
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

from test_usq import BASE, ENTRIES, Machine, SHIM

ROOT = Path(__file__).resolve().parents[1]
SIZE = 3524
EXTRA = ("SQ_INIT", "SQ_SCAN", "SQ_RUN", "REWIND_CB", "S_RESCALE",
         "S_BUILD_TREE", "S_ENCODE", "S_RLE", "S_READ", "S_HEADER", "S_WRITE")


def host_decode(raw, record_padding=False):
    assert raw[:2] == b"\x76\xff"
    checksum, = struct.unpack_from("<H", raw, 2)
    end = raw.index(0, 4)
    name = raw[4:end]
    count, = struct.unpack_from("<H", raw, end + 1)
    assert count <= 256
    nodes = [struct.unpack_from("<hh", raw, end + 3 + i * 4) for i in range(count)]
    offset = end + 3 + count * 4
    bit = 0

    def symbol():
        nonlocal bit
        if not nodes:
            return 256
        index = 0
        while index >= 0:
            side = (raw[offset + bit // 8] >> (bit % 8)) & 1
            bit += 1
            index = nodes[index][side]
        return -index - 1

    output = bytearray()
    while True:
        value = symbol()
        if value == 256:
            break
        if value == 0x90:
            repeat = symbol()
            if repeat == 0:
                output.append(0x90)
            else:
                assert 2 <= repeat <= 255 and output
                output.extend([output[-1]] * (repeat - 1))
        else:
            output.append(value)
    assert sum(output) & 65535 == checksum
    used = offset + (bit + 7) // 8
    if record_padding:
        assert len(raw) % 128 == 0 and raw[used:] == b"\x1a" * (-used % 128)
    else:
        assert used == len(raw), "unexpected trailing output"
    return name, bytes(output)


class Encoder(Machine):
    def __init__(self, library, image):
        super().__init__(library, image)
        for index, name in enumerate(EXTRA, len(ENTRIES)):
            self.symbols[name] = self.word(BASE + index * 2)
        library.set_rewindpc.argtypes = [C.c_ushort]

    def configure(self, raw, name=b"TEST.BIN", size=SIZE, write=True, rewind=True,
                  address=0x7003):
        self.ctx = address
        self.raw, self.position, self.output = raw, 0, bytearray()
        self.reads = self.writes = self.rewinds = self.passnumber = 0
        self.read_error = self.write_error = self.rewind_error = None
        self.read_error_pass = None
        self.second = None
        self.callback_exception = None
        self.mem[address - 1:address + SIZE + 1] = bytes([0xA5]) * (SIZE + 2)
        self.mem[address:address + 16] = bytes(16)
        self.mem[address] = 1
        self.putword(address + 6, self.symbols["READ_CB"])
        self.putword(address + 8, self.symbols["WRITE_CB"] if write else 0)
        self.putword(address + 10, self.symbols["REWIND_CB"] if rewind else 0)
        self.putword(address + 12, 0x6000)
        self.putword(address + 14, size)
        # No bounded terminator when name >=128; deliberately test rejection.
        self.mem[address + 64:address + 192] = (name + bytes(128))[:128]
        self.regs["IX"].value = address
        self.regs["SP"].value = 0xF000
        self.regs["IY"].value = 0xBEEF
        for i, name in enumerate(("A_", "B_", "C_", "D_", "E_", "H_", "L_", "F_")):
            self.regs[name].value = 0x31 + i
        self.core.set_hooks(self.symbols["READ_CB"], self.symbols["WRITE_CB"], self.hook)
        self.core.set_rewindpc(self.symbols["REWIND_CB"])
        self.cases += 1

    def callback(self, kind):
        if kind != 2:
            saved = self.read_error
            if self.read_error_pass is not None and self.passnumber != self.read_error_pass:
                self.read_error = None
            super().callback(kind)
            self.read_error = saved
            return
        try:
            self.rewinds += 1
            if self.rewind_error is not None:
                value, carry = self.rewind_error, True
            else:
                self.position = 0
                self.passnumber += 1
                if self.second is not None:
                    self.raw = self.second
                value, carry = 0xA7, False
            self.regs["A"].value = value
            self.regs["F"].value = 0x40 | int(carry)
            for i, name in enumerate(("B", "C", "D", "E", "H", "L")):
                self.regs[name].value = 0xD1 + i
        except BaseException as error:
            self.callback_exception = error

    def call(self, entry, budget=100000000):
        names = ("IX", "IY", "SP", "A_", "B_", "C_", "D_", "E_", "H_", "L_", "F_")
        saved = [self.regs[name].value for name in names]
        config = bytes(self.mem[self.ctx:self.ctx + 2]) + bytes(
            self.mem[self.ctx + 5:self.ctx + 16])
        filename = bytes(self.mem[self.ctx + 64:self.ctx + 192])
        steps = self.core.test_run(self.symbols[entry], budget)
        assert steps >= 0, (entry, steps, hex(self.regs["PC"].value))
        assert not self.callback_exception, self.callback_exception
        assert saved == [self.regs[name].value for name in names], entry
        assert config == bytes(self.mem[self.ctx:self.ctx + 2]) + bytes(
            self.mem[self.ctx + 5:self.ctx + 16]), entry
        assert filename == bytes(self.mem[self.ctx + 64:self.ctx + 192]), entry
        assert self.mem[self.ctx - 1] == self.mem[self.ctx + SIZE] == 0xA5, entry
        assert bytes(self.mem[BASE:BASE + len(self.image)]) == self.image, entry
        self.calls += 1
        return self.regs["A"].value if self.regs["F"].value & 1 else 0

    def squeeze(self, raw, name=b"TEST.BIN"):
        self.configure(raw, name)
        assert self.call("SQ_INIT") == 0
        assert (self.reads, self.writes, self.rewinds) == (0, 0, 0)
        assert self.call("SQ_SCAN") == 0
        assert self.mem[self.ctx + 2] == 2 and not self.output
        assert self.rewinds == 1 and self.position == 0
        assert self.word(self.ctx + 18) == sum(raw) & 65535
        assert int.from_bytes(bytes(self.mem[self.ctx + 36:self.ctx + 40]), "little") == len(raw)
        assert self.call("SQ_RUN") == 0
        assert self.reads == (len(raw) + 1) * 2
        assert self.rewinds == 1 and self.position == len(raw)
        before = self.reads, self.writes, self.rewinds
        assert self.call("SQ_RUN") == 0
        assert (self.reads, self.writes, self.rewinds) == before
        return bytes(self.output)

    def error(self, entry, status, detail=None):
        assert self.call(entry) == status, (entry, status, self.mem[self.ctx + 3])
        assert self.mem[self.ctx + 2] == 4
        if detail is not None:
            assert self.mem[self.ctx + 4] == detail
        before = bytes(self.mem[self.ctx:self.ctx + SIZE])
        counts = self.reads, self.writes, self.rewinds
        for entry in ("SQ_SCAN", "SQ_RUN"):
            assert self.call(entry) == status
            assert bytes(self.mem[self.ctx:self.ctx + SIZE]) == before
            assert (self.reads, self.writes, self.rewinds) == counts


def tests(m):
    roundtrips = 0

    def verify(raw, original, name=b"TEST.BIN"):
        nonlocal roundtrips
        assert host_decode(raw) == (name, original)
        decoder = Machine(m.core, m.image)
        m.core.set_rewindpc(0xFFFF)
        assert decoder.open(raw, address=0x9005) == 0
        assert decoder.call("USQ_RUN", budget=100000000) == 0
        assert decoder.output == original
        assert decoder.position == len(raw)
        roundtrips += 1

    rng = random.Random(1818)
    samples = [b"", b"A", b"\0", b"\x90", b"\x1a", b"\xff",
               bytes(range(256)), bytes(range(256)) * 8,
               b"\x90" * 600, b"\0" * 70000,
               bytes(range(256)) * 260,  # rescaling + 32-bit original count
               bytes(range(2, 256)) + b"\0\1" * 20000,
               bytes(rng.randrange(256) for _ in range(4096))]
    for length in (1, 2, 3, 4, 254, 255, 256, 257, 510, 511):
        samples.append(b"A" * length + b"B" + b"C" * length)
    for raw in samples:
        encoded = m.squeeze(raw)
        if len(raw) > 65000 and len(set(raw)) == 256:
            assert m.word(m.ctx + 20) < 32768
        verify(encoded, raw)
    # Known hand-encoded streams establish byte order and bit orientation
    # independently of either round-trip decoder.
    assert m.squeeze(b"A", b"A.TXT") == bytes.fromhex("76ff4100412e545854000100befffffe02")
    assert m.squeeze(b"", b"") == bytes.fromhex("76ff0000000000")
    # Boundary filenames are emitted exactly, including arbitrary high bits;
    # filesystem naming policy belongs to the utility, not the codec.
    for name in (b"", b"A" * 127, b"\x80\xffNAME"):
        encoded = m.squeeze(b"name", name)
        verify(encoded, b"name", name)
    assert len(m.squeeze(b"A" * 10000)) < 256

    # Arrange Fibonacci symbol counts without adjacent repeats, so RLE does
    # not hide the skew. This exercises actual codes longer than 16 bits.
    # EOF supplies the other weight-1 leaf in the Fibonacci distribution.
    counts = [1, 2]
    for _ in range(18):
        counts.append(counts[-1] + counts[-2])
    heap = [(-count, value) for value, count in enumerate(counts)]
    heapq.heapify(heap)
    data = bytearray()
    previous = None
    while heap:
        count, value = heapq.heappop(heap)
        data.append(value)
        if previous is not None:
            heapq.heappush(heap, previous)
        previous = (count + 1, value) if count < -1 else None
    assert previous is None
    encoded = m.squeeze(bytes(data))
    deepest = 0
    for symbol in range(257):
        index, depth = symbol, 0
        while True:
            parent = m.word(m.ctx + 1218 + index * 2)
            if parent == 65535:
                break
            depth += 1
            index = parent & 32767
            assert depth <= 256
        deepest = max(deepest, depth)
    assert deepest > 16, deepest
    verify(encoded, bytes(data))

    # Deterministic output and many small binary/RLE mixtures.
    assert m.squeeze(b"determinism" * 10) == m.squeeze(b"determinism" * 10)
    for _ in range(30):
        raw = bytes(rng.randrange(8) if rng.randrange(2) else 0x90
                    for _ in range(rng.randrange(512)))
        verify(m.squeeze(raw), raw)

    # Preflight failures must not read, write or rewind.
    for options, status in (({"write": False}, 13), ({"rewind": False}, 9),
                            ({"size": 16}, 11), ({"size": SIZE - 1}, 11),
                            ({"name": b"A" * 128}, 13)):
        m.configure(b"abc", **options)
        m.error("SQ_INIT", status)
        assert (m.reads, m.writes, m.rewinds) == (0, 0, 0)
    for size in (0, 15):
        m.configure(b"abc", size=size)
        before = bytes(m.mem[m.ctx:m.ctx + SIZE])
        assert m.call("SQ_INIT") == 11
        assert bytes(m.mem[m.ctx:m.ctx + SIZE]) == before

    for phase in (0, 1):
        m.configure(b"abc")
        if phase:
            assert m.call("SQ_INIT") == 0
        m.error("SQ_RUN", 12, phase)
        assert (m.reads, m.writes, m.rewinds) == (0, 0, 0)
    m.configure(b"abc")
    assert m.call("SQ_INIT") == m.call("SQ_SCAN") == 0
    m.error("SQ_SCAN", 12, 2)

    # Rewind failure occurs before any header or payload is written.
    for reason in (0, 255):
        m.configure(b"abc")
        m.rewind_error = reason
        assert m.call("SQ_INIT") == 0
        m.error("SQ_SCAN", 10, reason)
        assert not m.output and m.rewinds == 1
    for passnumber in (0, 1):
        for position in (0, 5):
            m.configure(b"callbacks" * 20)
            m.read_error = (position, 0xE7)
            m.read_error_pass = passnumber
            assert m.call("SQ_INIT") == 0
            if passnumber == 0:
                m.error("SQ_SCAN", 7, 0xE7)
                assert not m.output and not m.rewinds
            else:
                assert m.call("SQ_SCAN") == 0
                m.error("SQ_RUN", 7, 0xE7)

    # Header, tree, payload, and final partial-byte output failures.
    for after in (0, 1, 3, 5, 18, 30, 1050, 1120):
        m.configure(bytes(range(256)))
        assert m.call("SQ_INIT") == m.call("SQ_SCAN") == 0
        m.write_error = (after, 0 if after % 2 else 255)
        m.error("SQ_RUN", 8, m.write_error[1])
        assert len(m.output) == after
    raw = b"A"
    length = len(m.squeeze(raw))
    m.configure(raw)
    assert m.call("SQ_INIT") == m.call("SQ_SCAN") == 0
    m.write_error = (length - 1, 17)
    m.error("SQ_RUN", 8, 17)

    # Changed second-pass input: new symbol, different length, different sum.
    for original, second in ((b"AAA", b"ABA"), (b"AB", b"ABAB"),
                              (b"AB", b"AA"), (b"", b"A"), (b"A", b"")):
        m.configure(original)
        m.second = second
        assert m.call("SQ_INIT") == m.call("SQ_SCAN") == 0
        m.error("SQ_RUN", 6, 2)

    # Counter overflow is an explicit failure, not a wrapped stable count.
    m.configure(b"A")
    assert m.call("SQ_INIT") == 0
    m.mem[m.ctx + 32:m.ctx + 36] = b"\xff" * 4
    m.error("SQ_SCAN", 11, 3)
    assert not m.output
    # Recovery reinitializes working arrays while preserving the name.
    m.position = m.reads = 0
    assert m.call("SQ_INIT") == m.call("SQ_SCAN") == m.call("SQ_RUN") == 0
    verify(bytes(m.output), b"A")

    # Separate contexts can pause after SCAN and share a single code image.
    # Save the adapters' caller-owned state and reactivate it together with IX.
    contexts = []
    for address, original in ((0x6003, b"first context" * 30),
                              (0x8005, b"second context" * 40)):
        m.configure(original, address=address)
        assert m.call("SQ_INIT") == m.call("SQ_SCAN") == 0
        contexts.append((address, original, m.reads))
    outputs = []
    for address, original, reads in contexts:
        m.ctx = address
        m.regs["IX"].value = address
        m.raw, m.position, m.output = original, 0, bytearray()
        m.reads, m.writes, m.rewinds = reads, 0, 1
        m.passnumber = 1
        assert m.call("SQ_RUN") == 0
        outputs.append((bytes(m.output), original))
    for encoded, original in outputs:
        verify(encoded, original)

    # Exercise the advertised 256-edge path capacity with a deliberately
    # constructed valid tree. This boundary is deeper than the 16-bit
    # weights normally produce, and checks the final path byte/canary.
    m.configure(b"\0")
    assert m.call("SQ_INIT") == 0
    for i in range(256):
        node, left, right = 257 + i, (0 if i == 0 else 256 + i), i + 1
        m.putword(m.ctx + 2244 + i * 4, left)
        m.putword(m.ctx + 2244 + i * 4 + 2, right)
        m.putword(m.ctx + 1218 + left * 2, node)
        m.putword(m.ctx + 1218 + right * 2, node | 0x8000)
    m.putword(m.ctx + 22, 512)
    m.putword(m.ctx + 60, 256)
    m.mem[m.ctx + 41] = 1
    assert m.call("S_HEADER") == 0
    m.regs["D"].value = m.regs["E"].value = 0
    assert m.call("S_ENCODE") == 0
    assert m.word(m.ctx + 42) == 256
    m.regs["D"].value, m.regs["E"].value = 1, 0
    assert m.call("S_ENCODE") == 0
    m.regs["A"].value = m.mem[m.ctx + 40]
    assert m.call("S_WRITE") == 0
    assert bytes(m.output[-33:]) == bytes(32) + b"\x01"
    verify(bytes(m.output), b"\0")
    return roundtrips, deepest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembler", type=Path, default=Path.home() / "bin/z80asm")
    parser.add_argument("--z80pack", type=Path, default=Path.home() / "projects/git/z80pack")
    parser.add_argument("--cc", default="cc")
    args = parser.parse_args()
    core = args.z80pack / "z80core"
    with tempfile.TemporaryDirectory(prefix="bettercpm-sq-") as directory:
        work = Path(directory)
        (work / "sim.h").write_text("#define DEF_CPU Z80\n#define EXCLUDE_I8080\n")
        for name in ("simmem.h", "simport.h"):
            shutil.copy2(args.z80pack / "z80sim/srcsim" / name, work / name)
        shim = SHIM.replace("static WORD readpc, writepc;", "static WORD readpc, writepc, rewindpc;\n"
                            "void set_rewindpc(WORD p) { rewindpc=p; }")
        shim = shim.replace("if(hook && PC==writepc) hook(1);",
                            "if(hook && PC==writepc) hook(1);\n  if(hook && PC==rewindpc) hook(2);")
        (work / "shim.c").write_text(shim)
        subprocess.run([args.cc, "-shared", "-fPIC", "-O2", f"-I{work}", f"-I{core}",
                        str(work / "shim.c"), str(core / "simglb.c"),
                        *map(str, sorted(core.glob("simz80*.c"))), "-o", str(work / "core.so")], check=True)
        names = ("codec.inc", "codec.mac", "usq.inc", "usq.mac", "sq.inc", "sq.mac")
        for name in names:
            shutil.copy2(ROOT / "src/codec" / name, work / name)
        text = "        ORG 100H\n" + "".join(f"        INCLUDE {name}\n" for name in names)
        text += "".join(f"        DW {name}\n" for name in ENTRIES + EXTRA)
        text += ("        CODEC_CODE\n        USQ_CODE\nSQ_START:\n        SQ_CODE\n"
                 "READ_CB: RET\nWRITE_CB: RET\nREWIND_CB: RET\n        END\n")
        (work / "test.mac").write_text(text)
        subprocess.run([str(args.assembler), "-e32", "-fb", "-otest.bin", "-ltest.lst",
                        "test.mac"], cwd=work, check=True)
        image = (work / "test.bin").read_bytes()
        if image[:BASE] == bytes(BASE):
            image = image[BASE:]
        machine = Encoder(C.CDLL(str(work / "core.so")), image)
        roundtrips, depth = tests(machine)
        print(f"PASS: {machine.cases} SQ cases, {machine.calls} assembled entry calls;")
        print(f"{roundtrips} assembled-USQ + independent-host round trips; maximum code depth {depth}.")
        print(f"SQ code: {machine.symbols['READ_CB'] - machine.symbols['SQ_INIT']} bytes; context: 3524 bytes.")
        print("256-bit path boundary/callbacks/rewind/errors/registers/stack/canaries/immutable code checked.")


if __name__ == "__main__":
    main()
