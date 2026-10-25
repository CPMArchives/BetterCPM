#!/usr/bin/env python3
"""Compiled immutable-workspace transactions, preserving saves and failure gates."""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zlib

from build_ted import source
from test_ted_publisher import Publisher, PROBE
from test_usq import SHIM


class Workspace(Publisher):
    def bdos(self, fn, de):
        if fn == 252:
            self.polls += 1
            return int(self.polls == self.cancel_at)
        return super().bdos(fn, de)

    def actual(self, fn, de):
        if fn == 19:
            key = self.fcbkey(de)
            assert key in self.owned, ('foreign erase', key)
            self.mutations.append(('erase', key))
            self.files.pop(key, None)
            return 0
        source_key = self.fcbkey(de) if fn in (22, 23) else None
        target_key = self.fcbkey(de, 16) if fn == 23 else None
        result = super().actual(fn, de)
        if fn == 22 and result != 255:
            self.owned.add(source_key)
        if fn == 23 and result != 255 and source_key in self.owned:
            self.owned.discard(source_key)
            self.owned.add(target_key)
        return result

    def begin(self):
        self.mem[:] = bytes([0xa5])*65536
        self.mem[0x100:0x100+len(self.image)] = self.image
        self.mem[5] = 0xc9
        self.files, self.opened, self.calls = {}, {}, {}
        self.inode = 1
        self.user, self.drive, self.dma = 7, 1, 0x80
        self.failures, self.observer = {}, None
        self.events, self.mutations, self.exception = [], [], None
        self.matches, self.owned = [], set()
        self.polls, self.cancel_at = 0, 0
        self.invoke('TW_INIT')
        self.descriptor(self.address('TW_AREA'), (1, 31, 'IGNORED.TMP'))
        at = self.address('TW_POLL_PTR')
        self.mem[at:at+2] = self.address('TP_POLL').to_bytes(2, 'little')

    def invoke(self, entry):
        self.reg['SP'].value = self.symbols['UC_STACK_TOP']
        protected = bytes(self.mem[self.end:0xfffe])
        result = self.lib.test_run(self.address(entry), getattr(self,'instruction_budget',1000000000))
        assert self.exception is None, self.exception
        assert result >= 0, (entry, result, hex(self.reg['PC'].value))
        assert self.reg['SP'].value == self.symbols['UC_STACK_TOP']
        assert bytes(self.mem[self.end:0xfffe]) == protected
        failed = self.reg['F'].value & 1
        if not failed and self.mem[self.address('TW_OWN')]:
            self.owned.add(self.fcbkey_with_user(self.address('TW_DOC')))
        return failed

    def fcbkey_with_user(self, address):
        user = self.user
        self.user = self.mem[address+36]
        key = self.fcbkey(address)
        self.user = user
        return key

    def workspace(self):
        key = self.fcbkey_with_user(self.address('TW_DOC'))
        raw = self.files[key].data
        header, data = raw[:128], raw[128:]
        assert header[:8] == b'BCTED001'
        assert zlib.crc32(header[:124]) == int.from_bytes(header[124:], 'little')
        assert zlib.crc32(data) == int.from_bytes(header[8:12], 'little')
        assert len(data) == int.from_bytes(header[15:17], 'little')*128
        return key, header, data

    def load(self, data, key=(2, 16, 'SOURCE.TXT')):
        self.add(key, data)
        self.descriptor(self.address('TW_INPUT'), key)
        return self.invoke('TW_LOAD')

    def save(self, key=(16, 7, 'OUTPUT.TXT')):
        self.descriptor(self.address('TS_TARGET'), key)
        self.mem[self.address('TS_REPLACE')] = 1
        self.mem[self.address('TS_PROTECT')] = 1
        return self.invoke('TW_SAVE')

    def segments(self, entries):
        assert len(entries) <= 8
        self.mem[self.address('TW_SEGCOUNT')] = len(entries)
        at = self.address('TW_SEGMENTS')
        for kind, offset, count in entries:
            self.mem[at:at+7] = bytes([kind])+offset.to_bytes(3, 'little')+count.to_bytes(3, 'little')
            at += 7

    def edit(self, begin, end, inserted=b''):
        assert len(inserted) <= 255
        at = self.address('TW_META')+12
        length = int.from_bytes(bytes(self.mem[at:at+3]), 'little')
        self.mem[self.address('TW_INSERT'):self.address('TW_INSERT')+len(inserted)] = inserted
        self.segments([(1, 0, begin), (2, 0, len(inserted)), (1, end, length-end)])
        return self.invoke('TW_EDIT')


def padded(data):
    return data+b'\x1a'*(-len(data) % 128)


