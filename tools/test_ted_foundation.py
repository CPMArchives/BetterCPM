#!/usr/bin/env python3
"""Execute TED startup/workspace changes on the independent Z80 core.

This bounded gate is not editor qualification. It deliberately does not claim
WordStar, preservation, transactional publication, or native stack acceptance.
"""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from build_ted import build
from test_usq import SHIM
from test_usq_com import Command, diskkey


class Ted(Command):
    def __init__(self, library, image, listing, mapping):
        super().__init__(library, image, listing, required_symbols=(('MEMTOP', 'MAPLIMIT', 'NUMBUF', 'BFPOOL') if 'main' in mapping else ('TTX_INIT',)))
        self.listing, self.mapping = listing, mapping
        self.end = self.address('TED_END')
        self.symbols['UC_STACK_TOP'] = self.address('TED_STACK_TOP')
        self.stack_size = self.address('TED_STACK_SIZE')
        self.symbols['UC_STACK'] = self.symbols['UC_STACK_TOP']-self.stack_size
        self.symbols['UC_INPUT'] = 0x5c

    def address(self, name):
        match = re.search(r'^([0-9a-f]{4}).*\b'+re.escape(name)+r'(?::|\s+EQU\b)', self.listing, re.M|re.I)
        assert match, name
        return int(match[1], 16)

    def callback(self, kind):
        super().callback(kind)
        if self.exception:
            self.reg['PC'].value = 0xffff

    def bdos(self, fn, de):
        if fn == 6:
            self.events.append((fn, de))
            if de & 255 == 255:
                if not self.keys:
                    raise AssertionError(('unexpected input', self.console[-300:]))
                return self.keys.pop(0)
            self.console += chr(de & 255)
            return 0
        if fn in (33, 34):
            self.events.append((fn, de))
            key = self.fcbkey(de)
            record = int.from_bytes(bytes(self.mem[de+33:de+36]), 'little')
            position = record*128
            assert record < 8192, 'work record address wrapped or exceeded map'
            data = self.files[key]
            if fn == 33:
                if self.fail('random_read'):
                    return 1
                if position+128 > len(data):
                    return 1
                self.mem[self.dma:self.dma+128] = data[position:position+128]
            else:
                if self.fail('random_write'):
                    return 1
                if len(data) < position+128:
                    data += bytes(position+128-len(data))
                self.files[key] = data[:position]+bytes(self.mem[self.dma:self.dma+128])+data[position+128:]
            return 0
        return super().bdos(fn, de)

    def execute(self, *, tpa=0xd000, files=None, failures=None, command=b'EX\r', entry=None, setup=None):
        self.files = dict(files or {})
        self.original = dict(self.files)
        self.drive, self.user = 1, 31
        self.failures = failures or {}
        self.late_existing = None
        self.attempts, self.opened, self.searches = {}, {}, {}
        self.events, self.created, self.deleted, self.renamed = [], [], [], []
        self.dma, self.console, self.exception = 0x80, '', None
        self.keys = list(command)
        self.mem[:] = bytes([0xa5])*65536
        self.mem[0x100:0x100+len(self.image)] = self.image
        self.mem[0:3] = bytes.fromhex('c3ffff')
        self.mem[5] = 0xc9
        self.mem[6:8] = tpa.to_bytes(2, 'little')
        self.mem[0x80] = 0
        self.reg['SP'].value = 0xf0
        if setup:
            setup(self)
        protected = bytes(self.mem[tpa:0xfffe])
        result = self.lib.test_run(self.address('START') if entry is None else entry, 30000000)
        assert self.exception is None, self.exception
        assert result >= 0, (result, hex(self.reg['PC'].value), self.console[-300:])
        assert bytes(self.mem[tpa:0xfffe]) == protected, 'active TPA ceiling crossed'
        self.intact()
        assert self.dma == 0x80
        return self.console


