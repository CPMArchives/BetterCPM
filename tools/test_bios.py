#!/usr/bin/env python3
"""Execute and verify the BetterCP/M BIOS scaffold's public entries."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "build/bios/bios.bin"
BASE = 0xF000
COUNT = 17
SENTINEL = 0xFFFF


class Z80:
    """Small runner limited to instructions emitted by this fixture."""

    def __init__(self, image: bytes):
        self.mem = bytearray(65536)
        self.mem[BASE:BASE + len(image)] = image
        self.a = self.b = self.c = self.d = self.e = self.h = self.l = 0
        self.pc, self.sp, self.z = 0, 0xE000, False

    def word(self, address: int) -> int:
        return self.mem[address] | self.mem[address + 1] << 8

    def setword(self, address: int, value: int) -> None:
        self.mem[address] = value & 0xFF
        self.mem[address + 1] = value >> 8

    @property
    def bc(self) -> int:
        return self.b << 8 | self.c

    @bc.setter
    def bc(self, value: int) -> None:
        self.b, self.c = value >> 8, value & 0xFF

    @property
    def de(self) -> int:
        return self.d << 8 | self.e

    @de.setter
    def de(self, value: int) -> None:
        self.d, self.e = value >> 8, value & 0xFF

    @property
    def hl(self) -> int:
        return self.h << 8 | self.l

    @hl.setter
    def hl(self, value: int) -> None:
        self.h, self.l = value >> 8, value & 0xFF

    def push(self, value: int) -> None:
        self.sp = (self.sp - 2) & 0xFFFF
        self.setword(self.sp, value)

    def pop(self) -> int:
        value = self.word(self.sp)
        self.sp = (self.sp + 2) & 0xFFFF
        return value

    def run(self, address: int, limit: int = 200) -> None:
        self.pc = address
        self.push(SENTINEL)
        for _ in range(limit):
            if self.pc == SENTINEL:
                return
            op = self.mem[self.pc]
            self.pc += 1
            if op == 0xC3:              # JP nn
                self.pc = self.word(self.pc)
            elif op == 0xCD:            # CALL nn
                target = self.word(self.pc)
                self.pc += 2
                self.push(self.pc)
                self.pc = target
            elif op == 0xC9:            # RET
                self.pc = self.pop()
            elif op == 0xC8:            # RET Z
                if self.z:
                    self.pc = self.pop()
            elif op == 0x18:            # JR e
                displacement = self.mem[self.pc]
                self.pc += 1
                if displacement & 0x80:
                    displacement -= 0x100
                self.pc = (self.pc + displacement) & 0xFFFF
            elif op == 0x20:            # JR NZ,e
                displacement = self.mem[self.pc]
                self.pc += 1
                if not self.z:
                    if displacement & 0x80:
                        displacement -= 0x100
                    self.pc = (self.pc + displacement) & 0xFFFF
            elif op == 0xAF:            # XOR A
                self.a, self.z = 0, True
            elif op == 0xB7:            # OR A
                self.z = self.a == 0
            elif op == 0xB3:            # OR E
                self.a |= self.e
                self.z = self.a == 0
            elif op == 0xE6:            # AND n
                self.a &= self.mem[self.pc]
                self.pc += 1
                self.z = self.a == 0
            elif op == 0x3E:            # LD A,n
                self.a = self.mem[self.pc]
                self.pc += 1
            elif op == 0x79:            # LD A,C
                self.a = self.c
            elif op == 0x7A:            # LD A,D
                self.a = self.d
            elif op == 0x32:            # LD (nn),A
                target = self.word(self.pc)
                self.pc += 2
                self.mem[target] = self.a
            elif op == 0x01:            # LD BC,nn
                self.bc = self.word(self.pc)
                self.pc += 2
            elif op == 0x21:            # LD HL,nn
                self.hl = self.word(self.pc)
                self.pc += 2
            elif op == 0x26:            # LD H,n
                self.h = self.mem[self.pc]
                self.pc += 1
            elif op == 0x60:            # LD H,B
                self.h = self.b
            elif op == 0x69:            # LD L,C
                self.l = self.c
            elif op == 0x6E:            # LD L,(HL)
                self.l = self.mem[self.hl]
            elif op == 0xEB:            # EX DE,HL
                value = self.de
                self.de = self.hl
                self.hl = value
            elif op == 0x09:            # ADD HL,BC
                self.hl = (self.hl + self.bc) & 0xFFFF
            elif op == 0xED and self.mem[self.pc] == 0x43:  # LD (nn),BC
                self.pc += 1
                target = self.word(self.pc)
                self.pc += 2
                self.setword(target, self.bc)
            else:
                raise AssertionError(f"unsupported opcode {op:02X} at {self.pc - 1:04X}")
        raise AssertionError(f"execution limit reached from {address:04X}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    data = IMAGE.read_bytes()
    cpu = Z80(data)

    def entry(index: int) -> int:
        offset = BASE + index * 3
        require(cpu.mem[offset] == 0xC3, f"entry {index} is not JP")
        target = cpu.word(offset + 1)
        require(BASE <= target < BASE + len(data), f"entry {index} target outside image")
        return offset

    entries = [entry(index) for index in range(COUNT)]

    for index in (0, 1):
        target = cpu.word(entries[index] + 1)
        require(cpu.mem[target] == 0x18 and cpu.mem[target + 1] == 0xFE,
                f"entry {index} is not the explicit stop loop")

    const_impl = cpu.word(entries[2] + 1)
    platform_const = cpu.word(const_impl + 1)
    cpu.mem[platform_const:platform_const + 2] = bytes((0xAF, 0xC9))
    cpu.run(entries[2])
    require(cpu.a == 0, "CONST empty result is not 00h")
    cpu.mem[platform_const:platform_const + 3] = bytes((0x3E, 0x01, 0xC9))
    cpu.run(entries[2])
    require(cpu.a == 0xFF, "CONST ready result is not FFh")

    conin_impl = cpu.word(entries[3] + 1)
    platform_conin = cpu.word(conin_impl + 1)
    cpu.mem[platform_conin:platform_conin + 3] = bytes((0x3E, 0xC1, 0xC9))
    cpu.run(entries[3])
    require(cpu.a == 0x41, "CONIN did not clear parity")

    conout_impl = cpu.word(entries[4] + 1)
    platform_conout = cpu.word(conout_impl + 1)
    cpu.mem[platform_conout:platform_conout + 5] = bytes((0x79, 0x32, 0x00, 0x70, 0xC9))
    cpu.c = 0x09
    cpu.run(entries[4])
    require(cpu.mem[0x7000] == 0x09, "CONOUT did not transport C unchanged")

    cpu.run(entries[7])
    require(cpu.a == 0x1A, "unassigned READER did not return Ctrl-Z")

    settrk_impl = cpu.word(entries[10] + 1)
    track_state = cpu.word(settrk_impl + 2)
    cpu.bc = 0x1234
    cpu.run(entries[10])
    require(cpu.word(track_state) == 0x1234, "SETTRK state did not persist")
    cpu.run(entries[8])
    require(cpu.word(track_state) == 0, "HOME did not select track zero")

    for index, value, name in ((11, 0x0056, "SETSEC"), (12, 0x3456, "SETDMA")):
        implementation = cpu.word(entries[index] + 1)
        state = cpu.word(implementation + 2)
        cpu.bc = value
        cpu.run(entries[index])
        require(cpu.word(state) == value, f"{name} state did not persist")

    cpu.c = 0
    cpu.run(entries[9])
    require(cpu.hl != 0, "SELDSK did not expose drive A DPH")
    dph = cpu.hl
    dpb = cpu.word(dph + 10)
    require(cpu.word(dpb) == 80, "drive A SPT is not 80")
    require(bytes(cpu.mem[dpb + 2:dpb + 5]) == bytes((4, 15, 0)),
            "drive A BSH/BLM/EXM mismatch")
    require(cpu.word(dpb + 5) == 394 and cpu.word(dpb + 7) == 127,
            "drive A DSM/DRM mismatch")
    require(bytes(cpu.mem[dpb + 9:dpb + 11]) == bytes((0xC0, 0)),
            "drive A allocation mask mismatch")
    require(cpu.word(dpb + 11) == 32 and cpu.word(dpb + 13) == 2,
            "drive A CKS/OFF mismatch")
    cpu.c = 5
    cpu.run(entries[9])
    require(cpu.hl == 0, "SELDSK exposed an unavailable drive")
    for index, name in ((13, "READ"), (14, "WRITE")):
        cpu.a = 0
        cpu.run(entries[index])
        require(cpu.a != 0, f"{name} falsely reported success")
    cpu.run(entries[15])
    require(cpu.a == 0, "unassigned LISTST did not report not-ready")

    cpu.bc, cpu.de = 7, 0
    cpu.run(entries[16])
    require(cpu.hl == 7, "null-XLT SECTRAN was not identity")
    cpu.mem[0x7100:0x7104] = bytes((1, 5, 9, 13))
    cpu.bc, cpu.de = 2, 0x7100
    cpu.run(entries[16])
    require(cpu.hl == 9, "table SECTRAN returned the wrong identifier")

    print(f"executed {COUNT} BIOS-vector contracts from {BASE:04X}h binary")
    print("character transport, disk state, failure paths, and SECTRAN passed")


if __name__ == "__main__":
    main()
