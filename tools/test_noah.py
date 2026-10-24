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
        for name in ('AC_OPEN', 'AC_CLOSE', 'LBR_NEXT', 'LBR_READ', 'NH_CONTEXT', 'NX_TEMP', 'NX_VERIFY'):
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
        self.cancel_poll = kwargs.pop('cancel_poll', None)
        self.tamper = kwargs.pop('tamper', False)
        self.polls = 0
        self.write_allowed = bool(args and args[0].split() and args[0].split()[0].upper() in ('/X', '/EXTRACT'))
        result = super().run(*args, **kwargs)
        minimum = C.c_ushort.in_dll(self.lib, 'minimum_sp').value
        self.max_stack = max(self.max_stack, self.symbols['UC_STACK_TOP'] - minimum)
        assert self.max_stack < 128, 'stack overlaps version-tail scratch'
        return result

    def bdos(self, fn, de):
        writes = (19, 21, 22, 23)
        assert self.write_allowed or fn not in writes, ('not a read-only operation', fn)
        assert fn in (2, 6, 9, 15, 16, 17, 19, 20, 21, 22, 23, 25, 26, 33, 35), fn
        if fn == 6:
            self.events.append((fn, de))
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

    def library_call(self, name, count=0, output=0x6001):
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
        result.extend(m.mem[0x6001:0x6001 + count])
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
    assert 'LBR reader development build' in help_output
    for tail in ('/HELP', '/HELP X', 'X /help', '/HELP /HELP', '/VER /HELP',
                 '/HELP /VER', 'FILE\t/HeLp\t/UNKNOWN', ' ' * 122 + '/HELP'):
        assert m.run(tail, {}) == help_output, tail
        assert [f for f, _ in m.events] == [9]
        m.intact()
    for tail in ('', '*.LBR', 'B7:TEXTS.LBR',
                 'A:TEXTS.LBR OTHER', '/LIST', 'ABC.LONG', '.LBR', 'TOOLONG99.LBR',
                 'A..LBR', 'A/B.LBR', '/VERBOSE', 'Q:TEXTS.LBR', '/L', '/LISTX',
                 '/HEL', '/HELPX', '/HELP\0', 'X' * 127, '/TEST FILE C:',
                 '/EXTRACT FILE C: EXTRA', '/X FILE B7:', '/X FILE Q:', '/X FILE *.TXT'):
        assert 'Usage:' in m.run(tail, {source: raw}), tail
        assert not any(fn in (15, 33, 35) for fn, _ in m.events)
        m.intact()
    assert 'error' in m.run('MISSING.LBR', {})
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
        assert 'Structure/readability checked' in output, output
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
    assert 'A:README.TXT: exists; skipped.' in output
    assert 'skipped: 00000001' in output
    m.intact()
    same = with_crcs(archive([entry(b'TEXTS   LBR')], bytes(128)))
    output = m.run('/X B:TEXTS.LBR B:', {source: same}, user=7)
    assert 'exists; skipped' in output and not m.created
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
    assert 'Temporary retained: A:README00.TMP' in output and temp in m.files
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
    assert 'cancelled' in output and 'Structure/readability checked' not in output
    # Optional timestamps are not silently claimed restored on CP/M 2.2.
    stamped = bytearray(single)
    stamped[32 + 18] = 1
    output = m.run('/X B:TEXTS.LBR', {source: with_crcs(stamped)}, user=7)
    assert 'Timestamp not restored' in output
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
        print(f'PASS: {m.cases} NOAH command/adapter cases; {len(image)} bytes; deterministic build.')
        print(f'Maximum measured command stack: {m.max_stack} bytes (BDOS intercepted).')


if __name__ == '__main__':
    main()
