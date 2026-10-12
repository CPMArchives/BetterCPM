#!/usr/bin/env python3
"""Execute isolated multiplexed hooks; not full monitor/lifecycle qualification."""
from pathlib import Path
from test_monitor_profiles import load
from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'build/audit/monitor-efficiency/hooks-multiplex'


def main():
    cpu, symbols = load(FOLDER)
    cell = symbols['MP_MON']
    raw = symbols['MC_RAW']
    # Reset covers cold initialization and detaching before movement.
    cpu.run(symbols['MC_BASE'])
    assert cpu.word(cell) == raw
    for index in range(17):
        assert cpu.mem[LAYOUT['BIOS'] + index * 3] == 0xC3
    assert symbols['MONCALL'] == LAYOUT['BIOS'] + 63
    assert symbols['MONRAW'] == LAYOUT['BIOS'] + 66
    assert symbols['MONBASE'] == LAYOUT['BIOS'] + 69

    # Fake provider records operation and input byte, returning FEh.
    provider = 0x8000
    code = bytes((0x32, 0, 0x82, 0x79, 0x32, 1, 0x82, 0x3E, 0xFE, 0xC9))
    cpu.mem[provider:provider + len(code)] = code
    cpu.setword(cell, provider)
    for vector, operation, result in ((12, 0, 0xFE), (6, 1, 0xFF),
                                      (9, 2, 0x7E), (54, 3, 0xFE)):
        cpu.c = 0x41
        initial_sp = cpu.sp
        cpu.run(LAYOUT['BIOS'] + vector)
        assert cpu.mem[0x8200:0x8202] == bytes((operation, 0x41))
        assert cpu.a == result and cpu.sp == initial_sp
    for operation in (4, 5):
        cpu.a = operation
        cpu.run(symbols['MONCALL'])
        assert cpu.mem[0x8200] == operation

    # After detach, the stale provider may be destroyed safely.
    cpu.run(symbols['MONBASE'])
    cpu.mem[provider:provider + len(code)] = b'\xff' * len(code)
    cpu.c = ord('A')
    cpu.run(LAYOUT['BIOS'] + 12)
    assert cpu.mem[0xF800] == ord('A')
    # Raw backend output bypasses the bound provider, avoiding recursion.
    cpu.mem[provider:provider + len(code)] = code
    cpu.setword(cell, provider)
    cpu.mem[0x8200] = 0xCC
    cpu.a, cpu.c = 0, ord('B')
    cpu.run(symbols['MONRAW'])
    assert cpu.mem[0xF801] == ord('B') and cpu.mem[0x8200] == 0xCC
    # Prepared publisher reads the proposed address from private request +35.
    image = (FOLDER / 'publisher.bin').read_bytes()
    base = LAYOUT['CONFIG'] + 0x38F
    cpu.mem[base:base + len(image)] = image
    request, prospective, live, public = 0x6000, 0x6100, 0x6200, 0x6300
    for offset, value in ((27, prospective), (29, live), (31, public),
                           (33, 0xFFFF), (35, provider)):
        cpu.setword(request + offset, value)
    cpu.mem[prospective:prospective + 41] = bytes(range(41))
    cpu.de = request
    cpu.run(base)
    assert cpu.word(cell) == provider
    assert cpu.mem[live:live + 41] == bytes(range(41))
    assert cpu.word(public + 12) == 0xFFFF
    # Reuse the existing movement-order/rejection campaign with the isolated
    # scheduler. Its post-validation detach must preserve the old target on
    # rejection and select fallback on either successful move direction.
    from unittest.mock import patch
    import test_rsxschedule as schedule
    from test_bios import Z80
    image = (FOLDER / 'bios.bin').read_bytes()
    scheduler_image = (FOLDER / 'scheduler-fixture.bin').read_bytes()
    original_read = Path.read_bytes

    class BoundCPU(Z80):
        def __init__(self, unused):
            super().__init__(image)
            self.setword(cell, 0x8000)

        def run(self, address, limit=1000):
            super().run(address, limit)
            if address == schedule.SCHEDULER:
                assert self.word(cell) == (raw if self.a == 0 else 0x8000)

    def read(path):
        if path == schedule.ROOT / 'build/system/rsxschedule.bin':
            return scheduler_image
        if path == schedule.ROOT / 'build/system/rsxmover.bin':
            return original_read(FOLDER / 'mover-fixture.bin')
        return original_read(path)

    with patch.object(schedule, 'Z80', BoundCPU), patch.object(Path, 'read_bytes', read):
        schedule.main()
    print('PASS: multiplexed BIOS routing, normalized input/status, raw bypass,')
    print('fallback after stale-target destruction, and prepared publisher store')
    print('(fake provider; full RSX transaction and terminal rendering not tested)')


if __name__ == '__main__':
    main()
