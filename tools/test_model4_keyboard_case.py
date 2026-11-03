#!/usr/bin/env python3
"""Execute assembled case/rollover code and BIOS space-saving paths.

Instruction-level regression only: hardware timing and native interaction still
require trs80gp and physical Model 4 qualification. Disk I/O is stubbed here.
"""
import random
from pathlib import Path

from system_layout import LAYOUT
from test_monitor_profiles import load

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'build/bios'


def translation(slot, modifiers, state):
    """Independent matrix contract, including unconnected alphabet-row slots."""
    base = list(range(64, 96)) + list(b'0123456789:;,-./') + [13, 27, 3, 11, 10, 28, 29, 32]
    value = base[slot]
    if modifiers & 4:
        if slot < 32:
            return slot
        punctuation = dict(zip(b',-./0123456789', b'{_}\\0|2~4^6`[]'))
        return punctuation.get(value, 127 if value == 27 else value)
    if 1 <= slot <= 26:
        return value if modifiers & 3 or not state & 32 else value + 32
    if slot < 32 or not modifiers & 3:
        return value
    if value == 28:
        return 127
    return value ^ 16 if value >= 44 and value != 48 else value


def translation_checks():
    cpu, symbols = load(FOLDER)
    count = 0
    for state in (0, 8, 32, 40):
        cpu.mem[symbols['M4_KSTATE']] = state
        for modifiers in range(256):
            cpu.mem[0xF480] = modifiers
            for slot in range(56):
                cpu.de = slot
                cpu.run(symbols['M4_KEYFD'])
                expected = translation(slot, modifiers, state)
                assert cpu.a == expected, (slot, modifiers, state, cpu.a, expected)
                assert cpu.d == 0
                count += 1
    print(f'PASS: {count} translations, all modifier bytes and four CAPS states')

    cpu.mem[symbols['M4_KSTATE']] = 32
    for modifiers in range(8):
        cpu.mem[0xF480] = modifiers
        for slot in range(56):
            row, column = divmod(slot, 8)
            address = 0xF400 + (1 << row)
            cpu.mem[address] = 1 << column
            cpu.run(symbols['M4_SCAN'])
            assert (cpu.a, cpu.d, cpu.e) == (translation(slot, modifiers, 32), 0, slot)
            cpu.mem[address] = 0
    cpu.run(symbols['M4_SCAN'])
    assert (cpu.a, cpu.d, cpu.e) == (0, 0, 56)
    print('PASS: 448 matrix scans and empty-scan scratch-register contract')


class ModifierSamples(bytearray):
    def __getitem__(self, address):
        if address == 0xF480 and self.samples:
            return self.samples.pop(0)
        return super().__getitem__(address)


def caps_checks():
    cpu, symbols = load(FOLDER)
    cpu.mem = ModifierSamples(cpu.mem)
    for state in (0, 8, 32, 40):
        for first in (0, 8):
            for second in (0, 8):
                for noise in (0, 0xF7):
                    cpu.mem[symbols['M4_KSTATE']] = state
                    cpu.mem.samples = [first | noise, second | noise]
                    cpu.run(symbols['M4_SCAN'], limit=15000)
                    edge = (state ^ first) & 8
                    expected = state ^ (8 | (32 if first else 0)) if edge and first == second else state
                    assert cpu.mem[symbols['M4_KSTATE']] == expected, (state, first, second)
                    assert (cpu.a, cpu.d, cpu.e, cpu.sp) == (0, 0, 56, 0xE000)
    # Confirmed CAPS with a held A changes translation, not physical identity.
    cpu.mem[0xF401] = 2
    cpu.mem[symbols['M4_KSTATE']] = 32
    for physical, state, character in ((8, 8, 65), (0, 0, 65), (8, 40, 97), (0, 32, 97)):
        cpu.mem.samples = [physical, physical, physical]
        cpu.run(symbols['M4_SCAN'], limit=15000)
        assert (cpu.a, cpu.e, cpu.mem[symbols['M4_KSTATE']]) == (character, 1, state)
    cpu.port_write = lambda port, value: None
    for state in (0, 8, 32, 40):
        cpu.mem[symbols['M4_KSTATE']] = state
        cpu.run(symbols['M4_INIT'])
        assert cpu.mem[symbols['M4_KSTATE']] == state
    print('PASS: CAPS press/release confirmation, rejected transients, noise and held-letter transitions')


class EndEvents(Exception):
    pass


class ScanEvents(bytearray):
    def __getitem__(self, address):
        if address == self.scan:
            try:
                identity, character = next(self.events)
            except StopIteration:
                raise EndEvents from None
            # Stub the scan only, executing the real input queue unmodified.
            self[address:address+7] = bytes((0x3E, character, 0x1E, identity, 0x16, 0, 0xC9))
        return super().__getitem__(address)


def input_checks():
    rng = random.Random(0xCA95)
    cpu, symbols = load(FOLDER)
    cpu.mem = ScanEvents(cpu.mem)
    cpu.mem.scan = symbols['M4_SCAN']
    for _ in range(4096):
        events = [(rng.randrange(56), rng.choice((0, 1, 65, 97, 127))) for _ in range(12)] + [(56, 0)]
        identity, pending = 255, 0
        expected = []
        for physical, character in events:
            if not character:
                identity = 255
                if pending:
                    expected.append(pending)
                pending = 0
            elif physical != identity:
                if pending:
                    expected.append(pending)
                identity, pending = physical, character
        cpu.mem[symbols['M4_PENDING']:symbols['M4_PENDING']+2] = b'\xff\0'
        cpu.mem.events = iter(events)
        cpu.sp = 0xE000
        observed = []
        try:
            while True:
                cpu.run(symbols['M4_IN'])
                observed.append(cpu.a)
                assert cpu.sp == 0xE000
        except EndEvents:
            pass
        assert observed == expected, (events, observed, expected)
    print('PASS: 4096 deterministic rollover/release/held-modifier input traces')


