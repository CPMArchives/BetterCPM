#!/usr/bin/env python3
"""Execute assembled TIME providers against deterministic RTC port responses."""
from __future__ import annotations
import datetime
import hashlib
import json
import re
from pathlib import Path
from test_bios import Z80, require

ROOT = Path(__file__).resolve().parents[1]
REQUEST = 0x7000


def bcd(n):
    return (n // 10) * 16 + n % 10


def record(date):
    days = (date.date() - datetime.date(1977, 12, 31)).days
    return days.to_bytes(2, 'little') + bytes(map(bcd, (date.hour, date.minute, date.second)))


def cpu_for(name):
    cpu = Z80(b'')
    binary = (ROOT / f'build/rsx/{name}.bin').read_bytes()
    cpu.mem[0x8000:0x8000 + len(binary)] = binary
    symbols = {}
    for line in (ROOT / f'build/rsx/{name}.lst').read_text().splitlines():
        m = re.match(r'^([0-9a-f]{4})\s+.*\s([A-Z][A-Z0-9_]*):', line, re.I)
        if m:
            symbols[m[2]] = int(m[1], 16)
    return cpu, symbols


def invoke(cpu, entry, expected, status=0):
    cpu.mem[REQUEST:REQUEST+10] = bytes((1, 10, 0, 0)) + b'\xA5' * 5 + b'\0'
    cpu.mem[REQUEST-1] = 0xC3
    cpu.mem[REQUEST+10] = 0x3C
    cpu.de = REQUEST
    stack = cpu.sp
    cpu.run(entry, limit=800000)
    require(cpu.a == status and cpu.hl == (REQUEST+4 if status == 0 else 0),
            f'wrong native result A={cpu.a}, HL={cpu.hl:04x}, expected status {status}')
    require(cpu.sp == stack and cpu.de == REQUEST, 'request/stack not preserved')
    require(bytes(cpu.mem[REQUEST+4:REQUEST+9]) == (expected if status == 0 else b'\xA5'*5),
            'bad publication or failed GET changed caller data')
    require(cpu.mem[REQUEST-1] == 0xC3 and cpu.mem[REQUEST+10] == 0x3C, 'request guard changed')


class CPMSIM:
    def __init__(self, mode, attempts):
        self.mode, self.attempts = mode, attempts
        self.selected, self.reads, self.writes = 0, 0, []
    def write(self, port, value):
        require(port & 255 == 25 and value in (0, 1, 2, 3, 4), 'unexpected RTC write/mode toggle')
        self.selected = value
        self.writes.append(value)
    def read(self, port):
        if port & 255 == 25:
            return self.mode
        require(port & 255 == 26, 'unexpected RTC read')
        attempt, field = divmod(self.reads, 6)
        require(attempt < len(self.attempts), 'unexpected extra sampling attempt')
        require(self.selected == [0, 3, 4, 2, 1, 0][field], 'wrong RTC field selection')
        self.reads += 1
        return self.attempts[attempt][field]


def attempt(date, mode=0, end_second=None):
    data = record(date)
    h, m, s = (date.hour, date.minute, date.second) if mode else data[2:]
    return [s, data[0], data[1], h, m, s if end_second is None else end_second]


class FreHD:
    def __init__(self, sample, size=6, status=0):
        self.sample, self.size, self.status = sample, size, status
        self.latched, self.reads, self.latches = None, 0, []
    def write(self, port, value):
        port &= 255
        if port == 0xEC:
            self.latches.append(value)
        else:
            require(port == 0xC4 and value == 1, 'unexpected FreHD command')
            self.latched = bytes(self.sample)
    def read(self, port):
        port &= 255
        if port == 0xCF:
            return self.status
        if port == 0xC3:
            return self.size
        require(port == 0xC2 and self.latched is not None, 'unlatched FreHD read')
        value = self.latched[self.reads]
        self.reads += 1
        # The live clock can roll over mid-transfer; the response stays latched.
        self.sample = bytes((0, 0, 0, 26, 1, 1))
        return value


def frehd_sample(date):
    return bytes((date.second, date.minute, date.hour, date.year-2000, date.day, date.month))


def main():
    results = []
    boundaries = [(2000,2,28), (2000,2,29), (2001,2,28),
                  (2026,4,30), (2026,12,31), (2099,12,30)]
    for mode in (0, 1):
        for y,m,d in boundaries:
            old = datetime.datetime(y,m,d,23,59,59)
            new = old + datetime.timedelta(seconds=1)
            clock = CPMSIM(mode, [attempt(old, mode, 0), attempt(new, mode)])
            cpu, names = cpu_for('zprtc')
            cpu.port_read, cpu.port_write = clock.read, clock.write
            invoke(cpu, names['ZP_SERVICE'], record(new))
            require(clock.reads == 12, 'torn midnight sample was not retried exactly once')
            results.append(f'ZPRTC mode {mode}: midnight {old.date()}')
        cpu, names = cpu_for('zprtc')
        old = datetime.datetime(2026,10,6,12,34,59)
        new = old + datetime.timedelta(seconds=1)
        clock = CPMSIM(mode, [attempt(old, mode, 0)]*3 + [attempt(new, mode)])
        cpu.port_read, cpu.port_write = clock.read, clock.write
        invoke(cpu, names['ZP_SERVICE'], record(new))
        require(clock.reads == 24, 'fourth coherent sample not accepted')
        clock = CPMSIM(mode, [attempt(old, mode, 0)]*4)
        cpu.port_read, cpu.port_write = clock.read, clock.write
        invoke(cpu, names['ZP_SERVICE'], None, 5)
        require(clock.reads == 24, 'retry limit not exactly four')
        results.append(f'ZPRTC mode {mode}: retry success and exhaustion')
    for y,m,d in boundaries:
        for seconds in (0, 1):
            date = datetime.datetime(y,m,d,23,59,59) + datetime.timedelta(seconds=seconds)
            clock = FreHD(frehd_sample(date))
            cpu, names = cpu_for('frehdtime')
            cpu.port_read, cpu.port_write = clock.read, clock.write
            invoke(cpu, names['FT_SERVICE'], record(date))
            require(clock.reads == 6 and clock.latches == [0x50,0x40], 'wrong snapshot/map lifecycle')
            results.append(f'FreHD snapshot: {date}')
    report = ROOT / 'build/test-results/clock-sampling'
    report.mkdir(parents=True, exist_ok=False)
    (report / 'evidence.json').write_text(json.dumps({'result':'PASS','cases':results,
        'sha256':{name:hashlib.sha256((ROOT / f'build/rsx/{name}.bin').read_bytes()).hexdigest()
                  for name in ['zprtc','frehdtime']}},indent=2)+'\n')
    print(f'PASS: {len(results)} provider sampling/rollover checks, actual assembled routines')


if __name__ == '__main__':
    main()
