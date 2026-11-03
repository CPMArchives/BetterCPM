"""Boundary cases for the small Z80 runner's LDIR and LDDR."""
import unittest

from test_bios import Z80


class WriteTrace(bytearray):
    def __setitem__(self, address, value):
        self.writes.append(address)
        super().__setitem__(address, value)


class BlockTransferTests(unittest.TestCase):
    def machine(self, opcode, src, dst, count):
        cpu = Z80(b'')
        cpu.mem[0x100:0x103] = bytes((0xED, opcode, 0xC9))
        cpu.hl, cpu.de, cpu.bc = src, dst, count
        cpu.z = cpu.carry = True
        return cpu

    def test_counts_and_address_wrap(self):
        for opcode, step in ((0xB0, 1), (0xB8, -1)):
            for initial, transfers in ((1, 1), (0xFFFF, 65535), (0, 65536)):
                with self.subTest(opcode=opcode, initial=initial):
                    # Copy each byte onto itself so the return stack and code survive.
                    start = 0xFFFF if step == 1 else 0
                    cpu = self.machine(opcode, start, start, initial)
                    cpu.mem = WriteTrace(cpu.mem)
                    cpu.mem.writes = []
                    cpu.run(0x100)
                    # The first two writes install run()'s return address.
                    self.assertEqual(cpu.mem.writes[2:],
                                     [(start + step*i) & 0xFFFF for i in range(transfers)])
                    end = (start + step*transfers) & 0xFFFF
                    self.assertEqual((cpu.hl, cpu.de, cpu.bc), (end, end, 0))
                    self.assertTrue(cpu.z and cpu.carry)

    def test_overlap_propagates_one_byte_at_a_time(self):
        for opcode, src, step in ((0xB0, 0xFFFE, 1), (0xB8, 1, -1)):
            with self.subTest(opcode=opcode):
                dst = (src + step) & 0xFFFF
                cpu = self.machine(opcode, src, dst, 4)
                cpu.mem[src] = 0x5A
                cpu.run(0x100)
                self.assertEqual([cpu.mem[(dst + step*i) & 0xFFFF] for i in range(4)],
                                 [0x5A] * 4)
                self.assertEqual((cpu.hl, cpu.de, cpu.bc),
                                 ((src + 4*step) & 0xFFFF, (dst + 4*step) & 0xFFFF, 0))

    def test_overwritten_opcode_is_fetched_again(self):
        for opcode, step in ((0xB0, 1), (0xB8, -1)):
            with self.subTest(opcode=opcode):
                cpu = self.machine(opcode, 0x200, 0x100, 0)
                cpu.mem[0x200] = 0xC9  # RET replaces the ED prefix on the first transfer.
                cpu.run(0x100)
                self.assertEqual((cpu.hl, cpu.de, cpu.bc), (0x200 + step, 0x100 + step, 0xFFFF))


if __name__ == '__main__':
    unittest.main()
