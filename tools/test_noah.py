#!/usr/bin/env python3
"""Execute NOAH's read-only foundation and CP/M adapter on the full Z80 core."""
import argparse
import ctypes as C
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from build_noah import build, version_text
from test_lbr import archive, entry, with_crcs
from test_usq import SHIM
from test_usq_com import Command, diskkey, padded


class Noah(Command):
    def __init__(self, library, image, listing):
        self.lib, self.image = library, image
        self.overlay = getattr(image, "overlay", None)
        self.mem = (C.c_ubyte * 65536).in_dll(library, 'memory')
        self.reg = {}
        for name in ('A', 'B', 'C', 'D', 'E', 'H', 'L', 'A_', 'B_', 'C_', 'D_', 'E_', 'H_', 'L_'):
            self.reg[name] = C.c_ubyte.in_dll(library, name)
        for name in ('IX', 'IY', 'SP', 'PC'):
            self.reg[name] = C.c_ushort.in_dll(library, name)
        for name in ('F', 'F_'):
            self.reg[name] = C.c_int.in_dll(library, name)
        self.symbols = {}
        for old, name in (('UC_OLDSP', 'NH_OLDSP'), ('UC_STACK', 'NH_STACK'),
                          ('UC_STACK_TOP', 'NH_STACK_TOP'), ('UC_INPUT', 'NH_ADAPTER')):
            match = re.search(rf'^([0-9a-f]{{4}}).*\b{name}:\s', listing, re.M | re.I)
            assert match, name
            self.symbols[old] = int(match[1], 16)
        for name in ('AC_OPEN', 'AC_CLOSE', 'LBR_NEXT', 'LBR_READ', 'NH_CONTEXT', 'NX_TEMP', 'NX_VERIFY', 'NI_WAIT', 'NS_YES', 'NW_MEMORY_TEXT', 'NX_BUFFER', 'NR_FCB', 'NR_INPUT', 'NW_SOURCE'):
            match = re.search(rf'\b{name}[ \t]+([0-9a-f]{{4}})\b', listing, re.I)
            assert match, name
            self.symbols[name] = int(match[1], 16)
        self.hook = C.CFUNCTYPE(None, C.c_int)(self.callback)
        library.set_hooks.argtypes = [C.c_ushort, C.c_ushort, C.CFUNCTYPE(None, C.c_int)]
        library.test_run.argtypes = [C.c_ushort, C.c_int]
        library.test_run.restype = C.c_int
        self.cases = 0
        self.max_stack = 0

    def run(self, *args, **kwargs):
        supply=kwargs.pop('supply_overlay',True)
        self.overlay_change_at=kwargs.pop('overlay_change_at',None)
        self.overlay_opens=0
        self.source_change=kwargs.pop('source_change',None)
        self.writer_change=kwargs.pop('writer_change',None)
        self.source_opens=0
        self.cancel_poll = kwargs.pop('cancel_poll', None)
        self.tamper = kwargs.pop('tamper', False)
        self.polls = 0
        self.keys = list(kwargs.pop('keys', '').encode('ascii'))
        self.attrs = dict(kwargs.pop('attributes', {}))
        self.extent_attrs = dict(kwargs.pop('extent_attributes', {}))
        self.answers = []
        self.search_items = []
        self.search_cursor = 0
        self.partial_attributes = kwargs.pop('partial_attributes', False)
        self.rename_moves_on_failure = kwargs.pop('rename_moves_on_failure', False)
        self.delete_removes_on_failure = kwargs.pop('delete_removes_on_failure', False)
        kwargs.setdefault('tpa', 0xd501)
        self.write_allowed = bool(args and any(t.upper() in ('/X', '/EXTRACT', '/ADD', '/REMOVE', '/COMPACT', '/SQ', '/CR', '/EXPAND') for t in args[0].split()))
        injected=None
        if self.overlay is not None and supply:
            files = dict(args[1])
            drive = kwargs.get('drive',1); user=kwargs.get('user',0)
            injected=diskkey(drive,'NOAH.OVL',user)
            if injected in files: injected=None
            else: files[diskkey(drive,'NOAH.OVL',user)]=self.overlay
            args = (args[0],files)+args[2:]
        try:
            result = super().run(*args, **kwargs)
        except AssertionError as error:
            raise AssertionError((args[0], str(error))) from error
        if injected:
            self.files.pop(injected,None);self.original.pop(injected,None)
        self.overlay_events=[(f,d) for f,d in self.events if d==self.symbols['NR_FCB'] and f in (15,16,20)]
        self.events=[(f,d) for f,d in self.events if (f,d) not in self.overlay_events]
        if self.overlay_events and 'operation stopped' not in result and 'Insufficient transient' not in result:
            at=self.image.window
            assert bytes(self.mem[at:at+len(self.image.controller)])==self.image.controller, 'controller not restored'
        ceiling=kwargs.get('tpa',0xd501)
        assert not any(self.mem[ceiling:0xd800]), 'write above active TPA'
        minimum = C.c_ushort.in_dll(self.lib, 'minimum_sp').value
        self.max_stack = max(self.max_stack, self.symbols['UC_STACK_TOP'] - minimum)
        assert self.max_stack < 384, 'stack overlaps version-tail scratch'
        return result

    def callback(self, kind):
        # The pre-stack low-TPA diagnostic deliberately uses the CCP stack.
        de = self.reg['D'].value * 256 + self.reg['E'].value
        if kind == 0 and self.reg['PC'].value == 5 and self.reg['C'].value == 9 and de == self.symbols['NW_MEMORY_TEXT']:
            try:
                assert self.reg['SP'].value == 0xdffe
                self.reg['A'].value = self.bdos(9,de)
            except BaseException as error:
                self.exception = error
            return
        return super().callback(kind)

    def fail(self, operation):
        self.attempts[operation] = self.attempts.get(operation, 0) + 1
        choice = self.failures.get(operation)
        if isinstance(choice, (tuple, list, set)):
            return self.attempts[operation] in choice
        return choice is not None and (choice == 0 or self.attempts[operation] == choice)

    def bdos(self, fn, de):
        if fn==15 and de==self.symbols['NR_INPUT']:
            self.source_opens+=1
            if self.source_change and self.source_opens==self.source_change[1]:
                self.files[self.source_change[0]]=self.source_change[2]
        if fn==15 and de==self.symbols['NW_SOURCE'] and self.writer_change:
            self.files[self.writer_change[0]]=self.writer_change[1]
            self.writer_change=None
        if fn==16 and de in (self.symbols['NR_INPUT'],self.symbols['NW_SOURCE']):
            if self.fail('source_close'):
                self.events.append((fn,de))
                return 255
        if de==self.symbols['NR_FCB'] and fn in (15,16,20):
            if fn==15:
                self.overlay_opens+=1
                if self.overlay_opens==self.overlay_change_at:
                    key=self.fcbkey(de)
                    if key in self.files:
                        raw=bytearray(self.files[key]);raw[-8]^=1;self.files[key]=bytes(raw)
            failures,attempts=self.failures,self.attempts
            self.failures={};self.attempts={}
            try: return super().bdos(fn,de)
            finally: self.failures,self.attempts=failures,attempts
        writes = (19, 21, 22, 23, 34)
        assert self.write_allowed or fn not in writes, ('not a read-only operation', fn)
        assert fn in (2, 6, 9, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 25, 26, 30, 32, 33, 34, 35), fn
        if fn == 14:
            self.events.append((fn, de))
            self.drive = (de & 255) + 1
            return 0
        if fn == 32:
            self.events.append((fn, de))
            previous = self.user
            if de & 255 != 255:
                assert de & 255 < 32
                self.user = de & 255
            return previous
        if fn in (17, 18):
            self.events.append((fn, de))
            if fn == 17:
                key = self.fcbkey(de)
                self.searches[key] = self.searches.get(key, 0) + 1
                if self.late_existing and key == self.late_existing[0] and self.searches[key] == 2:
                    self.files[key] = self.late_existing[1]
                drive = self.mem[de] or self.drive
                pattern = bytes(b & 127 for b in self.mem[de + 1:de + 12])
                self.search_items = []
                for identity, content in self.files.items():
                    d, u, name = identity
                    base, dot, ext = name.partition('.')
                    canonical = (base.ljust(8) + ext.ljust(3)).encode('ascii')
                    if d != drive or u != self.user or not all(p == 63 or p == c for p, c in zip(pattern, canonical)):
                        continue
                    records = len(padded(content)) // 128
                    for extent in range(max(1, (records + 127) // 128)):
                        item = bytearray(32)
                        item[0] = u
                        item[1:12] = canonical
                        mask = self.extent_attrs.get(identity, {}).get(extent, self.attrs.get(identity, 0))
                        for bit in range(3):
                            if mask & (1 << bit): item[9 + bit] |= 128
                        item[12] = extent & 31
                        item[14] = extent >> 5
                        item[15] = max(0, min(128, records - extent * 128))
                        self.search_items.append(bytes(item))
                self.search_items.reverse()  # Physical order is deliberately not lexical.
                self.search_cursor = 0
            if self.search_cursor == len(self.search_items):
                return 255
            item = self.search_items[self.search_cursor]
            slot = self.search_cursor % 4
            self.search_cursor += 1
            self.mem[self.dma:self.dma + 128] = bytes([0xE5]) * 128
            self.mem[self.dma + slot * 32:self.dma + slot * 32 + 32] = item
            return slot
        if fn == 30:
            self.events.append((fn, de))
            key = self.fcbkey(de)
            mask = sum((1 << bit) for bit in range(3) if self.mem[de + 9 + bit] & 128)
            failed = self.fail('attributes')
            if not failed or self.partial_attributes:
                assert key in self.files
                self.attrs[key] = mask
                self.extent_attrs.pop(key, None)
            return 255 if failed else 2
        if fn == 23:
            self.events.append((fn, de))
            old, new = self.fcbkey(de), self.fcbkey(de, 16)
            if self.attrs.get(old, 0) & 1:
                return 255
            failed = self.fail('rename')
            if failed and not self.rename_moves_on_failure:
                return 255
            self.files[new] = self.files.pop(old)
            self.attrs[new] = self.attrs.pop(old, 0)
            self.renamed.append((old, new))
            return 255 if failed else 3
        if fn == 19 and self.delete_removes_on_failure:
            self.events.append((fn, de))
            key = self.fcbkey(de)
            failed = self.fail('delete')
            self.files.pop(key, None)
            self.attrs.pop(key, None)
            self.deleted.append(key)
            return 255 if failed else 0
        if fn == 19 and self.attrs.get(self.fcbkey(de), 0) & 1:
            return 255
        if fn == 6:
            self.events.append((fn, de))
            if self.mem[self.symbols['NI_WAIT']]:
                assert not self.mem[self.symbols['NS_YES']], '/Y waited for input'
                key = self.keys.pop(0) if self.keys else 13
                self.answers.append(key)
                return key
            self.polls += 1
            return 3 if self.polls == self.cancel_poll else 0
        if fn == 20 and self.fail('verify_read'):
            self.events.append((fn, de))
            return 2
        if fn == 15 and de == self.symbols['NX_VERIFY'] and self.tamper:
            key = self.fcbkey(de)
            if key in self.files and self.files[key]:
                if self.tamper == 'append':
                    self.files[key] += bytes(128)
                elif self.tamper == 'truncate':
                    self.files[key] = self.files[key][:-128]
                else:
                    self.files[key] = bytes([self.files[key][0] ^ 1]) + self.files[key][1:]
            self.tamper = False
        if fn == 2:
            self.events.append((fn, de))
            self.console += chr(de & 255)
            return de & 255
        if fn == 35:
            self.events.append((fn, de))
            if self.fail('size'):
                return 255
            data = padded(self.files[self.fcbkey(de)])
            self.mem[de + 33:de + 36] = (len(data) // 128).to_bytes(3, 'little')
            return 255  # DRI function 35 has no defined accumulator result.
        if fn == 34:
            self.events.append((fn, de))
            assert de in self.opened
            key = self.fcbkey(de)
            record = int.from_bytes(bytes(self.mem[de + 33:de + 36]), 'little')
            at = record * 128
            data = bytearray(padded(self.files[key]))
            assert at <= len(data), ('random write hole', record, len(data))
            failed = self.fail('write')
            count = 17 if failed else 128
            data[at:at + count] = bytes(self.mem[self.dma:self.dma + count])
            self.files[key] = bytes(data)
            return 2 if failed else 0
        if fn == 33:
            self.events.append((fn, de))
            if self.fail('read'):
                return 2
            assert de in self.opened
            record = int.from_bytes(bytes(self.mem[de + 33:de + 36]), 'little')
            data = padded(self.files[self.fcbkey(de)])
            offset = record * 128
            if offset >= len(data):
                return 1
            self.mem[self.dma:self.dma + 128] = data[offset:offset + 128]
            return 0
        return super().bdos(fn, de)

    def library_call(self, name, count=0, output=None):
        if output is None: output=self.symbols["NX_BUFFER"]
        self.reg['IX'].value = self.symbols['NH_CONTEXT']
        self.reg['SP'].value = self.symbols['UC_STACK_TOP']
        self.reg['B'].value, self.reg['C'].value = count >> 8, count & 255
        self.reg['D'].value, self.reg['E'].value = output >> 8, output & 255
        before = self.reg['IX'].value, self.reg['IY'].value, self.reg['SP'].value
        steps = self.lib.test_run(self.symbols[name], 4000000)
        assert steps >= 0, (name, steps)
        assert self.exception is None, self.exception
        assert before == (self.reg['IX'].value, self.reg['IY'].value, self.reg['SP'].value), (name, before, self.reg['IX'].value, self.reg['IY'].value, self.reg['SP'].value)
        return self.reg['A'].value if self.reg['F'].value & 1 else 0


def tests(m):
    raw = archive([entry(b'README  TXT', pad=3), entry(b'EMPTY      ', records=0)], b'A' * 125 + b'\x1a' * 3)
    source = diskkey(2, 'TEXTS.LBR', 7)
    for tail in ('B:TEXTS.LBR', '/LIST B:TEXTS.LBR', '/list b:texts.lbr', '\t/list\tB:TEXTS.LBR\t'):
        output = m.run(tail, {source: raw}, user=7)
        assert 'README   TXT 0000007D bytes' in output, output
        assert 'EMPTY        00000000 bytes' in output, output
        assert 'Listing complete' in output
        assert not m.opened
        assert m.drive == 1 and m.user == 7
        assert not m.created and not m.deleted and not m.renamed
        m.intact()
    # Exercise actual wrapper member reads across DMA records and at a short
    # final sector; the listing command itself only reads directory entries.
    data = bytes(range(256)) * 3
    raw_member = archive([entry(start=511, records=6, pad=17)], bytes(510 * 128) + data)
    m.run('DATA.LBR', {diskkey(1, 'DATA.LBR'): raw_member})
    assert m.library_call('AC_OPEN') == 0
    assert m.library_call('AC_OPEN') == 6  # Do not lose an already-open FCB.
    assert m.library_call('LBR_NEXT') == 0
    result = bytearray()
    while True:
        status = m.library_call('LBR_READ', 195)
        if status:
            assert status == 1
            break
        count = m.reg['B'].value * 256 + m.reg['C'].value
        assert 0 < count <= 195
        result.extend(m.mem[m.symbols["NX_BUFFER"]:m.symbols["NX_BUFFER"] + count])
    assert result == data[:-17]
    assert m.library_call('AC_CLOSE') == 0 and not m.opened
    m.intact()
    # Filename extension is not used for LBR recognition.
    assert 'Listing complete' in m.run('ODD.BIN', {diskkey(1, 'ODD.BIN'): raw})
    for tail in ('/VER', ' /ver  ', '\t/VER\t', ' ' * 123 + '/VER', '/VER' + ' ' * 123):
        assert m.run(tail, {}) == version_text(), (tail, repr(m.console), repr(version_text()))
        assert [f for f, _ in m.events] == [9]
    for tail in ('/VER FILE', 'FILE /VER', '/VER /VER', 'FILE\t/ver', '/VER /UNKNOWN'):
        assert m.run(tail, {}) == version_text()
        assert [f for f, _ in m.events] == [9]
    help_output = m.run('/HELP', {})
    assert 'LBR development build' in help_output
    for tail in ('/HELP', '/HELP X', 'X /help', '/HELP /HELP', '/VER /HELP',
                 '/HELP /VER', 'FILE\t/HeLp\t/UNKNOWN', ' ' * 122 + '/HELP'):
        assert m.run(tail, {}) == help_output, tail
        assert [f for f, _ in m.events] == [9]
        m.intact()
    for tail in ('', '/LIST', 'ABC.LONG', '.LBR', 'TOOLONG99.LBR',
                 'A..LBR', 'A/B.LBR', '/VERBOSE', 'Q:TEXTS.LBR', '/L', '/LISTX',
                 '/HEL', '/HELPX', '/HELP\0', 'X' * 127, '/TEST FILE C:',
                 '/EXTRACT FILE C: EXTRA',  '/X FILE Q:'):
        assert 'Usage:' in m.run(tail, {source: raw}), tail
        assert not any(fn in (15, 33, 35) for fn, _ in m.events)
        m.intact()
    assert 'No archives matched' in m.run('MISSING.LBR', {})
    assert 'error' in m.run('BAD.ARK', {diskkey(1, 'BAD.ARK'): b'\x1a\x02invalid ARK'})
    for failure in ('open', 'size', 'read', 'close_input'):
        output = m.run('B:TEXTS.LBR', {source: raw}, user=7, failures={failure: 1})
        assert 'error' in output.lower() or 'failed' in output.lower(), (failure, output)
        assert 'Listing complete' not in output
        if failure != 'close_input':
            assert not m.opened
        m.intact()
    # Partial enumeration must not be called complete when a later entry fails.
    damaged = archive([entry(records=0), entry(start=100)], b'')
    output = m.run('BAD.LBR', {diskkey(1, 'BAD.LBR'): damaged})
    assert 'FILE     BIN' in output and 'error' in output
    assert 'Listing complete' not in output
    m.intact()


def extraction_tests(m):
    source = diskkey(2, 'TEXTS.LBR', 7)
    payload = bytes(range(128)) + b'Y' * 128
    raw = with_crcs(archive([entry(b'README  TXT', 1, 1, 3),
                            entry(b'EMPTY      ', records=0),
                            entry(b'BINARY  BIN', 2, 1)], payload))
    for tail in ('/TEST B:TEXTS.LBR', '/T B:TEXTS.LBR'):
        output = m.run(tail, {source: raw}, user=7)
        assert 'Structure/selected readability checked' in output, output
        assert 'verified (hex): 00000003; unavailable/ambiguous: 00000001' in output
        assert not m.created and not m.deleted and not m.renamed
        m.intact()
    for tail in ('/EXTRACT B:TEXTS.LBR C:', '/X B:TEXTS.LBR C:', '/x b:texts.lbr c:'):
        output = m.run(tail, {source: raw}, user=7)
        assert m.files[diskkey(3, 'README.TXT', 7)] == payload[:125] + b'\x1a' * 3
        assert m.files[diskkey(3, 'EMPTY', 7)] == b''
        assert m.files[diskkey(3, 'BINARY.BIN', 7)] == b'Y' * 128
        assert 'Extracted (hex): 00000003; skipped: 00000000; failed: 00000000' in output
        assert 'Unprocessed (hex): 00000000' in output and not m.opened
        assert all(not k[2].endswith(('.TMP', '.BAK')) for k in m.files)
        m.intact()
    # Default destination is logged drive, NOT the archive drive.
    m.run('/X B:TEXTS.LBR', {source: raw}, drive=1, user=7)
    assert diskkey(1, 'README.TXT', 7) in m.files and diskkey(2, 'README.TXT', 7) not in m.files
    # Existing destinations, including the archive itself, are never replaced.
    existing = diskkey(1, 'README.TXT', 7)
    output = m.run('/X B:TEXTS.LBR', {source: raw, existing: b'KEEP ORIGINAL'}, user=7)
    assert 'A7:README.TXT: replacement declined; skipped.' in output, output
    assert 'skipped: 00000001' in output
    m.intact()
    same = with_crcs(archive([entry(b'TEXTS   LBR')], bytes(128)))
    output = m.run('/X B:TEXTS.LBR B:', {source: same}, user=7)
    assert 'selected input archive; skipped' in output and not m.created
    m.intact()
    # Recovery namespace respects both TMP and BAK, and can never equal final.
    single = with_crcs(archive([entry(b'README  TXT')], bytes(range(128))))
    keep = {diskkey(1, 'README00.TMP', 7): b'KEEP TEMP',
            diskkey(1, 'README01.BAK', 7): b'KEEP BACKUP'}
    m.run('/X B:TEXTS.LBR', {source: single, **keep}, user=7)
    assert m.created == [diskkey(1, 'README02.TMP', 7)]
    m.intact()
    for ext in (b'TMP', b'BAK'):
        special = with_crcs(archive([entry(b'BETTRC00' + ext)], bytes(128)))
        m.run('/X B:TEXTS.LBR', {source: special}, user=7)
        assert m.created == [diskkey(1, 'BETTRC01.TMP', 7)]
        m.intact()
    full = {diskkey(1, f'README{i:02}.BAK', 7): b'KEEP' for i in range(100)}
    output = m.run('/X B:TEXTS.LBR', {source: single, **full}, user=7)
    assert 'failed: 00000001' in output and not m.created
    m.intact()
    # Corrupt/unsafe archives must fail before any output MAKE.
    duplicate = with_crcs(archive([entry(records=0), entry(records=0)]))
    overlap = with_crcs(archive([entry(), entry(b'TWO     BIN')], bytes(128)))
    damaged = bytearray(single)
    damaged[-1] ^= 1
    for invalid in (duplicate, overlap, bytes(damaged)):
        output = m.run('/X B:TEXTS.LBR', {source: invalid}, user=7)
        assert 'error' in output and not m.created and not m.renamed
        m.intact()
    # All published outputs have been closed, reopened and compared, including
    # CP/M padding. A corrupt temporary must never be published.
    for tamper in (True, 'append', 'truncate'):
        output = m.run('/X B:TEXTS.LBR', {source: single}, user=7, tamper=tamper)
        assert 'failed: 00000001' in output and not m.renamed
        assert set(m.files) == {source}
        m.intact()
    for failure, nth in (('make', 1), ('write', 1), ('close_output', 1),
                         ('open', 2), ('verify_read', 1)):
        output = m.run('/X B:TEXTS.LBR', {source: single}, user=7, failures={failure: nth})
        assert 'failed: 00000001' in output and not m.renamed, (failure, output)
        assert set(m.files) == {source} and not m.opened, (failure, m.files)
        m.intact()
    # Inject an archive read error specifically AFTER staging has begun.
    m.run('/X B:TEXTS.LBR', {source: single}, user=7)
    make_index = next(i for i, (fn, _) in enumerate(m.events) if fn == 22)
    copy_read = sum(fn == 33 for fn, _ in m.events[:make_index]) + 1
    output = m.run('/X B:TEXTS.LBR', {source: single}, user=7, failures={'read': copy_read})
    assert 'failed: 00000001' in output and set(m.files) == {source} and not m.opened
    m.intact()
    # A publication failure retains a VERIFIED temporary and names it.
    output = m.run('/X B:TEXTS.LBR', {source: single}, user=7, failures={'rename': 1})
    temp = diskkey(1, 'README00.TMP', 7)
    assert 'Temporary retained: A7:README00.TMP' in output and temp in m.files
    assert m.files[temp] == bytes(range(128)) and diskkey(1, 'README.TXT', 7) not in m.files
    m.intact()
    # A target appearing at publication is preserved, along with verified TMP.
    destination = diskkey(1, 'README.TXT', 7)
    output = m.run('/X B:TEXTS.LBR', {source: single}, user=7,
                   late_existing=(destination, b'FOREIGN FILE'))
    assert m.files[destination] == b'FOREIGN FILE' and temp in m.files and not m.renamed
    assert 'Temporary retained:' in output
    m.intact()
    output = m.run('/X B:TEXTS.LBR', {source: single}, user=7,
                   failures={'write': 1, 'delete': 1})
    assert 'Temporary retained:' in output and temp in m.files and not m.renamed
    m.intact()
    # Controlled cancellation during preflight and after MAKE. The latter
    # cleans staging and accounts the current member as unprocessed.
    m.run('/X B:TEXTS.LBR', {source: single}, user=7)
    make_index = next(i for i, (fn, _) in enumerate(m.events) if fn == 22)
    after_make = sum(fn == 6 for fn, _ in m.events[:make_index]) + 1
    for poll in (1, after_make, after_make + 1, after_make + 2):
        output = m.run('/X B:TEXTS.LBR', {source: single}, user=7, cancel_poll=poll)
        assert 'cancelled' in output, (poll, output)
        assert set(m.files) == {source} and not m.opened and not m.renamed, (poll, m.files)
        if poll >= after_make:
            assert 'failed: 00000000' in output and 'Unprocessed (hex): 00000001' in output
        m.intact()
    output = m.run('/TEST B:TEXTS.LBR', {source: single}, user=7, cancel_poll=1)
    assert 'cancelled' in output and 'Structure/selected readability checked' not in output
    # Optional timestamps are not silently claimed restored on CP/M 2.2.
    stamped = bytearray(single)
    stamped[32 + 18] = 1
    output = m.run('/X B:TEXTS.LBR', {source: with_crcs(stamped)}, user=7)
    assert 'Timestamp not restored' in output
    m.intact()


def selector_overwrite_tests(m):
    one = with_crcs(archive([entry(b'README  TXT')], b'R' * 128))
    other = with_crcs(archive([entry(b'README  TXT')], b'S' * 128))
    source = diskkey(2, 'TEXTS.LBR', 7)
    target = diskkey(1, 'README.TXT', 7)
    # Shared DU scope, all users of one drive before next drive, lexical names.
    files = {diskkey(3, 'ZZ.LBR', 1): one, diskkey(2, 'Z.LBR', 2): one,
             diskkey(2, 'A.LBR', 2): one, diskkey(2, 'B.LBR', 1): one,
             diskkey(2, 'IGNORED.BIN', 1): one}
    output = m.run('/LIST [C[1],B[1-2]]:*.LBR README.TXT', files, user=7)
    headings = [line for line in output.splitlines() if line.startswith('Archive ')]
    assert headings == ['Archive B1:B.LBR', 'Archive B2:A.LBR', 'Archive B2:Z.LBR', 'Archive C1:ZZ.LBR'], headings
    assert 'selected 0004; processed 0004; failed 0000' in output
    assert m.user == 7 and m.drive == 1
    m.intact()
    output = m.run('/LIST B[1,1-2]:*.LBR README', files, user=7)
    assert 'No members matched' in output and 'README   TXT' not in output
    assert output.count('Archive ') == 3  # overlapping selectors do not duplicate.
    # Attribute selection is per archive, not a member-name reinterpretation.
    arc = diskkey(2, 'ARC.LBR', 1)
    sys = diskkey(2, 'SYS.LBR', 1)
    plain = diskkey(2, 'PLAIN.LBR', 1)
    output = m.run('B1:*.LBR[$SYS,$ARC] README.*', {arc: one, sys: one, plain: one},
                   attributes={arc: 4, sys: 2})
    assert 'Archive B1:ARC.LBR' in output and 'Archive B1:SYS.LBR' in output
    assert 'PLAIN.LBR' not in output
    m.intact()
    # One logical archive even when it occupies several CP/M extents; an
    # attribute predicate can match a later extent without duplicating it.
    big = one + bytes(17000)
    output = m.run('/LIST B7:TEXTS.LBR[$RO]', {source: big}, user=7,
                   extent_attributes={source: {0: 0, 1: 1}})
    assert output.count('Archive B7:TEXTS.LBR') == 1 and 'Listing complete' in output
    # Cross-user reader ownership: destination has an unrelated same-name file.
    misleading = diskkey(2, 'TEXTS.LBR', 3)
    output = m.run('/X B7:TEXTS.LBR C3:README.*', {source: one, misleading: other}, user=5)
    assert m.files[diskkey(3, 'README.TXT', 3)] == b'R' * 128
    assert m.user == 5 and m.drive == 1 and 'failed: 00000000' in output
    m.intact()
    # Nonselected corrupt payload does not become a selected-file checksum fail;
    # directory structure/overlaps still apply to the whole archive.
    filtered = bytearray(with_crcs(archive([entry(b'README  TXT'), entry(b'BAD     BIN', 2)], b'R'*128+b'B'*128)))
    filtered[-1] ^= 1
    output = m.run('/TEST B7:TEXTS.LBR README.TXT', {source: bytes(filtered)}, user=7)
    assert 'Integrity checks complete' in output and 'error' not in output
    # Y/N/All/Cancel uses shared choice handling and N default.
    for keys in ('Y', 'y', 'zY'):
        output = m.run('/X B7:TEXTS.LBR', {source: one, target: b'OLD'}, user=7, keys=keys)
        assert m.files[target] == b'R' * 128 and m.files[source] == one
        assert not any(k[2].endswith(('.BAK', '.TMP')) for k in m.files)
        assert not m.opened and 'failed: 00000000' in output
        if keys.startswith('z'): assert output.count('Replace? Y/N/A/C [N]:') == 2
    for keys in ('N', '\r', '\x1b', 'C', '\x03'):
        output = m.run('/X B7:TEXTS.LBR', {source: one, target: b'OLD'}, user=7, keys=keys)
        assert m.files[target] == b'OLD' and not m.created and not m.renamed
        if keys not in ('N', '\r'): assert 'cancelled' in output
        m.intact()
    # All persists across archives but never spills into protection approval.
    two = diskkey(2, 'Z.LBR', 7)
    output = m.run('/X B7:*.LBR /R', {source: one, two: other, target: b'OLD'}, user=7, keys='A')
    assert m.files[target] == b'S' * 128 and m.answers == [ord('A')]
    for mask, flags in ((1, '/R'), (2, '/SYS'), (3, '/R /SYS')):
        for keys in ('Y', 'N', '\r'):
            output = m.run(f'/X {flags} B7:TEXTS.LBR', {source: one, target: b'OLD'},
                           user=7, keys=keys, attributes={target: mask | 4})
            assert m.files[target] == (b'R' * 128 if keys == 'Y' else b'OLD'), output
            assert m.attrs[target] & 3 == mask
            assert m.files[source] == one
        output = m.run(f'/X /Y {flags} B7:TEXTS.LBR', {source: one, target: b'OLD'},
                       user=7, attributes={target: mask})
        assert m.files[target] == b'OLD' and not m.answers and not m.created
        assert 'protected; skipped' in output
    output = m.run('/X /Y B7:TEXTS.LBR', {source: one, target: b'OLD'}, user=7)
    assert m.files[target] == b'R' * 128 and not m.answers
    output = m.run('/X B7:TEXTS.LBR', {source: one, target: b'OLD'}, user=7, attributes={target: 1})
    assert 'protected; skipped' in output and not m.answers and not m.created
    # A later protected archive collision asks independently after ordinary All.
    protected = diskkey(1, 'SECOND.TXT', 7)
    mixed = with_crcs(archive([entry(b'README  TXT'), entry(b'SECOND  TXT', 2)], b'R'*128+b'T'*128))
    output = m.run('/X /R B7:TEXTS.LBR', {source: mixed, target: b'OLD', protected: b'KEEP'},
                   user=7, attributes={protected: 1}, keys='AN')
    assert m.answers == [ord('A'), ord('N')]
    assert m.files[target] == b'R'*128 and m.files[protected] == b'KEEP'
    # Any selected input is protected from /Y replacement, even a future input.
    attacker = with_crcs(archive([entry(b'Z       LBR')], bytes(128)))
    output = m.run('/X /Y B7:*.LBR B7:', {source: attacker, two: other}, user=7)
    assert m.files[two] == other and 'selected input archive; skipped' in output
    # Every rollback boundary preserves original bytes and old protection.
    for failure, nth in (('rename', 1), ('rename', 2), ('attributes', 1), ('attributes', 2), ('attributes', 3)):
        output = m.run('/X /R B7:TEXTS.LBR', {source: one, target: b'OLD'}, user=7,
                       keys='Y', attributes={target: 1}, failures={failure: nth}, partial_attributes=True)
        assert m.files[target] == b'OLD', (failure, nth, output, m.files)
        assert m.attrs[target] & 1 and m.files[source] == one
        assert 'failed: 00000001' in output
    # Backup cleanup failure keeps the verified new output, retains the original
    # BAK, restores its protection and reports a warning without rollback.
    output = m.run('/X /R B7:TEXTS.LBR', {source: one, target: b'OLD'}, user=7,
                   keys='Y', attributes={target: 1}, failures={'delete': 1})
    backup = diskkey(1, 'README00.BAK', 7)
    assert m.files[target] == b'R'*128 and m.files[backup] == b'OLD'
    assert m.attrs[target] & 1 and m.attrs[backup] & 1
    assert 'backup cleanup failed' in output and 'Extracted (hex): 00000001' in output
    # Failed rename-back stops the batch and preserves verified TMP plus original
    # BAK, including its RO state. The next archive is never processed.
    output = m.run('/X /R B7:*.LBR', {source: one, two: other, target: b'OLD'},
                   user=7, keys='Y', attributes={target: 1}, failures={'rename': (2, 3)})
    assert 'Recovery required; stop' in output and 'processed 0001' in output
    assert m.files[backup] == b'OLD' and m.attrs[backup] & 1
    assert m.files[diskkey(1, 'README00.TMP', 7)] == b'R'*128
    assert target not in m.files and m.files[source] == one and m.files[two] == other
    # Reported rename failure can still have changed the namespace. Preserve
    # both versions and report uncertain recovery instead of overwriting a name.
    for nth in (1, 2):
        output = m.run('/X /R B7:*.LBR', {source: one, two: other, target: b'OLD'},
                       user=7, keys='Y', attributes={target: 1}, failures={'rename': nth},
                       rename_moves_on_failure=True)
        assert 'Recovery required; stop' in output and 'processed 0001' in output
        assert m.files[backup] == b'OLD' and m.files[source] == one and m.files[two] == other
        if nth == 1:
            assert m.files[diskkey(1, 'README00.TMP', 7)] == b'R'*128
        else:
            assert m.files[target] == b'R'*128 and m.attrs[backup] & 1
            assert diskkey(1, 'README00.TMP', 7) not in m.files
            assert 'Temporary retained:' not in output
    output = m.run('/X B7:*.LBR', {source: one, two: other}, user=7,
                   failures={'rename': 1}, rename_moves_on_failure=True)
    assert 'Recovery required; stop' in output and 'processed 0001' in output
    assert m.files[target] == b'R'*128 and 'Temporary retained:' not in output
    assert 'Original protection may need restoration' not in output
    output = m.run('/X /R B7:TEXTS.LBR', {source: one, target: b'OLD'}, user=7,
                   keys='Y', attributes={target: 1}, failures={'delete': 1},
                   delete_removes_on_failure=True)
    assert 'backup not found' in output and m.files[target] == b'R'*128 and backup not in m.files
    # A created library matching the input wildcard is not added to the frozen
    # selection midway through the command.
    nested = with_crcs(archive([entry(b'NEW     LBR', records=len(one)//128)], one))
    output = m.run('/X /Y A0:*.LBR', {diskkey(1, 'BASE.LBR'): nested})
    assert m.files[diskkey(1, 'NEW.LBR')] == one and output.count('Archive ') == 1
    # Higher BetterCP/M user areas retain full 0..31 identities in parsing,
    # source I/O ownership, destination writes and caller restoration.
    high = diskkey(2, 'HIGH.LBR', 31)
    output = m.run('/X B31:HIGH.LBR C17:', {high: one}, user=2)
    assert m.files[diskkey(3, 'README.TXT', 17)] == b'R'*128
    assert m.user == 2 and m.drive == 1 and 'Archive B31:HIGH.LBR' in output
    mixed_files = {diskkey(1, 'BAD.LBR'): b'not an archive', diskkey(2, 'GOOD.LBR'): one}
    output = m.run('/TEST [A0,B0]:*.LBR', mixed_files, user=7)
    assert 'Archive/read error' in output and 'Integrity checks complete' in output
    assert 'selected 0002; processed 0002; failed 0001' in output
    m.intact()
    # A bounded selection fails as a whole before any archive open or output.
    crowded = {diskkey(2, f'F{i:07d}.LBR', 0): one for i in range(513)}
    m.instruction_budget = 30000000
    output = m.run('/X /Y B0:*.LBR', crowded, user=7)
    del m.instruction_budget
    assert 'exceeds 512' in output and not any(fn == 15 for fn, _ in m.events)
    assert not m.created and not m.renamed and not m.deleted
    assert m.user == 7 and m.drive == 1
    m.intact()
    output = m.run('/X B7:TEXTS.LBR C3:NOFILE.*', {source: one}, user=7)
    assert 'No members matched' in output and not m.created
    m.intact()
    # Syntax, domain and multi-DU destination errors must precede any mutation.
    for tail in ('/X B7:*.LBR [A0,B1]:', '/X E:*.LBR', '/TEST /Y B7:*.LBR',
                 '/X B7:*.LBR README[$RO]', '/X /LIST B7:*.LBR'):
        output = m.run(tail, {source: one, target: b'OLD'}, user=7, keys='Y')
        assert 'Usage:' in output and not m.created and not m.deleted and not m.renamed, (tail, output)
        m.intact()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    p.add_argument('--z80pack', type=Path, default=Path.home() / 'projects/git/z80pack')
    p.add_argument('--cc', default='cc')
    a = p.parse_args()
    core = a.z80pack / 'z80core'
    with tempfile.TemporaryDirectory(prefix='bettercpm-noah-test-') as temp:
        work = Path(temp)
        image = build(a.assembler, work)
        assert build(a.assembler, work / 'repeat') == image
        (work / 'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h', 'simport.h'):
            shutil.copy2(a.z80pack / 'z80sim/srcsim' / name, work / name)
        shim = SHIM.replace('int test_run(', 'WORD minimum_sp;\nint test_run(')
        shim = shim.replace(' PC=address;', ' minimum_sp=SP; PC=address;')
        shim = shim.replace('  if(PC==65535)', '  if(SP<minimum_sp) minimum_sp=SP;\n  if(PC==65535)')
        (work / 'shim.c').write_text(shim)
        subprocess.run([a.cc, '-shared', '-fPIC', '-O2', f'-I{work}', f'-I{core}',
                        str(work / 'shim.c'), str(core / 'simglb.c'),
                        *map(str, sorted(core.glob('simz80*.c'))), '-o', str(work / 'core.so')], check=True)
        m = Noah(C.CDLL(str(work / 'core.so')), image, (work / 'noah.lst').read_text(errors='replace'))
        tests(m)
        extraction_tests(m)
        selector_overwrite_tests(m)
        print(f'PASS: {m.cases} NOAH command/adapter cases; {len(image)} bytes; deterministic build.')
        print(f'Maximum measured command stack: {m.max_stack} bytes (BDOS intercepted).')


if __name__ == '__main__':
    main()
