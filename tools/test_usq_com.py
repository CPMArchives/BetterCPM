#!/usr/bin/env python3
"""Run USQ.COM on the full Z80 core with record-level CP/M BDOS fault injection.

Tests the real command binary, parser, DMA buffers, FCBs, private stack and
codec. The BDOS model deliberately permits destructive MAKE/RENAME, so the
command's own preflight checks must protect existing files. This is not a
replacement for the optional real CP/M smoke test in test_usq_com_cpm.py.
"""
import argparse
import ctypes as C
from pathlib import Path
import random
import re
import shutil
import subprocess
import tempfile

from build_usq import build
from test_usq import SHIM, squeeze, header


def diskkey(drive, name, user=0):
    return drive, user, name.upper()


def padded(data):
    return bytes(data) + b"\x1a" * (-len(data) % 128)


class Command:
    def __init__(self, library, image, listing):
        self.lib, self.image = library, image
        self.mem = (C.c_ubyte * 65536).in_dll(library, "memory")
        self.reg = {}
        for name in ("A", "B", "C", "D", "E", "H", "L", "A_", "B_", "C_",
                     "D_", "E_", "H_", "L_"):
            self.reg[name] = C.c_ubyte.in_dll(library, name)
        for name in ("IX", "IY", "SP", "PC"):
            self.reg[name] = C.c_ushort.in_dll(library, name)
        for name in ("F", "F_"):
            self.reg[name] = C.c_int.in_dll(library, name)
        self.symbols = {}
        for name in ("UC_OLDSP", "UC_STACK", "UC_STACK_TOP", "UC_CONTEXT", "UC_INPUT", "UC_TEMP"):
            match = re.search(rf"^([0-9a-f]{{4}}).*\b{name}:\s", listing, re.M | re.I)
            assert match, name
            self.symbols[name] = int(match[1], 16)
        self.hook = C.CFUNCTYPE(None, C.c_int)(self.callback)
        library.set_hooks.argtypes = [C.c_ushort, C.c_ushort, C.CFUNCTYPE(None, C.c_int)]
        library.test_run.argtypes = [C.c_ushort, C.c_int]
        library.test_run.restype = C.c_int
        library.set_hooks(5, 0xFFFE, self.hook)
        self.cases = 0

    def word(self, address):
        return self.mem[address] | self.mem[address + 1] << 8

    def fcbkey(self, address, offset=0):
        address += offset
        drive = self.mem[address] or self.drive
        name = bytes(x & 127 for x in self.mem[address + 1:address + 9]).decode("ascii").rstrip()
        ext = bytes(x & 127 for x in self.mem[address + 9:address + 12]).decode("ascii").rstrip()
        return drive, self.user, name + ("." + ext if ext else "")

    def callback(self, kind):
        try:
            assert kind == 0 and self.reg["PC"].value == 5
            sp = self.reg["SP"].value
            assert self.symbols["UC_STACK"] <= sp < self.symbols["UC_STACK_TOP"]
            fn = self.reg["C"].value
            de = self.reg["D"].value << 8 | self.reg["E"].value
            value = self.bdos(fn, de)
            self.reg["A"].value = value
            self.reg["F"].value = 0x55  # BDOS flags are unspecified.
            for i, name in enumerate(("B", "C", "D", "E", "H", "L")):
                self.reg[name].value = 0xD1 + i
        except BaseException as error:
            self.exception = error
            self.reg["A"].value = 255

    def fail(self, operation):
        self.attempts[operation] = self.attempts.get(operation, 0) + 1
        nth = self.failures.get(operation)
        return nth is not None and (nth == 0 or self.attempts[operation] == nth)

    def bdos(self, fn, de):
        self.events.append((fn, de))
        if fn == 25:
            return self.drive - 1
        if fn == 26:
            self.dma = de
            return 0
        if fn == 9:
            for i in range(512):
                byte = self.mem[de + i]
                if byte == 36:
                    return 0
                self.console += chr(byte)
            raise AssertionError("unterminated BDOS string")
        key = self.fcbkey(de)
        if fn == 15:
            if key not in self.files or self.fail("open"):
                return 255
            self.opened[de] = [key, 0]
            return 3                     # directory slot is not a boolean
        if fn == 17:
            self.searches[key] = self.searches.get(key, 0) + 1
            if self.late_existing and key == self.late_existing[0] and self.searches[key] == 2:
                self.files[key] = self.late_existing[1]
            if key in self.files:
                self.mem[self.dma:self.dma + 128] = bytes([0xE5]) * 128
                return 2
            return 255
        if fn == 22:
            if self.fail("make"):
                return 255
            # Stock CP/M MAKE preserves EX and the sequential current record.
            # Reserved assembly storage is not implicitly zero-initialized.
            assert self.mem[de + 12] == self.mem[de + 32] == 0
            self.files[key] = b""        # intentionally destructive if unchecked
            self.opened[de] = [key, 0]
            self.created.append(key)
            return 1
        if fn == 20:
            if self.fail("read"):
                return 2
            key, position = self.opened[de]
            data = padded(self.files[key])
            if position >= len(data):
                return 1
            self.mem[self.dma:self.dma + 128] = data[position:position + 128]
            self.opened[de][1] += 128
            return 0
        if fn == 21:
            key, position = self.opened[de]
            if self.fail("write"):
                # Partial media writes are allowed even when BDOS reports failure.
                self.files[key] += bytes(self.mem[self.dma:self.dma + 17])
                return 1
            self.files[key] += bytes(self.mem[self.dma:self.dma + 128])
            self.opened[de][1] += 128
            return 0
        if fn == 16:
            operation = "close_input" if de == self.symbols["UC_INPUT"] else "close_output"
            if self.fail(operation):
                return 255
            self.opened.pop(de, None)
            return 2
        if fn == 19:
            self.deleted.append(key)
            if self.fail("delete") or key not in self.files:
                return 255
            del self.files[key]
            return 0
        if fn == 23:
            if self.fail("rename"):
                return 255
            new = self.fcbkey(de, 16)
            self.files[new] = self.files.pop(key)  # destructive if unchecked
            self.renamed.append((key, new))
            return 3
        raise AssertionError(("unexpected BDOS function", fn))

    def run(self, command, files, drive=1, user=0, failures=None, late_existing=None):
        self.files = dict(files)
        self.original = dict(files)
        self.drive, self.user = drive, user
        self.failures = failures or {}
        self.late_existing = late_existing
        self.attempts, self.opened, self.searches = {}, {}, {}
        self.events, self.created, self.deleted, self.renamed = [], [], [], []
        self.dma, self.console, self.exception = 0x80, "", None
        self.mem[:] = bytes(65536)
        self.mem[0x100:0x100 + len(self.image)] = self.image
        self.mem[5] = 0xC9               # BDOS returns through a real RET
        tail = command.encode("ascii")
        assert len(tail) <= 127
        self.mem[0x80] = len(tail)
        self.mem[0x81:0x81 + len(tail)] = tail
        self.mem[0x81 + len(tail)] = 13
        self.reg["SP"].value = 0xE000
        self.reg["IY"].value = 0xBEEF
        for i, name in enumerate(("A_", "B_", "C_", "D_", "E_", "H_", "L_", "F_")):
            self.reg[name].value = i + 31
        result = self.lib.test_run(0x100, 4000000)
        assert result >= 0, ("CPU error/budget", result, hex(self.reg["PC"].value))
        assert self.exception is None, self.exception
        assert self.reg["SP"].value == 0xE000
        assert self.reg["IY"].value == 0xBEEF
        assert self.dma == 0x80
        for i, name in enumerate(("A_", "B_", "C_", "D_", "E_", "H_", "L_", "F_")):
            assert self.reg[name].value == i + 31
        code_end = self.symbols["UC_OLDSP"]
        assert bytes(self.mem[0x100:code_end]) == self.image[:code_end - 0x100]
        self.cases += 1
        return self.console

    def intact(self):
        for key, data in self.original.items():
            assert self.files.get(key) == data, ("original file changed", key)