def tests(m):
    count = 0
    for tpa in (m.end, m.end+2563, m.end+2564, 0x8000, 0xca01, 0xcf01, 0xd500):
        text = m.execute(tpa=tpa)
        if tpa < m.end+2564:
            assert 'Insufficient TED memory' in text
            assert not m.created and not m.deleted
            assert not any(fn in (15, 16, 17, 19, 22) for fn, _ in m.events)
        else:
            assert '[Exit]' in text
            assert len(m.created) == len(m.deleted) == 1
            assert not m.files
            assert m.word(m.symbols['MEMTOP']) == tpa
            assert m.word(m.symbols['MAPLIMIT']) == m.end+2048
        count += 1
    collision0 = diskkey(1, 'TEW00000.$$$', 31)
    collision1 = diskkey(1, 'TEW00001.$$$', 31)
    legacy = diskkey(1, 'EDITOR.TMP', 31)
    m.execute(files={collision0: b'KEEP0', collision1: b'KEEP1', legacy: b'KEEP OLD'})
    assert m.created == [diskkey(1, 'TEW00002.$$$', 31)]
    count += 1
    all_names = {diskkey(1, f'TEW{i:05d}.$$$', 31): b'KEEP' for i in range(1000)}
    m.execute(files=all_names)
    assert not m.created and not m.deleted and len(m.searches) == 1000
    count += 1
    m.execute(failures={'make': 1}, files={legacy: b'KEEP'})
    assert not m.created and not m.deleted
    count += 1
    m.execute(failures={'close_output': 1})
    assert m.created and not m.deleted and len(m.files) == 1
    count += 1
    m.execute(failures={'delete': 1})
    assert m.created and len(m.files) == 1
    count += 1
    # Real assembled cache/map paths, with only a single cache available.
    # This exercises evictions and random workspace I/O rather than startup
    # arithmetic alone. It is not a text-preservation round-trip assertion.
    document = diskkey(1, 'LARGE.TXT', 31)
    for extra in (0, 516, 1032):
        m.execute(tpa=m.end+2564+extra, files={document: b'0123456789'*8+b'\r\n'},
                  command=b'R LARGE.TXT\rEX\r')
        count += 1
    lines = [f'{i:04d} '+'abcdefghi'*8+'XYZ' for i in range(500)]
    large = ('\r\n'.join(lines)+'\r\n').encode()
    m.execute(tpa=m.end+2564, files={document: large}, command=b'R LARGE.TXT\rPR 1,500\rEX\r')
    assert any(fn == 34 for fn, _ in m.events), 'cache eviction not exercised'
    assert any(fn == 33 for fn, _ in m.events), 'cache reload not exercised'
    assert re.findall(r'[0-9]{4} '+('abcdefghi'*8)+'XYZ', m.console) == lines
    assert m.mem[m.symbols['NUMBUF']] == 1
    assert m.word(m.symbols['BFPOOL']) == m.end+2048
    count += 1
    for operation, expected in (('random_write', '10'), ('random_read', '9')):
        text = m.execute(tpa=m.end+2564, files={document: large},
                         command=b'R LARGE.TXT\rPR 1,500\rEX\r', failures={operation: 1})
        assert re.search(r'Fatal error 0*'+expected+r'\b', text), text[-200:]
        assert len(m.created) == 1 and not m.deleted
        assert m.created[0] in m.files, 'fatal workspace failure erased recovery material'
        count += 1
    # Existing final names cannot be erased by the legacy output adapter.
    def target(machine):
        machine.reg['SP'].value = machine.symbols['UC_STACK_TOP']
        machine.mem[0x5c:0x5c+36] = bytes(36)
        machine.mem[0x5d:0x5d+11] = b'EXIST   TXT'
    final = diskkey(1, 'EXIST.TXT', 31)
    m.execute(files={final: b'ORIGINAL'}, entry=m.address('FCREAT'), setup=target)
    assert not m.created and not m.deleted and m.reg['F'].value & 1
    count += 1
    def dirty(machine):
        machine.reg['SP'].value = machine.symbols['UC_STACK_TOP']
        machine.mem[machine.address('FMODF')] = 1
    text = m.execute(files={final: b'ORIGINAL'}, entry=m.address('CMDW'), setup=dirty)
    assert 'transactional publisher not implemented' in text
    assert m.mem[m.address('FMODF')] == 1
    assert not m.created and not m.deleted and not m.opened
    count += 1
    def underflow(machine):
        machine.reg['SP'].value = machine.symbols['UC_STACK_TOP']
        machine.mem[machine.symbols['BFPOOL']:machine.symbols['BFPOOL']+2] = (0x100).to_bytes(2, 'little')
    text = m.execute(entry=m.address(m.mapping['main']['NEWBUF']), setup=underflow)
    assert 'Fatal error' in text
    assert not m.created and not m.deleted
    count += 1
    return count


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    p.add_argument('--z80pack', type=Path, default=Path.home()/'projects/git/z80pack')
    a = p.parse_args()
    with tempfile.TemporaryDirectory(prefix='ted-foundation-') as directory:
        work = Path(directory)
        image = build(Path.home()/'bin/z80asm', work, legacy=True)
        (work/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h', 'simport.h'):
            shutil.copy2(a.z80pack/'z80sim/srcsim'/name, work/name)
        (work/'shim.c').write_text(SHIM)
        core = a.z80pack/'z80core'
        subprocess.run(['cc', '-shared', '-fPIC', '-O2', f'-I{work}', f'-I{core}',
                        str(work/'shim.c'), str(core/'simglb.c'),
                        *map(str, sorted(core.glob('simz80*.c'))), '-o', str(work/'core.so')], check=True)
        mapping = json.loads((work/'ted-build.json').read_text())['local_symbols']
        m = Ted(C.CDLL(str(work/'core.so')), image, (work/'TEDDEV.LST').read_text(), mapping)
        count = tests(m)
        report = {'status': 'PASS', 'scope': 'startup and workspace foundation only',
                  'editor_qualified': False, 'cases': count, 'static_end': m.end,
                  'executable_sha256': hashlib.sha256(image).hexdigest(),
                  'prepared_source_sha256': hashlib.sha256((work/'TEDDEV.MAC').read_bytes()).hexdigest(),
                  'host_assembler_sha256': hashlib.sha256((Path.home()/'bin/z80asm').read_bytes()).hexdigest(),
                  'core_inputs': {str(path.relative_to(a.z80pack)): hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in [core/'simglb.c', *sorted(core.glob('simz80*.c'))]},
                  'shim_sha256': hashlib.sha256(SHIM.encode()).hexdigest(),
                  'minimum_ceiling': m.end+2564, 'reserved_map_bytes': 2048,
                  'minimum_cache_bytes': 516, 'private_stack_bytes': m.stack_size,
                  'native_stack_measurement': 'NOT_RUN'}
        if a.output:
            a.output.parent.mkdir(parents=True, exist_ok=True)
            a.output.write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(report))


if __name__ == '__main__':
    main()
