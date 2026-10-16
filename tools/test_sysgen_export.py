#!/usr/bin/env python3
"""Execute SYSGEN export with controlled disk/file failures and exact bytes."""
from pathlib import Path
from build_system_package import compose
from startup_record import build as startup_record
from system_layout import LAYOUT
from test_utility_versions import address, runner

ROOT = Path(__file__).resolve().parents[1]


def main():
    image = (ROOT/'build/utilities/SYSGEN.COM').read_bytes()
    listing = (ROOT/'build/utilities/sysgen.lst').read_text()
    a = lambda name: address(listing, name)
    package, _ = compose()
    payload = bytearray(package[128:])
    payload[128:384] = startup_record('VER /BANNER', system_base=LAYOUT['SYSTEM'])
    expected = package[:128]+payload
    # The payload buffer ends at 9000h. Reject lower TPA before initialization;
    # the boundary itself must permit entering INIT.
    for boundary, allowed in ((0x8fff, False), (0x9000, True)):
        c = runner(image)
        c.mem[6:8] = boundary.to_bytes(2, 'little')
        c.mem[a('INIT'):a('INIT')+4] = bytes((0xdb, 243, 0xc3, 0xff))
        c.mem[a('INIT')+4] = 0xff
        c.mem[5:8] = bytes((0xc3, boundary & 255, boundary >> 8))
        c.mem[boundary:boundary+3] = bytes((0xdb, 244, 0xc9))
        entered = []
        text = []
        def guarded_io(port):
            if port & 255 == 243: entered.append(True);return 0
            assert c.c == 2
            text.append(chr(c.e));return 0
        c.port_read = guarded_io
        c.run(256, limit=100000)
        assert bool(entered) == allowed
        if not allowed: assert '36K' in ''.join(text)
    # Keep these fixtures independent of any user's real filesystem/media.
    cases = ['new', 'new-default', 'replace', 'decline', 'temp-exists', 'backup-exists',
             'protected-ro', 'protected-sys', 'read', 'create', 'write',
             'close', 'verify', 'delete', 'rename-old', 'rename-new',
             'final-verify', 'backup-delete', 'partial-old', 'partial-new', 'abort', 'bad-descriptor',
             'bad-pointer', 'geometry']
    for fault in cases:
        c = runner(image)
        c.mem[5:8] = bytes((0xdb, 244, 0xc9))
        c.mem[a('DISKIO'):a('DISKIO')+4] = bytes((0xdb, 245, 0xb7, 0xc9))
        c.mem[a('SOURCE'):a('SOURCE')+64] = package[16:80]
        c.mem[a('XARG2'):a('XARG2')+12] = b'\x02BACKUP  SYS'
        c.mem[a('SOURCEDEV')] = 0
        files = {}
        attrs = {}
        target = 'SYSTEM.SYS' if fault == 'new-default' else 'BACKUP.SYS'
        if fault == 'new-default':
            c.mem[a('XARG2'):a('XARG2')+12] = b'\x00SYSTEM  SYS'
        old = b'old package'.ljust(256, b'!')
        if fault in ('replace', 'decline', 'protected-ro', 'protected-sys',
                     'rename-old', 'rename-new', 'final-verify', 'backup-delete', 'partial-old', 'partial-new'):
            files[target] = bytearray(old)
        if fault == 'temp-exists': files['SYSGEN.$$$'] = bytearray(b'recovery')
        if fault == 'backup-exists': files['SYSGEN.BAK'] = bytearray(b'recovery')
        if fault == 'protected-ro': attrs[target] = (128, 0)
        if fault == 'protected-sys': attrs[target] = (0, 128)
        original_files = {n: bytes(b) for n, b in files.items()}
        disk = bytearray(payload)
        if fault == 'bad-descriptor':
            at = disk.index(b'BDCF\x05\x04\x04\x40')
            disk[at+4] = 99
        if fault == 'bad-pointer':
            at = disk.index(b'BDCF\x05\x04\x04\x40')
            disk[at+10:at+12] = b'\xff\xff'
        if fault == 'geometry': c.mem[a('SOURCE')+17] ^= 1
        before_disk = bytes(disk)
        dma = 128
        cursors = {}
        writes = 0
        renames = 0
        opened_final = False
        console = []
        reads = []
        def name(pointer):
            stem = bytes(x & 127 for x in c.mem[pointer+1:pointer+9]).decode().rstrip()
            ext = bytes(x & 127 for x in c.mem[pointer+9:pointer+12]).decode().rstrip()
            return stem+('.'+ext if ext else '')
        def io(port):
            nonlocal dma, writes, renames, opened_final
            if port & 255 == 245:
                assert c.a == 0, 'export attempted a protected-sector write'
                record = c.hl
                reads.append(record)
                if fault == 'read' and record == 7: return 1
                c.mem[c.de:c.de+128] = disk[record*128:(record+1)*128]
                return 0
            assert port & 255 == 244
            service, ptr = c.c, c.de
            if service == 2:
                console.append(chr(c.e));return 0
            if service == 6:
                if fault == 'abort' and writes == 5: return 3
                if target in files and writes == 0:
                    return ord('N') if fault == 'decline' else ord('Y')
                return 0
            if service == 25: return 0
            if service == 26: dma = ptr;return 0
            n = name(ptr)
            if service == 15:
                if n not in files: return 255
                cursors[ptr] = 0
                if n == target and renames >= 2: opened_final = True
                ro, sy = attrs.get(n, (0, 0))
                c.mem[ptr+9] |= ro;c.mem[ptr+10] |= sy
                return 0
            if service == 16:
                if fault == 'close' and writes == 161: return 255
                return 0
            if service == 22:
                if fault == 'create': return 255
                assert n not in files
                files[n] = bytearray();cursors[ptr] = 0;return 0
            if service == 21:
                writes += 1
                if fault in ('write', 'delete') and writes == 5: return 2
                files[n].extend(c.mem[dma:dma+128]);return 0
            if service == 20:
                at = cursors[ptr]*128
                if at == len(files[n]): return 1
                c.mem[dma:dma+128] = files[n][at:at+128]
                if (fault == 'verify' and n == 'SYSGEN.$$$' and at == 128 or
                    fault == 'final-verify' and opened_final and at == 128):
                    c.mem[dma] ^= 1
                cursors[ptr] += 1
                return 0
            if service == 19:
                if fault == 'delete' or fault == 'backup-delete' and n == 'SYSGEN.BAK':
                    return 255
                if n not in files:return 255
                del files[n];return 0
            if service == 23:
                renames += 1
                if fault == 'rename-old' or fault == 'rename-new' and renames == 2:
                    return 255
                dest = name(ptr+16)
                if fault == 'partial-old' and renames == 1 or fault == 'partial-new' and renames == 2:
                    original = files[n]
                    split = len(original)//2
                    files[dest] = original[:split]
                    files[n] = original[split:]
                    return 255
                assert dest not in files
                files[dest] = files.pop(n)
                return 0
            raise AssertionError(('unexpected BDOS', service, n))
        c.port_read = io
        c.run(a('XEXPORTGO'), limit=3000000)
        text = ''.join(console)
        assert bytes(disk) == before_disk
        if fault in ('new', 'new-default', 'replace', 'backup-delete'):
            assert bytes(files[target]) == expected, fault
            assert 'Package exported and verified.' in text, (fault, text)
            assert 'SYSGEN.$$$' not in files
            assert ('SYSGEN.BAK' in files) == (fault == 'backup-delete')
            assert reads == list(range(1, 160))+[0]
        elif fault in ('decline', 'temp-exists', 'backup-exists',
                       'protected-ro', 'protected-sys'):
            assert {n: bytes(b) for n, b in files.items()} == original_files, (fault, text)
        elif fault == 'rename-old':
            assert bytes(files[target]) == old
            assert bytes(files['SYSGEN.$$$']) == expected
        elif fault == 'rename-new':
            assert target not in files
            assert bytes(files['SYSGEN.BAK']) == old
            assert bytes(files['SYSGEN.$$$']) == expected
        elif fault == 'partial-old':
            assert bytes(files['SYSGEN.BAK'])+bytes(files[target]) == old
            assert bytes(files['SYSGEN.$$$']) == expected
            assert 'publication failed' in text
        elif fault == 'partial-new':
            assert bytes(files[target])+bytes(files['SYSGEN.$$$']) == expected
            assert bytes(files['SYSGEN.BAK']) == old
            assert 'publication failed' in text
        elif fault == 'final-verify':
            assert bytes(files['SYSGEN.BAK']) == old
            assert 'publication failed' in text
        elif fault == 'delete':
            assert target not in files and 'SYSGEN.$$$' in files
            assert 'could not be removed' in text
        else:
            assert target not in files and 'SYSGEN.$$$' not in files, (fault, text)
        if fault not in ('new', 'new-default', 'replace', 'backup-delete'):
            assert 'Package exported and verified.' not in text, (fault, text)
    print(f'PASS: {len(cases)} emitted-code export/package/failure cases; saved startup and exact payload preserved')


if __name__ == '__main__':
    main()