def tests(m):
    cases = []
    for data in (b'', b'\x1a'*384, b'X'*128, b'Y'*256,
                 padded(b' \tMixed  \r\nlast\n\rTail \t  ')+b'\x1a'*256,
                 padded(b'X'*127), padded(b'X'*129), padded(b'Z'*4095)):
        m.begin()
        assert m.load(data) == 0
        _, _, actual = m.workspace()
        assert actual == data
        assert m.save() == 0
        assert m.files[(16, 7, 'OUTPUT.TXT')].data == data
        cases.append('exact no-edit '+str(len(data)))
    m.begin()
    initial = b'one\t  \r\nTWO\nthree\rlast  '
    assert m.load(padded(initial)) == 0
    old_key, _, _ = m.workspace()
    assert m.edit(3, 3, b'\t ') == 0
    current = initial[:3]+b'\t '+initial[3:]
    assert m.workspace()[2] == padded(current)
    assert old_key not in m.files
    assert m.save() == 0
    assert m.files[(16, 7, 'OUTPUT.TXT')].data == padded(current)
    assert m.edit(0, 3, b'REPLACE') == 0
    current = b'REPLACE'+current[3:]
    assert m.workspace()[2] == padded(current)
    cases.append('insert/delete literal tabs, spaces and mixed terminators')
    before = m.workspace()
    before_name = bytes(m.mem[m.address('TW_META'):m.address('TW_META')+128])
    assert m.load(padded(b'A'*4096), (2, 31, 'TOOLONG.TXT')) != 0
    assert m.workspace() == before
    assert bytes(m.mem[m.address('TW_META'):m.address('TW_META')+128]) == before_name
    assert m.edit(0, 0, b'!') == 0
    assert m.fcbkey_with_user(m.address('TW_META')+22) == (16, 7, 'OUTPUT.TXT')
    cases.append('rejected load preserves document and Save As identity')
    for inserted in (b'\0', b'\x80', b'A'*255):
        m.begin()
        assert m.load(padded(b'x'*4095)) == 0
        before = m.workspace()
        assert m.edit(0, 0, inserted) != 0
        assert m.workspace() == before
        cases.append('rejected edit '+str(inserted[:1]))
    for fn in (16, 20, 21, 22, 23, 30, 33):
        for after in (False, True):
            m.begin()
            assert m.load(padded(initial)) == 0
            before = m.workspace()
            m.calls = {}
            m.failures = {fn: (1, after)}
            failed = m.edit(0, 0, b'!')
            if failed:
                assert m.workspace() == before, (fn, after)
                m.failures = {}
                assert m.save() == 0, ('save after failed edit', fn, after)
            else:
                assert m.workspace()[2] == padded(b'!'+initial)
            cases.append(f'workspace fault {fn}/{after}: {failed}')
    m.begin()
    assert m.load(padded(initial)) == 0
    assert m.edit(0, 0, b'recovered\t  ') == 0
    checkpoint = m.files[m.workspace()[0]].data
    recovery = (2, 31, 'TEW00999.$$$')
    m.begin()
    m.add(recovery, checkpoint)
    m.descriptor(m.address('TW_INPUT'), recovery)
    assert m.invoke('TW_RECOVER') == 0
    assert m.workspace()[2] == checkpoint[128:]
    assert m.files[recovery].data == checkpoint
    assert m.workspace()[1][21] == 1
    assert m.save() == 0
    assert m.files[(16, 7, 'OUTPUT.TXT')].data == checkpoint[128:]
    cases.append('verified recovery creates fresh ownership and retains original checkpoint')
    for offset in (0, 8, 12, 15, 17, 20, 21, 22, 59, 124, 128, len(checkpoint)-1):
        m.begin()
        assert m.load(padded(b'CURRENT')) == 0
        current = m.workspace()
        damaged = bytearray(checkpoint)
        damaged[offset] ^= 0x80
        if offset < 124:
            damaged[124:128] = zlib.crc32(damaged[:124]).to_bytes(4, 'little')
        m.add(recovery, bytes(damaged))
        m.descriptor(m.address('TW_INPUT'), recovery)
        assert m.invoke('TW_RECOVER') != 0, offset
        assert m.workspace() == current
        assert m.files[recovery].data == damaged
        cases.append('recovery rejects corrupt field '+str(offset))
    # More than twice either platform's unloaded 53 KiB TPA. It must remain
    # editable using the one 512-byte source cache and bounded output buffers.
    m.begin()
    large = b''.join((f'{i:04d} '+'abcdefghij'*7+'TAIL!\r\n').encode() for i in range(1500))
    assert len(large) > 2*53*1024
    assert m.load(padded(large)) == 0
    assert m.edit(511, 513, b'\t  ') == 0
    result = large[:511]+b'\t  '+large[513:]
    assert m.workspace()[2] == padded(result)
    assert m.save() == 0
    assert m.files[(16, 7, 'OUTPUT.TXT')].data == padded(result)
    cases.append('larger than twice maximum platform TPA; cache-boundary edit/save')
    m.begin()
    m.instruction_budget=2000000000
    limit=(b'A'*127+b'\n')*8191
    assert m.load(limit)==0
    before=m.workspace()
    assert before[2]==limit
    assert m.load(limit+b'B'*127+b'\n',(2,31,'OVER.TXT'))!=0
    assert m.workspace()==before
    cases.append('8191-record maximum accepted; 8192-record source refused without replacing document')
    return cases


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    p.add_argument('--z80pack', type=Path, default=Path.home()/'projects/git/z80pack')
    a = p.parse_args()
    with tempfile.TemporaryDirectory(prefix='ted-workspace-') as directory:
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
        m = Workspace(C.CDLL(str(work/'core.so')), image, (work/'probe.lst').read_text(), mapping)
        results = tests(m)
        report = {'status': 'PASS', 'scope': 'compiled workspace and file publication; editor UI not asserted',
                  'cases': len(results), 'probe_sha256': hashlib.sha256(image).hexdigest(), 'results': results}
        if a.output:
            a.output.parent.mkdir(parents=True, exist_ok=True)
            a.output.write_text(json.dumps(report, indent=2)+'\n')
        print('PASS', len(results), 'compiled workspace cases')


if __name__ == '__main__':
    main()