def tests(m):
    src = diskkey(1, "TEST.SQ")
    dest = diskkey(1, "RESULT.BIN")
    rng = random.Random(7)
    samples = [b"", b"A", b"\x1a", b"\x90", b"\0" * 127, b"A" * 128,
               b"B" * 129, bytes(range(256)) * 2,
               bytes(rng.randrange(256) for _ in range(1500))]
    for data in samples:
        raw = squeeze(data, name=b"RESULT.BIN")
        assert "complete" in m.run(" TEST.SQ", {src: raw})
        assert m.files[dest] == padded(data)
        assert len(m.created) == len(m.renamed) == 1
        assert not m.deleted and not m.opened
        m.intact()
    raw = squeeze(b"drive selection", name=b"RESULT.BIN")
    # Default destination is logged drive, not input drive. User stays implicit.
    for command, logged, source_drive, target_drive, user in (
        (" B:TEST.SQ", 1, 2, 1, 0),
        (" B:TEST.SQ C:", 1, 2, 3, 0),
        (" TEST.SQ A:", 2, 2, 1, 0),
        (" b:test.sq c:", 1, 2, 3, 7),
        ("\tB:TEST.SQ\tP:\t", 1, 2, 16, 0),
    ):
        source = diskkey(source_drive, "TEST.SQ", user)
        assert "complete" in m.run(command, {source: raw}, drive=logged, user=user)
        assert m.files[diskkey(target_drive, "RESULT.BIN", user)] == padded(b"drive selection")
        m.intact()

    # Strict plain filename validation for both command and embedded name.
    for name in (b"A", b"ABCDEFGH.XYZ", b"ABC.", b"a$b.bin", b"A-B_1.DAT"):
        assert "complete" in m.run(" TEST.SQ", {src: squeeze(b"names", name=name)})
        canonical = name.decode().upper().rstrip(".")
        assert m.files[diskkey(1, canonical)] == padded(b"names")
    for command in ("", " A:", " Q:TEST.SQ", " TEST.SQ Q:", " TEST.SQ B:XX",
                    " TEST.SQ B: EXTRA", " *.SQ", " T?ST.SQ", " .SQ",
                    " TOOLONG99.SQ", " TEST.LONG", " A/B.SQ", " 0/TEST.SQ",
                    " TEST.SQ B", " TEST.SQ :", " A..SQ", " TEST.SQ ;"):
        assert "Usage:" in m.run(command, {src: raw}), command
        assert not m.created and not m.opened
        m.intact()
    for name in (b"", b".BIN", b"TOOLONG99.BIN", b"A.LONG", b"A..B", b"../A",
                 b"B:OUT.BIN", b"0/OUT.BIN", b"A B.BIN", b"*.BIN", b"A?.BIN",
                 b"A\\B", b"\xffNAME.BIN", b"A\x1aBIN"):
        text = m.run(" TEST.SQ", {src: squeeze(b"unsafe", name=name)})
        assert "unsafe embedded filename" in text, (name, text)
        assert not m.created and not m.opened
        m.intact()

    assert "replace input" in m.run(" TEST.SQ", {src: squeeze(b"same", name=b"TEST.SQ")})
    m.intact()
    existing = {src: raw, dest: b"KEEP ORIGINAL"}
    assert "output exists" in m.run(" TEST.SQ", existing)
    assert not m.created
    m.intact()
    # Existing temporaries are never reused/deleted, and destination name
    # itself cannot be selected as the temporary even if it does not exist.
    temp0 = diskkey(1, "USQ00000.$$$")
    temp1 = diskkey(1, "USQ00001.$$$")
    assert "complete" in m.run(" TEST.SQ", {src: raw, temp0: b"KEEP0", temp1: b"KEEP1"})
    assert m.created == [diskkey(1, "USQ00002.$$$")]
    m.intact()
    raw_temp_name = squeeze(b"temp-named destination", name=b"USQ00000.$$$")
    assert "complete" in m.run(" TEST.SQ", {src: raw_temp_name})
    assert m.created == [temp1]
    assert m.files[temp0] == padded(b"temp-named destination")

    # All returned I/O failures must prevent publication and remove only
    # our own temporary. Include partial writes and final-record flush.
    data = bytes(rng.randrange(256) for _ in range(600))
    raw = squeeze(data, name=b"RESULT.BIN")
    cases = [("open", 1, "cannot open"), ("make", 1, "cannot create"),
             ("read", 1, "read failed"), ("read", 4, "read failed"),
             ("write", 1, "write failed"), ("write", 5, "write failed"),
             ("close_output", 1, "close failed"), ("close_input", 1, "close failed"),
             ("rename", 1, "cannot finalize")]
    for operation, nth, message in cases:
        text = m.run(" TEST.SQ", {src: raw, temp0: b"KEEP"}, failures={operation: nth})
        assert message in text and "complete" not in text, (operation, text)
        assert dest not in m.files
        assert not m.opened
        assert set(m.files) == {src, temp0}, (operation, m.files.keys())
        m.intact()
    bad_sum = bytearray(raw)
    bad_sum[2] ^= 1
    assert "checksum mismatch" in m.run(" TEST.SQ", {src: bytes(bad_sum)})
    assert dest not in m.files and not m.opened
    assert set(m.files) == {src}
    m.intact()
    # Failure deleting a temporary is explicitly reported; never erase final.
    text = m.run(" TEST.SQ", {src: bytes(bad_sum)}, failures={"delete": 1})
    assert "cleanup failed" in text and temp0 in m.files and dest not in m.files
    m.intact()
    # Refuse a file appearing at the final existence recheck.
    text = m.run(" TEST.SQ", {src: raw}, late_existing=(dest, b"LATE FILE"))
    assert "output exists" in text and m.files[dest] == b"LATE FILE"
    assert set(m.files) == {src, dest} and not m.renamed
    m.intact()

    for malformed in (b"not squeezed", header([(0, -257)]), b"\x76\xff"):
        text = m.run(" TEST.SQ", {src: malformed})
        assert "invalid or truncated" in text
        assert not m.created and set(m.files) == {src}
        m.intact()
    # Complete records of zero code bits contain A symbols but no encoded
    # EOF. Avoid ordinary CP/M padding, which can itself form valid codes.
    short = header([(-66, -257)], checksum=65, name=b"RESULT.BIN")
    short += bytes(-len(short) % 128)
    text = m.run(" TEST.SQ", {src: short})
    assert "complete" not in text and set(m.files) == {src}
    m.intact()
    assert "cannot open input" in m.run(" MISSING.SQ", {})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembler", type=Path, default=Path.home() / "bin/z80asm")
    parser.add_argument("--z80pack", type=Path, default=Path.home() / "projects/git/z80pack")
    parser.add_argument("--cc", default="cc")
    args = parser.parse_args()
    core = args.z80pack / "z80core"
    with tempfile.TemporaryDirectory(prefix="bettercpm-usq-com-") as temporary:
        work = Path(temporary)
        image = build(args.assembler, work)
        (work / "sim.h").write_text("#define DEF_CPU Z80\n#define EXCLUDE_I8080\n")
        for name in ("simmem.h", "simport.h"):
            shutil.copy2(args.z80pack / "z80sim/srcsim" / name, work / name)
        (work / "shim.c").write_text(SHIM)
        subprocess.run([args.cc, "-shared", "-fPIC", "-O2", f"-I{work}", f"-I{core}",
                        str(work / "shim.c"), str(core / "simglb.c"),
                        *map(str, sorted(core.glob("simz80*.c"))), "-o", str(work / "core.so")], check=True)
        listing = (work / "usq.lst").read_text(errors="replace")
        machine = Command(C.CDLL(str(work / "core.so")), image, listing)
        tests(machine)
        print(f"PASS: {machine.cases} standalone USQ.COM cases on full Z80 core;")
        print("FCBs/DMA/record padding/parser/fault cleanup/existing-file protection checked.")


if __name__ == "__main__":
    main()
