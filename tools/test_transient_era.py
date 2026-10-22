#!/usr/bin/env python3
"""Qualify ordinary transient ERA with actual CP/M disk mutations and prompts."""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from test_bios import Z80
from test_disk_utilities import ROOT
from test_z80pack_sysgen_install import session


def pure_checks():
    listing = (ROOT / 'build/utilities/era.lst').read_text()
    binary = (ROOT / 'build/utilities/ERA.COM').read_bytes()
    def addr(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':', listing, re.M | re.I)[1], 16)
    cases = {'': 0x11, '$ARC': 0x10, '$SYS': 0x44, '$RO': 0x22,
             '$SYS+$RO,$ARC': 0x98, '$RO,$RW': 0x33,
             '!$DIR': 0x44, '!$RW': 0x22, '!!$SYS': 0x44,
             '$SYS+$ARC': 0x40, '$SYS,$ARC': 0x54,
             '$SYS+$RO': 0x88, '!$SYS+!$RO': 0x11}
    for expression, expected in cases.items():
        cpu = Z80(b'')
        cpu.mem[0x100:0x100 + len(binary)] = binary
        text = expression.encode()
        cpu.mem[0x3000:0x3000+len(text)] = text
        cpu.mem[addr('OQ_PTR'):addr('OQ_PTR')+2] = (0x3000).to_bytes(2, 'little')
        cpu.mem[addr('OQ_LEN')] = len(text)
        cpu.run(addr('E_ADMISSION'), limit=100000)
        assert cpu.mem[addr('E_ALLOW')] == expected, (expression, cpu.mem[addr('E_ALLOW')], expected)
    # Execute the actual DWORD formatter, including internal zeros and >64K.
    for number in (0, 1, 10, 101, 1000, 65535, 65536, 100001, 4294967295):
        cpu = Z80(b'');cpu.mem[0x100:0x100+len(binary)] = binary
        cpu.mem[5:8] = bytes((0xDB,0xFE,0xC9))
        output = bytearray()
        def bdos(port):
            assert cpu.c == 2, cpu.c
            output.append(cpu.e)
            return 0
        cpu.port_read = bdos
        cpu.mem[addr('E_VALUE'):addr('E_VALUE')+4] = number.to_bytes(4,'little')
        cpu.run(addr('E_DEC32'), limit=100000)
        assert output.decode() == str(number), (number, output)
    # Drive failure recovery through the production code with a failing BDOS
    # search. Help must not count as a skip/retry, and /Y must never read input.
    for keys, unattended, expected_fail, expected_search in (
            ([ord('?'), ord('S')], False, 1, 0),
            ([ord('R'), 0, ord('S')], False, 1, 1),
            ([ord('A')], False, 0, 0),
            ([3], False, 0, 0), ([], True, 1, 0)):
        cpu=Z80(b'');cpu.mem[0x100:0x100+len(binary)]=binary
        cpu.mem[0:3]=bytes((0xC3,0xFF,0xFF));cpu.mem[5:8]=bytes((0xDB,0xFE,0xC9))
        heap=addr('E_HEAP');cpu.setword(addr('E_CURRENT'),heap);cpu.setword(addr('E_NEXT'),heap+32)
        cpu.mem[heap:heap+32]=bytes(32);cpu.mem[heap+2:heap+13]=b'FAIL    DAT'
        cpu.mem[heap+14]=2;cpu.ix=heap
        cpu.mem[addr('E_QUIET')]=1;cpu.mem[addr('E_YES')]=int(unattended)
        output=bytearray();pending=list(keys);searches=[]
        def fail_bdos(port):
            if cpu.c==2:output.append(cpu.e)
            elif cpu.c==6:
                assert not unattended
                assert pending, 'unexpected input request'
                return pending.pop(0)
            elif cpu.c in (17,18):searches.append(cpu.c);return 255
            return 0
        cpu.port_read=fail_bdos;cpu.run(addr('E_FAILURE'),limit=100000)
        assert cpu.word(addr('E_NFAIL'))==expected_fail
        assert len(searches)==expected_search
        assert not pending
        if ord('?') in keys:
            assert output.count(b'R Retry, S Skip, A Abort all.')==1
            assert output.count(b'R/S/A/? ')==2
    for restore_fails in (False, True):
        cpu=Z80(b'');cpu.mem[0x100:0x100+len(binary)]=binary
        cpu.mem[0:3]=bytes((0xC3,0xFF,0xFF));cpu.mem[5:8]=bytes((0xDB,0xFE,0xC9))
        heap=addr('E_HEAP');cpu.setword(addr('E_CURRENT'),heap);cpu.setword(addr('E_NEXT'),heap+32)
        cpu.mem[heap:heap+32]=bytes(32);cpu.mem[heap+2:heap+13]=b'FAIL    DAT'
        cpu.mem[heap+13]=1;cpu.mem[heap+14]=2;cpu.ix=heap
        cpu.mem[addr('E_QUIET')]=1;cpu.mem[addr('E_YES')]=1
        cpu.mem[addr('E_OVERRIDE')]=1;cpu.mem[addr('E_ALLOW')]=0x22
        attributes=[];output=bytearray();deletes=[]
        def erase_failure(port):
            if cpu.c==2:output.append(cpu.e)
            elif cpu.c==17:
                dma=addr('E_DMA');cpu.mem[dma:dma+32]=bytes(32)
                cpu.mem[dma+9]=128
                return 0
            elif cpu.c==18:return 255
            elif cpu.c==30:
                attributes.append(cpu.mem[cpu.de+9]&128)
                return 255 if restore_fails and len(attributes)==2 else 0
            elif cpu.c==19:deletes.append(1);return 255
            return 0
        cpu.port_read=erase_failure;cpu.run(addr('E_TRY'),limit=100000)
        assert attributes==[0,128] and deletes==[1],(attributes,deletes)
        assert cpu.word(addr('E_NFAIL'))==1 and cpu.word(addr('E_ERASED'))==0
        assert (b'Unable to restore read-only protection.' in output)==restore_fails
    cpu=Z80(b'');cpu.mem[0x100:0x100+len(binary)]=binary
    heap=addr('E_HEAP');cpu.setword(addr('E_NEXT'),heap)
    cpu.setword(addr('E_LIMIT'),heap+31)
    cpu.mem[heap:heap+64]=bytes([0xA5])*64
    cpu.run(addr('E_RECORD'),limit=10000)
    assert cpu.carry and cpu.word(addr('E_NEXT'))==heap
    assert cpu.mem[heap:heap+64]==bytes([0xA5])*64
    for answer in (32, 13, 3):
        cpu=Z80(b'');cpu.mem[0x100:0x100+len(binary)]=binary
        cpu.mem[0:3]=bytes((0xC3,0xFF,0xFF));cpu.mem[5:8]=bytes((0xDB,0xFE,0xC9))
        cpu.mem[addr('E_PAGING')]=1;cpu.mem[addr('E_LINES')]=23;cpu.a=ord('X')
        output=bytearray();keys=[answer]
        def page_bdos(port):
            if cpu.c==6:return keys.pop(0)
            if cpu.c==2:output.append(cpu.e)
            elif cpu.c==9:
                start=cpu.de;end=cpu.mem.index(36,start);output.extend(cpu.mem[start:end])
            return 0
        cpu.port_read=page_bdos;cpu.run(addr('E_CHAR'),limit=100000)
        assert not keys and output.count(b'MORE -- Space/ENTER for next page.')==1
        assert (b'ERA cancelled.' in output)==(answer==3)
        if answer!=3:assert output.endswith(b'X')
    return len(cases)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    count = pure_checks()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    shutil.copytree(args.image_dir / 'disks', report / 'disks')
    shutil.copy2(args.image_dir / 'diskdefs', report / 'diskdefs')
    a, b = [report / 'disks' / ('drive' + n + '.dsk') for n in 'ab']
    def cpm(tool, disk, *values):
        return subprocess.run([tool, '-T', 'raw', '-f', 'bettercpm-default', str(disk), *map(str, values)], cwd=report, check=True, capture_output=True)
    cpm('cpmrm', a, '0:*.*')
    for name in ('ERA.COM', 'DIR.COM', 'CPX.COM'):
        cpm('cpmcp', a, ROOT / 'build/utilities' / name, '0:' + name)
    cpm('cpmcp', a, ROOT / 'build/cpx/RCP.CPX', '0:RCP.CPX')
    b.write_bytes(bytes([229]) * len(b.read_bytes()))
    original = {}
    def add(user, name, attrs='', size=128):
        path = report / ('fixture-' + str(user) + '-' + name)
        data = name.encode().ljust(size, b'X')
        path.write_bytes(data)
        cpm('cpmcp', b, path, str(user) + ':' + name)
        if attrs:
            cpm('cpmchattr', b, attrs, str(user) + ':' + name)
        original[(user,name)] = data
    for user in range(1, 10):
        add(user, 'NORMAL.DAT', size=33024 if user == 1 else 128)
        add(user, 'READONLY.DAT', 'r')
        add(user, 'SYSTEM.DAT', 's')
        add(user, 'BOTH.DAT', 'rs')
    add(10, 'N.DAT'); add(10, 'Y.DAT'); add(11,'EXACT.DAT')
    simulator = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    prompt = b'A0>_ '
    results = []
    def execute(command, responses=(), label='case'):
        wanted = responses[0][0] if responses else prompt
        steps = [(command.encode() + b'\r', wanted, 60)]
        for i, (_, outgoing) in enumerate(responses):
            next_prompt = responses[i+1][0] if i+1 < len(responses) else prompt
            steps.append((outgoing, next_prompt, 60))
        text = session(simulator, report/'disks', steps, report/(label+'.txt'))
        results.append(label)
        return text
    def remains(user, expected):
        # Inspect physical directory sectors; cpmls aborts on empty glob results.
        image = b.read_bytes()
        skew = [0,4,8,12,16,2,6,10]
        directory = b''.join(image[6*18*256+n*256:6*18*256+(n+1)*256] for n in skew)
        actual = set()
        for offset in range(0, len(directory), 32):
            entry = directory[offset:offset+32]
            if entry[0] == user:
                name = bytes(v & 127 for v in entry[1:12])
                actual.add(name[:8].decode().rstrip()+'.'+name[8:].decode().rstrip())
        assert actual == set(expected), (user, actual, expected)
        for name in expected:
            dest = report / ('remaining-' + str(user) + '-' + name)
            cpm('cpmcp', b, str(user)+':'+name, dest)
            assert dest.read_bytes() == original[(user,name)]
    all_names = {'NORMAL.DAT','READONLY.DAT','SYSTEM.DAT','BOTH.DAT'}
    text = execute(':ERA /VER', label='version')
    from utility_versions import banner
    assert banner('ERA').encode() in text
    text = execute(':ERA /Y B1:*.DAT', label='safe-broad')
    assert b'1 FILES ERASED, 3 SKIPPED, 34K FREED' in text, text[-500:]
    remains(1, all_names-{'NORMAL.DAT'})
    execute(':ERA /Y /R B2:*.DAT[$SYS+$RO,$RW]', label='matching-branch')
    remains(2, {'SYSTEM.DAT','READONLY.DAT'})
    execute(':ERA /Y /R B3:*.DAT[$SYS,$RO]', label='separate-branches')
    remains(3, {'NORMAL.DAT','BOTH.DAT'})
    execute(':ERA /Y /R B4:*.DAT[!$DIR+!$RW]', label='negated-aliases')
    remains(4, all_names-{'BOTH.DAT'})
    execute(':ERA /Y B5:*.DAT[$RO]', label='unattended-ro-skip')
    remains(5, all_names)
    text = execute(':ERA /C B5:READONLY.DAT[$RO]', [(b'Read only. Erase? Y/N ', b'Y')], 'one-ro-prompt')
    assert text.count(b'Erase? Y/N ') == 1
    remains(5, all_names-{'READONLY.DAT'})
    execute(':ERA /Q B6:*.DAT', [(b'ERASE THESE FILES? Y/N ', b'N')], 'quiet-still-confirms')
    remains(6, all_names)
    execute(':ERA B6:NORMAL.DAT', [(b'Erase? Y/N ', b'\x03')], 'abort-exact')
    remains(6, all_names)
    for i, operand in enumerate(('B6:F*A.DAT','B6:*.DAT /Z','B6:*.DAT /QQ','[B6,E0]:*.DAT','B6:*.DAT[$RO,]')):
        text = execute(':ERA /Y '+operand, label='invalid-'+str(i))
        assert b'Invalid filespec or option.' in text or b'INVALID DRIVE' in text
        remains(6, all_names)
    execute(':ERA /Y /C [B7,B8,B7]:*.DAT', label='multi-du-deduplicated')
    remains(7, all_names-{'NORMAL.DAT'}); remains(8, all_names-{'NORMAL.DAT'})
    execute(':ERA /Y /R B9:*.DAT[$RO+$SYS,$RO+$DIR,$RW+$SYS,$RW+$DIR]', label='all-admitted')
    remains(9, set())
    execute(':ERA /C B10:*.DAT', [(b'ERASE THESE FILES? Y/N ', b'Y'),
            (b'Erase? Y/N ', b'N'), (b'Erase? Y/N ', b'Y')], 'per-file-confirmation')
    remains(10, {'N.DAT'})
    text=execute(':ERA /C B11:EXACT.DAT', [(b'Erase? Y/N ',b'Y')], 'one-exact-prompt')
    assert text.count(b'Erase? Y/N ')==1
    remains(11,set())
    (report/'result.json').write_text(json.dumps({'pure_admission_cases':count,'sessions':results},indent=2)+'\n')
    print('PASS transient ERA:', len(results), 'sessions and', count, 'admission truth masks')


if __name__ == '__main__':
    main()
