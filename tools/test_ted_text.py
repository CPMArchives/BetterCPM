#!/usr/bin/env python3
"""Execute the preserving TED stream validator; independent physical-record oracle."""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import random
import re
import shutil
import subprocess
import tempfile

from build_ted import build
from test_usq import SHIM
from test_ted_foundation import Ted


def expected(data):
    padding = data.find(b'\x1a')
    logical = data if padding < 0 else data[:padding]
    faults = []
    for offset, byte in enumerate(logical):
        if byte not in (9, 10, 13) and not 32 <= byte < 127:
            faults.append((offset, 1))
    for match in re.finditer(br'[^\r\n]*', logical):
        if len(match[0]) > 4095:
            faults.append((match.start()+4095, 2))
    if padding >= 0:
        for offset in range(padding+1, len(data)):
            if data[offset] != 26:
                faults.append((offset, 3))
                break
    if faults:
        offset, error = min(faults)
        line = len(re.findall(br'\r\n|\r|\n', logical[:offset]))+1
        return {'error': error, 'offset': offset, 'line': line}
    if len(data) % 128:
        return {'error': 5, 'offset': len(data), 'line': len(re.findall(br'\r\n|\r|\n', logical))+1}
    term = re.search(br'\r\n|\r|\n', logical)
    return {'error': 0, 'length': len(logical), 'physical': len(data),
            'lines': len(re.findall(br'\r\n|\r|\n', logical))+1,
            'column': len(re.split(br'\r\n|\r|\n', logical)[-1]),
            'term': {b'\r\n': 1, b'\n': 2, b'\r': 3}[term[0]] if term else 0,
            'eof': int(padding >= 0)}


class Codec(Ted):
    def address(self, name):
        cache = self.__dict__.setdefault('_addresses', {})
        if name not in cache:
            cache[name] = super().address(name)
        return cache[name]

    def initialize(self):
        self.mem[:] = bytes([0xa5])*65536
        self.mem[0x100:0x100+len(self.image)] = self.image
        self.call('TTX_INIT')

    def call(self, entry, byte=0):
        self.reg['SP'].value = self.symbols['UC_STACK_TOP']
        for index, name in enumerate(('B', 'C', 'D', 'E', 'H', 'L')):
            self.reg[name].value = index+37
        self.reg['A'].value = byte
        self.reg['F'].value = 0xff  # Entry carry must never become a false overflow.
        result = self.lib.test_run(self.address(entry), 10000)
        assert result >= 0, (entry, result)
        assert self.reg['SP'].value == self.symbols['UC_STACK_TOP']
        for index, name in enumerate(('B', 'C', 'D', 'E', 'H', 'L')):
            assert self.reg[name].value == index+37, (entry, name)
        return self.reg['A'].value, self.reg['F'].value & 1

    def value(self, name, size):
        at = self.address(name)
        return int.from_bytes(bytes(self.mem[at:at+size]), 'little')

    def check(self, data):
        self.initialize()
        wanted = expected(data)
        for byte in data:
            result, failed = self.call('TTX_FEED', byte)
            if failed:
                assert result == wanted['error'], (wanted, result)
                break
            assert result == byte
        else:
            result, failed = self.call('TTX_FINISH')
        assert failed == bool(wanted['error']), wanted
        if failed:
            assert self.value('TTX_BADPOS', 3) == wanted['offset'], wanted
            assert self.value('TTX_BADLINE', 3) == wanted['line'], wanted
            state = bytes(self.mem[self.address('TTX_STATE'):self.address('TTX_END')])
            assert self.call('TTX_FEED', 65) == (wanted['error'], 1)
            assert bytes(self.mem[self.address('TTX_STATE'):self.address('TTX_END')]) == state
        else:
            for key, symbol, width in (
                ('length', 'TTX_LENGTH', 3), ('physical', 'TTX_PHYS', 3),
                ('lines', 'TTX_LINES', 3), ('column', 'TTX_COLUMN', 2),
                ('term', 'TTX_TERM', 1), ('eof', 'TTX_EOF', 1)):
                assert self.value(symbol, width) == wanted[key], (key, wanted, self.value(symbol, width))
        return wanted


def tests(machine):
    cases = []
    def records(data):
        return data+b'\x1a'*(-len(data) % 128)
    for data in (b'', b'\x1a'*128, b'\x1a'*384, b'x'*128, b'x'*256,
                 b' a\t \t\r\n\n\r\nx  \rLast\t  ', b'\r', b'\n', b'\r\n',
                 b'x'*127+b'\r\nTail', b'x'*127+b'\rTail',
                 b'x'*126+b'\r\nTail', b'No final newline'):
        cases.append(machine.check(records(data)))
    for length in (127, 128, 129, 161, 162, 163, 4094, 4095, 4096):
        for byte in (b'Z', b'\t'):
            cases.append(machine.check(records(byte*length)))
            cases.append(machine.check(records(b'first\r\n'+byte*length+b'\r\n')))
    for byte in (*range(0, 9), 11, 12, *range(14, 26), *range(27, 33), 127, 128, 255):
        # Space (32) is an intentionally valid boundary fixture.
        cases.append(machine.check(records(b'good\r\n'+bytes([byte])+b'end')))
    for offset in (0, 1, 127, 128, 129, 511, 512):
        cases.append(machine.check(records(b'x'*offset+b'\x1a\x1aTRAIL')))
    rng = random.Random(0x7ed)
    for _ in range(50):
        lines = [bytes(rng.choice([9, *range(32, 127)]) for _ in range(rng.randrange(0, 180)))
                 for _ in range(rng.randrange(1, 10))]
        data = b''
        for line in lines:
            data += line+rng.choice((b'\r', b'\n', b'\r\n'))
        cases.append(machine.check(records(data+rng.choice((b'', b'last\t  ')))))
    cases.append(machine.check(b'partial'))
    machine.initialize()
    at = machine.address('TTX_PHYS')
    machine.mem[at:at+3] = bytes([255])*3
    assert machine.call('TTX_FEED', 65) == (4, 1)
    assert machine.value('TTX_BADPOS', 3) == 0xffffff
    return cases


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    p.add_argument('--z80pack', type=Path, default=Path.home()/'projects/git/z80pack')
    a = p.parse_args()
    with tempfile.TemporaryDirectory(prefix='ted-text-') as directory:
        work = Path(directory)
        image = build(Path.home()/'bin/z80asm', work)
        (work/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h', 'simport.h'):
            shutil.copy2(a.z80pack/'z80sim/srcsim'/name, work/name)
        (work/'shim.c').write_text(SHIM)
        core = a.z80pack/'z80core'
        subprocess.run(['cc', '-shared', '-fPIC', '-O2', f'-I{work}', f'-I{core}',
                        str(work/'shim.c'), str(core/'simglb.c'),
                        *map(str, sorted(core.glob('simz80*.c'))), '-o', str(work/'core.so')], check=True)
        mapping = json.loads((work/'ted-build.json').read_text())['local_symbols']
        machine = Codec(C.CDLL(str(work/'core.so')), image, (work/'TEDDEV.LST').read_text(), mapping)
        cases = tests(machine)
        report = {'status': 'PASS', 'scope': 'compiled preserving stream validator; editor acceptance not asserted',
                  'cases': len(cases)+1, 'payload_sha256': hashlib.sha256(image).hexdigest(),
                  'results': cases}
        if a.output:
            a.output.parent.mkdir(parents=True, exist_ok=True)
            a.output.write_text(json.dumps(report, indent=2)+'\n')
        print('PASS', report['cases'], 'compiled text-stream cases')


if __name__ == '__main__':
    main()
