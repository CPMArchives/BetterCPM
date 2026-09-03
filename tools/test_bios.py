#!/usr/bin/env python3
"""Execute and verify the BetterCP/M BIOS scaffold's public entries."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "build/bios/bios.bin"
BASE = 0xEF00
COUNT = 17
SENTINEL = 0xFFFF


class Z80:
    """Small runner limited to instructions emitted by this fixture."""

    def __init__(self, image: bytes):
        self.mem = bytearray(65536)
        self.mem[BASE:BASE + len(image)] = image
        self.a = self.b = self.c = self.d = self.e = self.h = self.l = 0
        self.pc, self.sp, self.z, self.carry = 0, 0xE000, False, False

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
            elif op in (0xC2, 0xCA, 0xD2, 0xDA):  # JP NZ/Z/NC/C,nn
                target = self.word(self.pc)
                self.pc += 2
                take = ((op == 0xC2 and not self.z) or
                        (op == 0xCA and self.z) or
                        (op == 0xD2 and not self.carry) or
                        (op == 0xDA and self.carry))
                if take:
                    self.pc = target
            elif op == 0xCD:            # CALL nn
                target = self.word(self.pc)
                self.pc += 2
                self.push(self.pc)
                self.pc = target
            elif op == 0xC9:            # RET
                self.pc = self.pop()
            elif op == 0xF5:            # PUSH AF
                flags = (0x40 if self.z else 0) | (1 if self.carry else 0)
                self.push(self.a << 8 | flags)
            elif op == 0xF1:            # POP AF
                value = self.pop()
                self.a = value >> 8
                self.z, self.carry = bool(value & 0x40), bool(value & 1)
            elif op == 0xC5:            # PUSH BC
                self.push(self.bc)
            elif op == 0xC1:            # POP BC
                self.bc = self.pop()
            elif op == 0xE5:            # PUSH HL
                self.push(self.hl)
            elif op == 0xE1:            # POP HL
                self.hl = self.pop()
            elif op == 0xD5:            # PUSH DE
                self.push(self.de)
            elif op == 0xD1:            # POP DE
                self.de = self.pop()
            elif op == 0xC8:            # RET Z
                if self.z:
                    self.pc = self.pop()
            elif op == 0xD8:            # RET C
                if self.carry:
                    self.pc = self.pop()
            elif op == 0xD0:            # RET NC
                if not self.carry:
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
            elif op in (0x28, 0x30, 0x38):  # JR Z/NC/C,e
                displacement = self.mem[self.pc]
                self.pc += 1
                take = ((op == 0x28 and self.z) or
                        (op == 0x30 and not self.carry) or
                        (op == 0x38 and self.carry))
                if take:
                    if displacement & 0x80:
                        displacement -= 0x100
                    self.pc = (self.pc + displacement) & 0xFFFF
            elif op == 0xAF:            # XOR A
                self.a, self.z = 0, True
                self.carry = False
            elif op == 0x37:            # SCF
                self.carry = True
            elif op == 0x3F:            # CCF
                self.carry = not self.carry
            elif op == 0xB7:            # OR A
                self.z = self.a == 0
                self.carry = False
            elif op == 0xF6:            # OR n
                self.a |= self.mem[self.pc]
                self.pc += 1
                self.z = self.a == 0
                self.carry = False
            elif op == 0xB3:            # OR E
                self.a |= self.e
                self.z = self.a == 0
                self.carry = False
            elif op == 0xB5:            # OR L
                self.a |= self.l
                self.z = self.a == 0
                self.carry = False
            elif op == 0xE6:            # AND n
                self.a &= self.mem[self.pc]
                self.pc += 1
                self.z = self.a == 0
                self.carry = False
            elif op == 0xA1:            # AND C
                self.a &= self.c
                self.z = self.a == 0
                self.carry = False
            elif op == 0xA6:            # AND (HL)
                self.a &= self.mem[self.hl]
                self.z = self.a == 0
                self.carry = False
            elif op == 0x2F:            # CPL
                self.a ^= 0xFF
            elif op == 0x3E:            # LD A,n
                self.a = self.mem[self.pc]
                self.pc += 1
            elif op == 0xFE:            # CP n
                value = self.mem[self.pc]
                self.pc += 1
                self.z, self.carry = self.a == value, self.a < value
            elif op == 0xD6:            # SUB n
                value = self.mem[self.pc]
                self.pc += 1
                self.carry = self.a < value
                self.a = (self.a - value) & 0xFF
                self.z = self.a == 0
            elif op == 0x91:            # SUB C
                self.carry = self.a < self.c
                self.a = (self.a - self.c) & 0xFF
                self.z = self.a == 0
            elif op == 0x93:            # SUB E
                self.carry = self.a < self.e
                self.a = (self.a - self.e) & 0xFF
                self.z = self.a == 0
            elif op == 0x3D:            # DEC A
                self.a = (self.a - 1) & 0xFF
                self.z = self.a == 0
            elif op == 0x3C:            # INC A
                self.a = (self.a + 1) & 0xFF
                self.z = self.a == 0
            elif op == 0x87:            # ADD A,A
                value = self.a * 2
                self.a = value & 0xFF
                self.z, self.carry = self.a == 0, value > 0xFF
            elif op == 0x04:            # INC B
                self.b = (self.b + 1) & 0xFF
                self.z = self.b == 0
            elif op == 0x05:            # DEC B
                self.b = (self.b - 1) & 0xFF
                self.z = self.b == 0
            elif op == 0x03:            # INC BC
                self.bc = (self.bc + 1) & 0xFFFF
            elif op == 0x13:            # INC DE
                self.de = (self.de + 1) & 0xFFFF
            elif op == 0x1B:            # DEC DE
                self.de = (self.de - 1) & 0xFFFF
            elif op == 0x1C:            # INC E
                self.e = (self.e + 1) & 0xFF
                self.z = self.e == 0
            elif op == 0x1D:            # DEC E
                self.e = (self.e - 1) & 0xFF
                self.z = self.e == 0
            elif op == 0x23:            # INC HL
                self.hl = (self.hl + 1) & 0xFFFF
            elif op == 0x34:            # INC (HL)
                self.mem[self.hl] = (self.mem[self.hl] + 1) & 0xFF
            elif op == 0x35:            # DEC (HL)
                self.mem[self.hl] = (self.mem[self.hl] - 1) & 0xFF
                self.z = self.mem[self.hl] == 0
                self.z = self.mem[self.hl] == 0
            elif op == 0x06:            # LD B,n
                self.b = self.mem[self.pc]
                self.pc += 1
            elif op == 0x0E:            # LD C,n
                self.c = self.mem[self.pc]
                self.pc += 1
            elif op == 0x1E:            # LD E,n
                self.e = self.mem[self.pc]
                self.pc += 1
            elif op == 0x16:            # LD D,n
                self.d = self.mem[self.pc]
                self.pc += 1
            elif op == 0x2E:            # LD L,n
                self.l = self.mem[self.pc]
                self.pc += 1
            elif op == 0x31:            # LD SP,nn
                self.sp = self.word(self.pc)
                self.pc += 2
            elif op == 0x79:            # LD A,C
                self.a = self.c
            elif op == 0x78:            # LD A,B
                self.a = self.b
            elif op == 0x47:            # LD B,A
                self.b = self.a
            elif op == 0x45:            # LD B,L
                self.b = self.l
            elif op == 0x44:            # LD B,H
                self.b = self.h
            elif op == 0x4F:            # LD C,A
                self.c = self.a
            elif op == 0x4D:            # LD C,L
                self.c = self.l
            elif op == 0x4B:            # LD C,E
                self.c = self.e
            elif op == 0x7A:            # LD A,D
                self.a = self.d
            elif op == 0x7B:            # LD A,E
                self.a = self.e
            elif op == 0x7C:            # LD A,H
                self.a = self.h
            elif op == 0x7D:            # LD A,L
                self.a = self.l
            elif op == 0x7E:            # LD A,(HL)
                self.a = self.mem[self.hl]
            elif op == 0x5F:            # LD E,A
                self.e = self.a
            elif op == 0x59:            # LD E,C
                self.e = self.c
            elif op == 0x57:            # LD D,A
                self.d = self.a
            elif op == 0x32:            # LD (nn),A
                target = self.word(self.pc)
                self.pc += 2
                self.mem[target] = self.a
            elif op == 0x3A:            # LD A,(nn)
                target = self.word(self.pc)
                self.pc += 2
                self.a = self.mem[target]
            elif op == 0x1A:            # LD A,(DE)
                self.a = self.mem[self.de]
            elif op == 0x01:            # LD BC,nn
                self.bc = self.word(self.pc)
                self.pc += 2
            elif op == 0x21:            # LD HL,nn
                self.hl = self.word(self.pc)
                self.pc += 2
            elif op == 0x2A:            # LD HL,(nn)
                target = self.word(self.pc)
                self.pc += 2
                self.hl = self.word(target)
            elif op == 0x22:            # LD (nn),HL
                target = self.word(self.pc)
                self.pc += 2
                self.setword(target, self.hl)
            elif op == 0x11:            # LD DE,nn
                self.de = self.word(self.pc)
                self.pc += 2
            elif op == 0x26:            # LD H,n
                self.h = self.mem[self.pc]
                self.pc += 1
            elif op == 0x60:            # LD H,B
                self.h = self.b
            elif op == 0x62:            # LD H,D
                self.h = self.d
            elif op == 0x67:            # LD H,A
                self.h = self.a
            elif op == 0x69:            # LD L,C
                self.l = self.c
            elif op == 0x6F:            # LD L,A
                self.l = self.a
            elif op == 0x6B:            # LD L,E
                self.l = self.e
            elif op == 0x6E:            # LD L,(HL)
                self.l = self.mem[self.hl]
            elif op == 0x4E:            # LD C,(HL)
                self.c = self.mem[self.hl]
            elif op == 0x46:            # LD B,(HL)
                self.b = self.mem[self.hl]
            elif op == 0x5E:            # LD E,(HL)
                self.e = self.mem[self.hl]
            elif op == 0x56:            # LD D,(HL)
                self.d = self.mem[self.hl]
            elif op == 0x77:            # LD (HL),A
                self.mem[self.hl] = self.a
            elif op == 0x36:            # LD (HL),n
                self.mem[self.hl] = self.mem[self.pc]
                self.pc += 1
            elif op == 0x34:            # INC (HL)
                self.mem[self.hl] = (self.mem[self.hl] + 1) & 0xFF
            elif op == 0xB9:            # CP C
                self.z, self.carry = self.a == self.c, self.a < self.c
            elif op == 0xBB:            # CP E
                self.z, self.carry = self.a == self.e, self.a < self.e
            elif op == 0xBC:            # CP H
                self.z, self.carry = self.a == self.h, self.a < self.h
            elif op == 0xBD:            # CP L
                self.z, self.carry = self.a == self.l, self.a < self.l
            elif op == 0xBE:            # CP (HL)
                value = self.mem[self.hl]
                self.z, self.carry = self.a == value, self.a < value
            elif op == 0xB6:            # OR (HL)
                self.a |= self.mem[self.hl]
                self.z = self.a == 0
                self.carry = False
            elif op == 0xEB:            # EX DE,HL
                value = self.de
                self.de = self.hl
                self.hl = value
            elif op == 0xE3:            # EX (SP),HL
                value = self.word(self.sp)
                self.setword(self.sp, self.hl)
                self.hl = value
            elif op == 0x09:            # ADD HL,BC
                self.hl = (self.hl + self.bc) & 0xFFFF
            elif op == 0x19:            # ADD HL,DE
                self.hl = (self.hl + self.de) & 0xFFFF
            elif op == 0x29:            # ADD HL,HL
                self.hl = (self.hl * 2) & 0xFFFF
            elif op == 0x0F:            # RRCA
                low = self.a & 1
                self.a = (self.a >> 1) | (low << 7)
                self.carry = bool(low)
            elif op == 0x96:            # SUB (HL)
                value = self.mem[self.hl]
                self.carry = self.a < value
                self.a = (self.a - value) & 0xFF
                self.z = self.a == 0
            elif op == 0xCB and self.mem[self.pc] == 0x3F:  # SRL A
                self.pc += 1
                self.carry = bool(self.a & 1)
                self.a >>= 1
                self.z = self.a == 0
            elif op == 0xCB and self.mem[self.pc] == 0x3C:  # SRL H
                self.pc += 1
                self.carry = bool(self.h & 1)
                self.h >>= 1
                self.z = self.h == 0
            elif op == 0xCB and self.mem[self.pc] == 0x3A:  # SRL D
                self.pc += 1
                self.carry = bool(self.d & 1)
                self.d >>= 1
                self.z = self.d == 0
            elif op == 0xCB and self.mem[self.pc] == 0x39:  # SRL C
                self.pc += 1
                self.carry = bool(self.c & 1)
                self.c >>= 1
                self.z = self.c == 0
            elif op == 0xCB and self.mem[self.pc] == 0x1D:  # RR L
                self.pc += 1
                old_carry = self.carry
                self.carry = bool(self.l & 1)
                self.l = (self.l >> 1) | (0x80 if old_carry else 0)
                self.z = self.l == 0
            elif op == 0xCB and self.mem[self.pc] == 0x25:  # SLA L
                self.pc += 1
                self.carry = bool(self.l & 0x80)
                self.l = (self.l << 1) & 0xFF
                self.z = self.l == 0
            elif op == 0xCB and self.mem[self.pc] == 0x23:  # SLA E
                self.pc += 1
                self.carry = bool(self.e & 0x80)
                self.e = (self.e << 1) & 0xFF
                self.z = self.e == 0
            elif op == 0xED and self.mem[self.pc] == 0x43:  # LD (nn),BC
                self.pc += 1
                target = self.word(self.pc)
                self.pc += 2
                self.setword(target, self.bc)
            elif op == 0xED and self.mem[self.pc] == 0x5B:  # LD DE,(nn)
                self.pc += 1
                target = self.word(self.pc)
                self.pc += 2
                self.de = self.word(target)
            elif op == 0xED and self.mem[self.pc] == 0x53:  # LD (nn),DE
                self.pc += 1
                target = self.word(self.pc)
                self.pc += 2
                self.setword(target, self.de)
            elif op == 0xED and self.mem[self.pc] == 0x73:  # LD (nn),SP
                self.pc += 1
                target = self.word(self.pc)
                self.pc += 2
                self.setword(target, self.sp)
            elif op == 0xED and self.mem[self.pc] == 0x7B:  # LD SP,(nn)
                self.pc += 1
                target = self.word(self.pc)
                self.pc += 2
                self.sp = self.word(target)
            elif op == 0xED and self.mem[self.pc] == 0x52:  # SBC HL,DE
                self.pc += 1
                value = self.hl - self.de - (1 if self.carry else 0)
                self.carry = value < 0
                self.hl = value & 0xFFFF
                self.z = self.hl == 0
            elif op == 0xED and self.mem[self.pc] == 0x4B:  # LD BC,(nn)
                self.pc += 1
                target = self.word(self.pc)
                self.pc += 2
                self.bc = self.word(target)
            elif op == 0xED and self.mem[self.pc] == 0xB0:  # LDIR
                self.pc += 1
                count = self.bc
                for _ in range(count):
                    self.mem[self.de] = self.mem[self.hl]
                    self.hl = (self.hl + 1) & 0xFFFF
                    self.de = (self.de + 1) & 0xFFFF
                self.bc = 0
            elif op == 0xC0:            # RET NZ
                if not self.z:
                    self.pc = self.pop()
            elif op == 0x10:            # DJNZ e
                displacement = self.mem[self.pc]
                self.pc += 1
                self.b = (self.b - 1) & 0xFF
                if self.b:
                    if displacement & 0x80:
                        displacement -= 0x100
                    self.pc = (self.pc + displacement) & 0xFFFF
            elif op == 0xA0:            # AND B
                self.a &= self.b
                self.z, self.carry = self.a == 0, False
            elif op == 0xB0:            # OR B
                self.a |= self.b
                self.z, self.carry = self.a == 0, False
            elif op in (0x80, 0x81, 0x82):  # ADD A,B / C / D
                value = {0x80: self.b, 0x81: self.c, 0x82: self.d}[op]
                total = self.a + value
                self.a = total & 0xFF
                self.z, self.carry = self.a == 0, total > 0xFF
            elif op == 0xC6:            # ADD A,n
                total = self.a + self.mem[self.pc]
                self.pc += 1
                self.a = total & 0xFF
                self.z, self.carry = self.a == 0, total > 0xFF
            elif op == 0xCE:            # ADC A,n
                total = self.a + self.mem[self.pc] + (1 if self.carry else 0)
                self.pc += 1
                self.a = total & 0xFF
                self.z, self.carry = self.a == 0, total > 0xFF
            elif op == 0xB1:            # OR C
                self.a |= self.c
                self.z, self.carry = self.a == 0, False
            elif op in (0xB8, 0xBA, 0xBB):  # CP B / CP D / CP E
                value = {0xB8: self.b, 0xBA: self.d, 0xBB: self.e}[op]
                self.z, self.carry = self.a == value, self.a < value
            elif op == 0x54:            # LD D,H
                self.d = self.h
            elif op == 0x5D:            # LD E,L
                self.e = self.l
            elif op == 0x2B:            # DEC HL
                self.hl = (self.hl - 1) & 0xFFFF
            elif op == 0xE9:            # JP (HL)
                self.pc = self.hl
            elif op == 0x14:            # INC D
                self.d = (self.d + 1) & 0xFF
                self.z = self.d == 0
            elif op == 0x0D:            # DEC C
                self.c = (self.c - 1) & 0xFF
                self.z = self.c == 0
            elif op in (0x71, 0x72, 0x73):  # LD (HL),C / D / E
                self.mem[self.hl] = {0x71: self.c, 0x72: self.d,
                                     0x73: self.e}[op]
            elif op == 0x12:            # LD (DE),A
                self.mem[self.de] = self.a
            else:
                raise AssertionError(f"unsupported opcode {op:02X} at {self.pc - 1:04X}")
        raise AssertionError(f"execution limit reached from {address:04X}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def install_drive_tables(cpu: Z80, dph_base: int = 0xC9A8,
                         dpb_address: int = 0xC9E8,
                         workspaces=None) -> None:
    """Install the gateway-owned four-drive DPH/DPB contract in test memory."""
    # Patch 2026-09-03: the original fixture repeated the bring-up CB00h
    # boundary. Keep this table explicit until the generated system-layout
    # include lands, but mirror the packed descriptor unit exactly.
    if workspaces is None:
        workspaces = ((0xC9F8, 0xCA18), (0xCA4A, 0xCA6A),
                      (0xCA9C, 0xCABC), (0xCAEE, 0xCB0E))
    for drive, (csv, alv) in enumerate(workspaces):
        dph = dph_base + drive * 16
        for offset, value in ((8, 0xEC80), (10, dpb_address),
                              (12, csv), (14, alv)):
            cpu.mem[dph + offset:dph + offset + 2] = value.to_bytes(2, "little")
    cpu.mem[dpb_address:dpb_address + 15] = bytes(
        (80, 0, 4, 15, 0, 0x8A, 1, 127, 0, 0xC0, 0, 32, 0, 2, 0)
    )


def main() -> None:
    data = IMAGE.read_bytes()
    cpu = Z80(data)
    install_drive_tables(cpu)

    def entry(index: int) -> int:
        offset = BASE + index * 3
        require(cpu.mem[offset] == 0xC3, f"entry {index} is not JP")
        target = cpu.word(offset + 1)
        require(BASE <= target < BASE + len(data), f"entry {index} target outside image")
        return offset

    entries = [entry(index) for index in range(COUNT)]

    boot_target = cpu.word(entries[0] + 1)
    require(cpu.mem[boot_target] == 0xCD and
            cpu.mem[boot_target + 3] == 0xC3 and
            cpu.word(boot_target + 4) == 0xE900,
            "BOOT does not initialize the platform then reconstruct commands")
    warm_target = cpu.word(entries[1] + 1)
    require(cpu.mem[warm_target] == 0xC3 and
            cpu.word(warm_target + 1) == 0xE900,
            "WBOOT does not enter command-image restoration")
    private_read = BASE + 17 * 3
    private_cursor = private_read + 3
    require(cpu.mem[private_read] == 0xC3 and
            BASE <= cpu.word(private_read + 1) < BASE + len(data),
            "private physical-read vector is not a bounded JP")
    require(cpu.mem[private_cursor] == 0xC3 and
            BASE <= cpu.word(private_cursor + 1) < BASE + len(data),
            "private cursor-character vector is not a bounded JP")
    read_impl = cpu.word(private_read + 1)
    require(cpu.mem[read_impl] == 0x3E and cpu.mem[read_impl + 1] == 1,
            "private physical-read implementation does not select system drive A")

    const_impl = cpu.word(entries[2] + 1)
    platform_const = cpu.word(const_impl + 1)
    cpu.mem[platform_const:platform_const + 2] = bytes((0xAF, 0xC9))
    cpu.run(entries[2])
    require(cpu.a == 0, "CONST empty result is not 00h")
    cpu.mem[platform_const:platform_const + 3] = bytes((0x3E, 0x01, 0xC9))
    cpu.run(entries[2])
    require(cpu.a == 0xFF, "CONST ready result is not FFh")

    # Exercise the production matrix scanner before replacing CONIN below.
    scan_at = platform_const - BASE + 1
    scan = int.from_bytes(data[scan_at:scan_at + 2], "little")
    cpu.mem[platform_const:platform_const + 3] = data[
        platform_const - BASE:platform_const - BASE + 3]
    cpu.mem[0xF420], cpu.mem[0xF480] = 0x04, 0x01  # Shift-colon
    cpu.run(scan)
    require(cpu.a == ord("*"), "matrix scanner missed Shift-colon asterisk")
    cpu.mem[0xF420] = 0x20                         # Shift-minus
    cpu.run(scan)
    require(cpu.a == ord("="), "matrix scanner missed Shift-minus equals")
    cpu.mem[0xF420] = 0x80                         # Shift-slash
    cpu.run(scan)
    require(cpu.a == ord("?"), "matrix scanner missed Shift-slash question mark")
    cpu.mem[0xF420] = cpu.mem[0xF480] = 0
    cpu.mem[0xF402], cpu.mem[0xF480] = 0x01, 0x04  # Control-H
    cpu.run(scan)
    require(cpu.a == 8, "matrix scanner did not translate Control-H")
    cpu.mem[0xF402], cpu.mem[0xF440], cpu.mem[0xF480] = 0, 0x20, 0
    cpu.run(scan)
    require(cpu.a == 28, "physical Left was not distinct from Control-H")
    cpu.mem[0xF480] = 0x01                        # Shift-Left
    cpu.run(scan)
    require(cpu.a == 127, "Shift-Left did not produce DEL")
    cpu.mem[0xF440] = cpu.mem[0xF480] = 0

    conin_impl = cpu.word(entries[3] + 1)
    platform_conin = cpu.word(conin_impl + 1)
    cpu.mem[platform_conin:platform_conin + 3] = bytes((0x3E, 0xC1, 0xC9))
    cpu.run(entries[3])
    require(cpu.a == 0x41, "CONIN did not clear parity")

    conout_impl = cpu.word(entries[4] + 1)
    platform_conout = cpu.word(conout_impl + 1)

    scroll_cpu = Z80(data)
    scroll_cpu.mem[0xF800:0xFF80] = bytes((0x20,)) * 1920
    scroll_cpu.mem[0xFF80] = 0xA5
    for character in range(ord("A"), ord("Z")):
        for value in (character, 13, 10):
            scroll_cpu.c = value
            scroll_cpu.run(entries[4])
    require([scroll_cpu.mem[0xF800 + row * 80] for row in range(23)] ==
            list(range(ord("C"), ord("Z"))),
            "CONOUT did not scroll 80x24 rows in order")
    require(scroll_cpu.mem[0xFF30:0xFF80] == bytes((0x20,)) * 80,
            "CONOUT did not clear the new bottom row")
    require(scroll_cpu.mem[0xFF80] == 0xA5,
            "CONOUT wrote beyond Model 4 video RAM")

    wrap_cpu = Z80(data)
    wrap_cpu.mem[0xF800:0xFF80] = bytes((0x20,)) * 1920
    wrap_cpu.mem[0xFF80] = 0x5A
    for _ in range(1920):
        wrap_cpu.c = ord("Q")
        wrap_cpu.run(entries[4])
    require(wrap_cpu.mem[0xF800:0xFF30] == bytes((ord("Q"),)) * 1840 and
            wrap_cpu.mem[0xFF30:0xFF80] == bytes((0x20,)) * 80,
            "CONOUT did not scroll at the automatic-wrap boundary")
    require(wrap_cpu.mem[0xFF80] == 0x5A,
            "automatic wrap wrote beyond Model 4 video RAM")

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
    dphs = [dph]
    work = {(cpu.word(dph + 12), cpu.word(dph + 14))}
    for drive, name in ((1, "B"), (2, "C"), (3, "D")):
        cpu.c = drive
        cpu.run(entries[9])
        require(cpu.hl != 0 and cpu.hl not in dphs,
                f"SELDSK did not expose a distinct drive {name} DPH")
        require(cpu.word(cpu.hl + 10) == dpb,
                f"drive {name} did not share the selected 790K geometry")
        pair = (cpu.word(cpu.hl + 12), cpu.word(cpu.hl + 14))
        require(pair not in work,
                f"drive {name} reused another drive's check/allocation workspace")
        dphs.append(cpu.hl)
        work.add(pair)
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

    # Execute every drive-A logical read with an instrumented physical layer.
    cpu.c = 0
    cpu.run(entries[9])
    cpu.bc = 2
    cpu.run(entries[10])
    cpu.bc = 0x7200
    cpu.run(entries[12])
    read_impl = cpu.word(entries[13] + 1)
    read_calls = [address for address in range(read_impl, read_impl + 48)
                  if cpu.mem[address] == 0xCD]
    require(len(read_calls) >= 2, "READ physical-call site was not found")
    call_at = read_calls[1]
    platform_read = cpu.word(call_at + 1)
    read_success = bytes((
        0x32, 0x00, 0x73,       # LD (7300h),A: cylinder
        0x78, 0x32, 0x01, 0x73, # LD A,B / LD (7301h),A: side
        0x79, 0x32, 0x02, 0x73, # LD A,C / LD (7302h),A: sector
        0xAF, 0xC9,              # XOR A / RET
    ))
    cpu.mem[platform_read:platform_read + len(read_success)] = read_success
    order = (1, 3, 5, 7, 9, 2, 4, 6, 8, 10)
    for logical in range(80):
        for quarter in range(4):
            cpu.mem[0xED00 + quarter * 128:0xED80 + quarter * 128] = bytes((quarter,)) * 128
        cpu.bc = logical
        cpu.run(entries[11])
        cpu.a = 0xFF
        cpu.run(entries[13])
        physical = logical // 4
        require(cpu.a == 0, f"READ {logical} did not succeed")
        require(cpu.mem[0x7300] == 2, f"READ {logical} changed cylinder")
        require(cpu.mem[0x7301] == physical // 10,
                f"READ {logical} selected wrong side")
        require(cpu.mem[0x7302] == order[physical % 10],
                f"READ {logical} selected wrong sector ID")
        require(cpu.mem[0x7200:0x7280] == bytes((logical & 3,)) * 128,
                f"READ {logical} copied wrong 128-byte quarter")

    write_impl = cpu.word(entries[14] + 1)
    write_jumps = [address for address in range(write_impl, write_impl + 90)
                   if cpu.mem[address] == 0xC3]
    require(write_jumps, "WRITE physical-jump site was not found")
    platform_write = cpu.word(write_jumps[-1] + 1)
    write_success = bytes((
        0x32, 0x10, 0x73,
        0x78, 0x32, 0x11, 0x73,
        0x79, 0x32, 0x12, 0x73,
        0xAF, 0xC9,
    ))
    cpu.mem[platform_write:platform_write + len(write_success)] = write_success
    for logical in range(80):
        for quarter in range(4):
            cpu.mem[0xED00 + quarter * 128:0xED80 + quarter * 128] = bytes((quarter,)) * 128
        replacement = (0x80 | logical) & 0xFF
        cpu.mem[0x7200:0x7280] = bytes((replacement,)) * 128
        cpu.bc = logical
        cpu.run(entries[11])
        cpu.c = logical % 3       # exercise CP/M write types 0, 1, and 2
        cpu.run(entries[14])
        physical = logical // 4
        require(cpu.a == 0, f"WRITE {logical} did not succeed")
        require(cpu.mem[0x7310] == 2 and cpu.mem[0x7311] == physical // 10,
                f"WRITE {logical} selected wrong cylinder/side")
        require(cpu.mem[0x7312] == order[physical % 10],
                f"WRITE {logical} selected wrong sector ID")
        for quarter in range(4):
            expected = replacement if quarter == (logical & 3) else quarter
            require(cpu.mem[0xED00 + quarter * 128:0xED80 + quarter * 128] ==
                    bytes((expected,)) * 128,
                    f"WRITE {logical} corrupted quarter {quarter}")

    # 2026-09-01 patch: preserve the caller-visible failure contract while the
    # physical layer evolves.  Scratch contents are deliberately not asserted.
    cpu.bc = 7
    cpu.run(entries[11])
    dma_before = bytes((0xA5,)) * 128
    cpu.mem[0x7200:0x7280] = dma_before
    cpu.mem[platform_read:platform_read + 4] = bytes((0x3E, 0x05, 0xB7, 0xC9))
    cpu.run(entries[13])
    require(cpu.a == 5, "READ did not propagate the physical error status")
    require(cpu.mem[0x7200:0x7280] == dma_before,
            "failed READ modified the caller DMA buffer")

    cpu.mem[0x7310] = 0xA5
    cpu.c = 0
    cpu.run(entries[14])
    require(cpu.a == 5, "WRITE did not propagate its pre-read error status")
    require(cpu.mem[0x7310] == 0xA5,
            "WRITE reached the physical writer after a failed pre-read")
    require(cpu.mem[0x7200:0x7280] == dma_before,
            "failed WRITE modified the caller DMA buffer")

    cpu.mem[platform_read:platform_read + len(read_success)] = read_success
    cpu.mem[platform_write:platform_write + 4] = bytes((0x3E, 0x06, 0xB7, 0xC9))
    cpu.run(entries[14])
    require(cpu.a == 6, "WRITE did not propagate the physical write error")
    require(cpu.mem[0x7200:0x7280] == dma_before,
            "failed physical WRITE modified the caller DMA buffer")

    print(f"executed {COUNT} BIOS-vector contracts from {BASE:04X}h binary")
    print("character transport, disk state, all 80 reads/writes, failure paths, and SECTRAN passed")


if __name__ == "__main__":
    main()
