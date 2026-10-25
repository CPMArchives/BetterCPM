#!/usr/bin/env python3
"""Run TED's actual record publisher on a hostile, extent-aware BDOS model.

MAKE/RENAME intentionally overwrite names unless the guest guards them. Faults
may be reported either before or after the actual mutation. This is a synthetic
fault gate; real CP/M filesystem and native qualification are separate gates.
"""
import argparse
import ctypes as C
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from build_ted import source
from test_ted_text import Codec
from test_usq import SHIM

PROBE = '''
TP_REWIND: LD C,250
 CALL 5
 OR A
 RET
TP_RECORD: LD C,251
 CALL 5
 RET
TP_DEFER: LD C,253
 CALL 5
 RET
TP_POLL: LD C,252
 CALL 5
 OR A
 RET Z
 SCF
 RET
'''


@dataclass
class File:
    data: bytes
    inode: int
    attributes: list


class Publisher(Codec):
    def callback(self, kind):
        try:
            assert kind == 0
            sp = self.reg['SP'].value
            assert self.symbols['UC_STACK'] <= sp < self.symbols['UC_STACK_TOP']
            function = self.reg['C'].value
            de = self.reg['D'].value << 8 | self.reg['E'].value
            result = self.bdos(function, de)
            self.reg['A'].value = result
            self.reg['F'].value = 0xff
            for index, name in enumerate(('B', 'C', 'D', 'E', 'H', 'L')):
                self.reg[name].value = 0xe0+index
        except BaseException as error:
            self.exception = error
            self.reg['PC'].value = 0xffff

    def add(self, key, data, *, ro=False, sys=False, arc=False, last_extent_only=False):
        assert len(data) % 128 == 0
        attrs = [bytearray(11) for _ in range(max(1, (len(data)+16383)//16384))]
        for a in (attrs[-1:] if last_extent_only else attrs):
            a[8], a[9], a[10] = 128*ro, 128*sys, 128*arc
        self.inode += 1
        self.files[key] = File(data, self.inode, attrs)

    def fault(self, fn, after):
        spec = self.failures.get(fn)
        return spec is not None and spec == (self.calls[fn], after)

    def bdos(self, fn, de):
        if fn == 250:
            self.cursor = 0
            return 0
        if fn == 251:
            if self.cursor == len(self.payload):
                return 1
            assert self.cursor < len(self.payload)
            at = self.address('TS_BUFFER')
            self.mem[at:at+128] = self.payload[self.cursor:self.cursor+128]
            self.cursor += 128
            return 0
        if fn == 253:
            assert self.mem[self.address('TS_PHASE')]>=5, 'deferral outside committed publication'
            self.deferred+=1
            self.user,self.drive,self.dma=31,16,0x80
            return 0
        if fn == 252:
            self.polls += 1
            phase = self.mem[self.address('TS_PHASE')]
            assert phase < 5, 'cancellable poll inside namespace publication'
            return int(self.polls == self.cancel_at)
        self.calls[fn] = self.calls.get(fn, 0)+1
        self.events.append((fn, de, self.user))
        if self.observer:
            self.observer(self, fn, de, False)
        if self.fault(fn, False):
            return 2 if fn in (20, 21) else 255
        result = self.actual(fn, de)
        if self.observer:
            self.observer(self, fn, de, True)
        if self.fault(fn, True):
            return 2 if fn in (20, 21) else 255
        return result

    def actual(self, fn, de):
        if fn == 32:
            if de & 255 != 255:
                self.user = de & 255
            return self.user
        if fn == 26:
            self.dma = de
            return 0
        key = self.fcbkey(de)
        if fn in (17, 18):
            if fn == 17:
                self.matches = []
                obj = self.files.get(key)
                if obj:
                    for index, attributes in enumerate(obj.attributes):
                        entry = bytearray(32)
                        entry[0] = self.user
                        entry[1:12] = bytes((self.mem[de+i+1] & 127) | attributes[i] for i in range(11))
                        entry[12] = index & 31
                        entry[14] = index >> 5
                        entry[15] = min(128, max(0, len(obj.data)//128-index*128))
                        # Stable allocation metadata independent of names and
                        # attributes, changing when another object is substituted.
                        entry[16:20] = obj.inode.to_bytes(4, 'little')
                        entry[20:24] = index.to_bytes(4, 'little')
                        self.matches.append(bytes(entry))
            if not self.matches:
                return 255
            entry = self.matches.pop(0)
            self.mem[self.dma:self.dma+128] = entry+bytes([229])*96
            return 0
        if fn == 15:
            if key not in self.files:
                return 255
            self.opened[de] = [key, 0]
            return 2
        if fn == 22:
            # Deliberately destructive: a broken guest preflight loses data.
            self.add(key, b'')
            self.opened[de] = [key, 0]
            self.mutations.append(('make', key))
            return 1
        if fn == 16:
            assert de in self.opened, ('stale close', de, key)
            assert self.opened[de][0][1] == self.user
            del self.opened[de]
            return 3
        if fn in (20, 21, 33):
            assert de in self.opened, ('unopened FCB', fn, de)
            key, offset = self.opened[de]
            if fn == 33:
                offset = int.from_bytes(bytes(self.mem[de+33:de+36]), 'little')*128
            assert key[1] == self.user, 'wrong DU for active FCB'
            obj = self.files[key]
            if fn in (20, 33):
                if offset >= len(obj.data):
                    return 1
                assert offset+128 <= len(obj.data)
                self.mem[self.dma:self.dma+128] = obj.data[offset:offset+128]
            else:
                data = bytes(self.mem[self.dma:self.dma+128])
                obj.data = obj.data[:offset]+data+obj.data[offset+128:]
                required = max(1, (len(obj.data)+16383)//16384)
                while len(obj.attributes) < required:
                    obj.attributes.append(bytearray(obj.attributes[-1]))
                for attrs in obj.attributes:
                    attrs[10] &= 127
                self.mutations.append(('write', key))
            self.opened[de][1] += 128
            return 0
        if fn == 30:
            obj = self.files.get(key)
            if not obj:
                return 255
            attrs = bytearray(self.mem[de+i+1] & 128 for i in range(11))
            obj.attributes = [bytearray(attrs) for _ in obj.attributes]
            self.mutations.append(('attributes', key))
            return 0
        if fn == 23:
            obj = self.files.get(key)
            if not obj or any(x[8] for x in obj.attributes):
                return 255
            target = self.fcbkey(de, 16)
            self.files[target] = self.files.pop(key)  # destructive if unchecked
            self.mutations.append(('rename', key, target))
            return 0
        if fn == 19:
            raise AssertionError('Publisher must never erase any file')
        raise AssertionError(('unexpected BDOS', fn))

    def descriptor(self, address, key):
        drive, user, filename = key
        name, _, extension = filename.partition('.')
        self.mem[address:address+37] = bytes(37)
        self.mem[address] = drive
        self.mem[address+1:address+12] = (name.ljust(8)+extension.ljust(3)).encode()
        self.mem[address+36] = user

    def run(self, payload, existing=b'ORIGINAL'+bytes(120), *, replace=True, protect=True,
            key=(1, 0, 'TEST.TXT'), attrs=None, failures=None, cancel_at=0, extras=None,
            aliases=(), observer=None, defer=False):
        assert len(payload) % 128 == 0
        self.mem[:] = bytes([0xa5])*65536
        self.mem[0x100:0x100+len(self.image)] = self.image
        self.mem[5] = 0xc9
        self.files, self.opened, self.calls = {}, {}, {}
        self.inode = 1
        self.user, self.drive, self.dma = 7, 1, 0x80
        self.payload, self.cursor, self.polls, self.cancel_at = payload, 0, 0, cancel_at
        self.failures, self.observer = failures or {}, observer
        self.events, self.mutations, self.exception = [], [], None
        self.matches = []
        self.deferred=0
        if existing is not None:
            self.add(key, existing, **(attrs or {}))
        for name, data in (extras or {}).items():
            self.add(name, data)
        original = {k: v.data for k, v in self.files.items()}
        self.descriptor(self.address('TS_TARGET'), key)
        self.mem[self.address('TS_REPLACE')] = int(replace)
        self.mem[self.address('TS_PROTECT')] = int(protect)
        self.mem[self.address('TS_ALIAS_COUNT')] = len(aliases)
        for i, alias in enumerate(aliases):
            self.descriptor(self.address('TS_ALIASES')+i*37, alias)
        if defer:
            at=self.address('TS_DEFER_PTR')
            self.mem[at:at+2]=self.address('TP_DEFER').to_bytes(2,'little')
        for variable, entry in (('TS_REWIND_PTR', 'TP_REWIND'), ('TS_RECORD_PTR', 'TP_RECORD'), ('TS_POLL_PTR', 'TP_POLL')):
            at = self.address(variable)
            self.mem[at:at+2] = self.address(entry).to_bytes(2, 'little')
        self.reg['SP'].value = self.symbols['UC_STACK_TOP']
        protected = bytes(self.mem[0xc000:0xfffe])
        result = self.lib.test_run(self.address('TS_RUN'), 100000000)
        assert self.exception is None, self.exception
        assert result >= 0, (result, hex(self.reg['PC'].value))
        assert self.reg['SP'].value == self.symbols['UC_STACK_TOP']
        assert bytes(self.mem[0xc000:0xfffe]) == protected
        assert self.user == 7 and self.dma == 0x80
        error = self.mem[self.address('TS_ERROR')]
        assert bool(self.reg['F'].value & 1) == bool(error)
        # Every unrelated original is immutable, even on ambiguous mutations.
        for name, data in original.items():
            if name != key:
                assert self.files[name].data == data, ('unrelated file changed', name)
        return error


def tests(m):
    cases = []
    new = bytes(range(128))*3
    old = b'ORIGINAL'+bytes(120)
    target = (1, 0, 'TEST.TXT')
    assert m.run(new) == 0
    assert m.files[target].data == new
    assert m.files[(1, 0, 'TEB00000.BAK')].data == old
    assert (1, 0, 'TET00000.$$$') not in m.files
    cases.append('replace')
    for user in (0, 7, 15, 16, 31):
        for drive in (1, 2, 16):
            key = drive, user, 'TEST.TXT'
            assert m.run(new, key=key) == 0
            assert m.files[key].data == new
            cases.append(f'DU {drive}/{user}')
    for payload in (b'', bytes(128), bytes(256)):
        assert m.run(payload, existing=None) == 0
        assert m.files[target].data == payload
        cases.append(f'new {len(payload)}')
    assert m.run(new, replace=False) == 1
    assert not m.mutations
    cases.append('overwrite authorization')
    for flags in ({'ro': True}, {'sys': True}, {'ro': True, 'sys': True, 'arc': True}):
        assert m.run(new, attrs=flags, protect=False) == 2
        assert not m.mutations
        assert m.run(new, attrs=flags) == 0
        final = m.files[target]
        assert bool(final.attributes[0][8]) == flags.get('ro', False)
        assert bool(final.attributes[0][9]) == flags.get('sys', False)
        assert final.attributes[0][10] == 0
        cases.append('protected '+str(flags))
    large = bytes(32768)
    assert m.run(new, existing=large, attrs={'ro': True, 'sys': True, 'last_extent_only': True}, protect=False) == 2
    assert not m.mutations
    cases.append('physical extent union')
    keep = {(1, 0, 'TET00000.$$$'): bytes(128), (1, 0, 'TEB00000.BAK'): bytes(256)}
    assert m.run(new, extras=keep) == 0
    assert m.files[(1, 0, 'TEB00001.BAK')].data == old
    cases.append('unrelated recovery names')
    assert m.run(new, aliases=(target,)) == 6
    assert not m.mutations
    cases.append('target workspace alias')
    for bad in ('*.TXT', 'A?.TXT', 'A/B.TXT', 'A\\B.TXT', 'A;B.TXT', 'A[B.TXT', 'A B.TXT', 'A:B.TXT'):
        assert m.run(new, key=(1, 0, bad), existing=None) == 11, bad
        assert not m.mutations
        cases.append('bad descriptor '+bad)
    # Record verification, independently of CLOSE's return status.
    def corrupt(m, fn, de, after):
        if fn == 16 and after and m.mem[m.address('TS_PHASE')] == 2:
            stage = m.files[(1, 0, 'TET00000.$$$')]
            stage.data = bytes([stage.data[0] ^ 1])+stage.data[1:]
    assert m.run(new, observer=corrupt) == 4
    assert m.files[target].data == old
    cases.append('readback corruption')
    def unexpected(m, fn, de, after):
        if fn == 23 and after and m.calls[23] == 1:
            m.add(target, b'UNEXPECTED'+bytes(118))
    assert m.run(new, observer=unexpected) != 0
    assert m.files[target].data == b'UNEXPECTED'+bytes(118)
    assert m.files[(1, 0, 'TEB00000.BAK')].data == old
    assert m.calls[23] == 1
    cases.append('unexpected final blocks rollback')
    def altered_backup(m, fn, de, after):
        if fn == 23 and after and m.calls[23] == 1:
            m.add((1, 0, 'TEB00000.BAK'), b'OTHER BACKUP'+bytes(116))
    assert m.run(new, observer=altered_backup) != 0
    assert m.files[(1, 0, 'TEB00000.BAK')].data == b'OTHER BACKUP'+bytes(116)
    assert m.calls[23] == 1
    cases.append('substituted backup not restored')
    # Discover every actual disk-call boundary, then report failure before and
    # after its side effect. New output is never reported committed on failure
    # except when a rename's independently verified namespace proves it moved.
    assert m.run(new) == 0
    normal_counts = dict(m.calls)
    for fn in (15, 16, 20, 21, 22, 23, 30):
        for nth in range(1, normal_counts.get(fn, 0)+1):
            for after in (False, True):
                error = m.run(new, failures={fn: (nth, after)})
                if error == 0:
                    assert m.files[target].data == new
                    assert any(f.data == old for f in m.files.values())
                else:
                    assert any(f.data == old for f in m.files.values()), (fn, nth, after, error)
                    assert m.files.get(target) is None or m.files[target].data in (old, new)
                cases.append(f'fault {fn}/{nth}/{after}: {error}')
    for nth in range(1, 10):
        error = m.run(new, cancel_at=nth)
        if error:
            assert error == 7 and m.files[target].data == old
        else:
            assert m.files[target].data == new
        cases.append(f'cancel {nth}: {error}')
    # A failed existence search may not authorize destructive MAKE over a
    # collision: a second independent namespace check guards the mutation.
    assert m.run(new, extras=keep, failures={17: (2, False)}) != 0
    assert m.files[(1, 0, 'TET00000.$$$')].data == bytes(128)
    cases.append('reservation search failure')
    many = {(1, 0, f'TET{i:05d}.$$$'): b'' for i in range(1000)}
    assert m.run(new, extras=many) == 10
    assert not m.mutations
    cases.append('bounded reservation exhaustion')
    assert m.run(new,defer=True,extras={(1,31,'TEST.TXT'):bytes([77])*128})==0
    assert m.deferred>0 and m.files[target].data==new
    cases.append('non-cancelling critical input observer changes DU/DMA; every read rebinds and unrelated file survives')
    return cases


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    p.add_argument('--z80pack', type=Path, default=Path.home()/'projects/git/z80pack')
    a = p.parse_args()
    with tempfile.TemporaryDirectory(prefix='ted-publisher-') as directory:
        work = Path(directory)
        prepared, mapping = source()
        prepared = prepared.replace('TED_END EQU $', PROBE+'\nTED_END EQU $')
        (work/'probe.mac').write_text(prepared)
        subprocess.run([str(Path.home()/'bin/z80asm'), '-e32', '-fb', '-o'+str(work/'probe.bin'),
                        '-l'+str(work/'probe.lst'), str(work/'probe.mac')], check=True)
        image = (work/'probe.bin').read_bytes()
        (work/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h', 'simport.h'):
            shutil.copy2(a.z80pack/'z80sim/srcsim'/name, work/name)
        (work/'shim.c').write_text(SHIM)
        core = a.z80pack/'z80core'
        subprocess.run(['cc', '-shared', '-fPIC', '-O2', f'-I{work}', f'-I{core}',
                        str(work/'shim.c'), str(core/'simglb.c'),
                        *map(str, sorted(core.glob('simz80*.c'))), '-o', str(work/'core.so')], check=True)
        machine = Publisher(C.CDLL(str(work/'core.so')), image, (work/'probe.lst').read_text(), mapping)
        results = tests(machine)
        report = {'status': 'PASS', 'scope': 'compiled publisher synthetic BDOS faults only',
                  'cases': len(results), 'probe_sha256': hashlib.sha256(image).hexdigest(), 'results': results}
        if a.output:
            a.output.parent.mkdir(parents=True, exist_ok=True)
            a.output.write_text(json.dumps(report, indent=2)+'\n')
        print('PASS', len(results), 'compiled publisher cases')


if __name__ == '__main__':
    main()