class PhysicalReads(bytearray):
    def __getitem__(self, address):
        if address == 0x9200:
            cpu = self.cpu
            self.reads.append((cpu.a, cpu.b, cpu.c, cpu.hl))
            status = next(self.statuses)
            cpu.hl = (cpu.hl + 512) & 0xFFFF
            cpu.de, cpu.bc = 0xDEAD, 0xABCD
            self[address:address+4] = bytes((0x3E, status, 0xB7, 0xC9))
        return super().__getitem__(address)


def compaction_checks():
    cpu, symbols = load(FOLDER)
    for slot in range(8):
        cpu.mem[symbols['BIO_QUART']] = slot
        cpu.run(symbols['BIO_SLOT'])
        assert (cpu.hl, cpu.bc, cpu.a, cpu.z) == (LAYOUT['MODULEBUF'] + 128*slot, 128, 0, True)
    # The MONCALL trampoline is inspected by existing API 1.7 clients.
    trampoline = symbols['MONCALL']
    assert cpu.mem[trampoline] == 0xC3
    assert cpu.mem[cpu.word(trampoline+1)] == 0x2A  # LD HL,(MP_MON)
    cpu.mem = PhysicalReads(cpu.mem)
    cpu.mem.cpu = cpu
    cpu.mem[symbols['BIOPHREAD']:symbols['BIOPHREAD']+3] = bytes((0xC3, 0, 0x92))
    rng = random.Random(0xF37C)
    for _ in range(512):
        table = bytes(rng.randrange(256) for _ in range(6))
        cpu.mem[0x9500:0x9506] = table
        for statuses in ((0, 0), (7,), (0, 9)):
            cpu.mem.reads = []
            cpu.mem.statuses = iter(statuses)
            cpu.hl, cpu.de, cpu.ix = 0x8000, 0x9500, 0x1234
            cpu.run(symbols['M4_FETCH'])
            expected = [(*table[:3], 0x8000)]
            if statuses[0] == 0:
                expected.append((*table[3:], 0x8200))
            assert cpu.mem.reads == expected
            assert (cpu.a, cpu.z, cpu.ix, cpu.sp) == (statuses[-1], statuses[-1] == 0, 0x1234, 0xE000)
    selector = LAYOUT['RSX_SELECTOR']
    cpu.mem[selector:selector+4] = bytes((0x32, 0, 0x93, 0xC9))
    for value in range(256):
        for statuses in ((0, 0), (7,), (0, 9)):
            cpu.mem.reads, cpu.mem.statuses = [], iter(statuses)
            cpu.mem[0x9300] = 0xCC
            cpu.a, cpu.ix = value, 0x1234
            cpu.run(symbols['M4_RSLOAD'])
            assert cpu.a == (value if statuses[-1] == 0 else statuses[-1])
            assert cpu.mem[0x9300] == (value if statuses[-1] == 0 else 0xCC)
            assert (cpu.ix, cpu.sp) == (0x1234, 0xE000)
            assert cpu.mem.reads[0][3] == LAYOUT['CONFIG']
            assert len(cpu.mem.reads) == len(statuses)
    print('PASS: eight 1024-byte-buffer slots, API 1.7 trampoline and 1536 arbitrary two-sector fetch/error cases')
    print('PASS: 768 RSX-selector success/error cases, selector preservation and balanced stack')


def routing_checks():
    cpu, symbols = load(FOLDER)
    cpu.setword(symbols['MP_MON'], 0x9000)
    for iobyte in range(256):
        cpu.mem[3] = iobyte
        console, printer = iobyte & 3, iobyte >> 6
        for status in (0, 1, 0x7E, 0xFF):
            # Provider records operation, returns arbitrary status/character.
            cpu.mem[0x9000:0x9006] = bytes((0x32, 0, 0x91, 0x3E, status, 0xC9))
            for label, expected, operation in (
                ('BIOCONST', 255 if console == 1 and status else 0, 1 if console == 1 else 0xCC),
                ('BIOCONIN', status & 127 if console == 1 else 26, 2 if console == 1 else 0xCC),
                ('BIOLSTST', 255 if printer == 1 else 0, 0xCC),
                ('BIOCONOT', None, 0 if console == 1 or console == 2 and printer == 1 else 0xCC),
                ('BIOLIST', None, 0 if printer == 1 else 0xCC),
            ):
                cpu.mem[0x9100] = 0xCC
                cpu.c = 0x58
                cpu.run(symbols[label])
                assert cpu.mem[0x9100] == operation, (iobyte, label)
                assert expected is None or cpu.a == expected, (iobyte, label, cpu.a, expected)
                assert cpu.sp == 0xE000
    print('PASS: 5120 console/list routing and status cases across every IOBYTE')


if __name__ == '__main__':
    translation_checks()
    caps_checks()
    input_checks()
    compaction_checks()
    routing_checks()
