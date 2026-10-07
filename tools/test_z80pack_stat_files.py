#!/usr/bin/env python3
"""Check exact STAT totals on private multi-extent and many-file media."""
import argparse
import subprocess
import re
from pathlib import Path
from test_z80pack_submit_xsub import ROOT, run_case
from build_ccp import assemble


def capacity_probe():
    from test_bios import Z80
    listing = (ROOT / 'build/utilities/stat.lst').read_text()
    def address(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':', listing, re.M | re.I)[1], 16)
    cpu = Z80(b'')
    binary = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    cpu.mem[0x100:0x100 + len(binary)] = binary
    cpu.setword(address('DPB'), 0x8000)
    cpu.setword(address('DIRENT'), 0x8100)
    cpu.mem[0x8006] = 1  # eight word-sized allocation slots
    cpu.mem[address('KSHIFT')] = 1
    for entries, slots, expected in [(384, 400, 384), (128, 400, 128), (384, 100, 100), (384, 0, 0)]:
        cpu.setword(0x8007, entries - 1)
        cpu.setword(6, address('SUMMARY') + slots * 16 + 7)
        cpu.run(address('SUMROOM'), limit=10000)
        assert cpu.word(address('SUMCAP')) == expected
    cpu.setword(address('SUMCAP'), 384)
    for i in range(385):
        cpu.mem[0x8100:0x8120] = bytes(32)
        cpu.mem[0x8101:0x810c] = f'N{i:07}DAT'.encode()
        cpu.mem[0x810f] = 1
        cpu.setword(0x8110, i + 1)
        cpu.run(address('SUMEXTENT'), limit=200000)
    assert cpu.word(address('SUMCOUNT')) == 384
    assert cpu.mem[address('SUMFULL')] == 1
    for i in range(384):
        offset = address('SUMMARY') + i * 16
        assert cpu.mem[offset:offset + 11] == f'N{i:07}DAT'.encode()
        assert cpu.word(offset + 11) == 1
        assert cpu.word(offset + 13) == 2
        assert cpu.mem[offset + 15] == 1
    # The reported SYSTEM.SYS case uses EXM=0: two physical entries.
    cpu.setword(address('SUMCOUNT'), 0)
    cpu.mem[address('SUMFULL')] = 0
    for extent, records, blocks in ((0, 128, 8), (1, 33, 3)):
        cpu.mem[0x8100:0x8120] = bytes(32)
        cpu.mem[0x8101:0x810c] = b'SYSTEM  SYS'
        cpu.mem[0x810c] = extent
        cpu.mem[0x810f] = records
        for i in range(blocks):
            cpu.setword(0x8110 + i * 2, 1 + extent * 8 + i)
        cpu.run(address('SUMEXTENT'), limit=200000)
    offset = address('SUMMARY')
    assert cpu.word(address('SUMCOUNT')) == 1
    assert cpu.word(offset + 11) == 161
    assert cpu.word(offset + 13) == 22
    assert cpu.mem[offset + 15] == 2
    print('STAT EXM=0 two-entry totals, 384-summary boundary and overflow passed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, default=ROOT / 'build/z80pack-iobyte-qualified')
    parser.add_argument('--simulator', type=Path, default=Path.home() / 'projects/git/z80pack/cpmsim/cpmsim')
    args = parser.parse_args()
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)

    capacity_probe()

    def files(work):
        subprocess.run(['cpmrm', '-f', 'bettercpm-default', str(work / 'disks/drivea.dsk'), '0:stat.com'], cwd=work, check=True)
        image = work / 'disks/driveb.dsk'
        blank = image.read_bytes()
        image.unlink()
        image.write_bytes(blank)
        fixtures = {'SYSTEM.SYS': 161 * 128, 'LONG.DAT': 513 * 128}
        fixtures.update({f'F{i:02}.DAT': 128 for i in reversed(range(24))})
        for name, size in fixtures.items():
            source = work / name
            source.write_bytes(bytes(size))
            subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(image), str(source), '0:' + name], cwd=work, check=True)
        for user in (3, 15, 31):
            subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default',
                            str(image), str(source), f'{user}:USER.DAT'],
                           cwd=work, check=True)
        stat = (ROOT / 'build/utilities/STAT.COM').read_bytes()
        stat3 = work / 'STAT3.COM'
        stat3.write_bytes(stat)
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default',
                        str(work / 'disks/drivea.dsk'), str(stat3), '3:STAT.COM'],
                       cwd=work, check=True)
        # Test-only trampoline marks the selected drive R/O at SETATTR entry.
        listing = (ROOT / 'build/utilities/stat.lst').read_text()
        entry = int(re.search(r'^([0-9a-f]{4})\s+.*?\bSETATTR:', listing, re.M | re.I)[1], 16)
        rostat = bytearray(stat)
        original = bytes(rostat[entry - 0x100:entry - 0x100 + 3])
        trampoline = (len(stat) + 0x100 + 4095) & ~255
        rostat[entry - 0x100:entry - 0x100 + 3] = bytes((0xc3, trampoline & 255, trampoline >> 8))
        target = entry + 3
        wrapper = bytes.fromhex('0e 1c cd 05 00') + original + bytes((0xc3, target & 255, target >> 8))
        rostat += bytes(trampoline - 0x100 - len(rostat)) + wrapper
        source = """        ORG 100H
        LD DE,FCB
        LD C,22
        CALL 5
        CP 0FFH
        JR Z,BAD
        LD A,2
        LD (FCB+34),A
        LD DE,FCB
        LD C,34
        CALL 5
        OR A
        JR NZ,BAD
        LD DE,FCB
        LD C,16
        CALL 5
        CP 0FFH
        JR Z,BAD
        LD DE,GOOD
        JR PRINT
BAD:    LD DE,FAIL
PRINT:  LD C,9
        CALL 5
        JP 0
GOOD:   DB 'SPARSE READY',13,10,'$'
FAIL:   DB 'SPARSE FAILED',13,10,'$'
FCB:    DB 2,'SPARSE  DAT'
        REPT 24
        DB 0
        ENDM
        END
"""
        probe = assemble(Path.home() / 'bin/z80asm', source, work / 'sparse.bin', work / 'sparse.lst', 0x100)
        # Populate the login vector within the same invocation before its snapshot.
        allentry = int(re.search(r'^([0-9a-f]{4})\s+.*?\bALLDETAILS:', listing, re.M | re.I)[1], 16)
        allstat = bytearray(stat)
        original = bytes(allstat[allentry - 0x100:allentry - 0x100 + 5])
        allstat[allentry - 0x100:allentry - 0x100 + 5] = bytes((0xc3, trampoline & 255, trampoline >> 8, 0, 0))
        target = allentry + 5
        wrapper = bytes.fromhex('1e 01 0e 0e cd 05 00 1e 00 0e 0e cd 05 00') + original + bytes((0xc3, target & 255, target >> 8))
        allstat += bytes(trampoline - 0x100 - len(allstat)) + wrapper
        return {'STAT.COM': stat, 'ROSTAT.COM': rostat, 'SPMAKE.COM': probe, 'ALLSTAT.COM': allstat}

    body = r'''
send -s "stat b:system.sys\r"
expect -re {00161 Recs +00022K Bytes +00001 Ext R/W B:SYSTEM +\.SYS}
prompt
send -s "stat b:long.dat\r"
expect -re {00513 Recs +00066K Bytes +00003 Ext R/W B:LONG +\.DAT}
prompt
send -s "stat b:system.sys \$S\r"
expect -re {00161 +00161 Recs +00022K Bytes +00001 Ext R/W B:SYSTEM +\.SYS}
prompt
send -s "spmake\r"
expect -exact "SPARSE READY"
prompt
send -s "stat b:sparse.dat \$S\r"
expect -re {00513 +00001 Recs +00002K Bytes +00002 Ext R/W B:SPARSE +\.DAT}
prompt
send -s "stat b:f?***.dat\r"
'''
    for i in range(24):
        body += f'expect -re {{00001 Recs +00002K Bytes +00001 Ext R/W B:F{i:02} +\\.DAT}}\n'
    body += 'prompt\n'
    for filespec in ['F**?.DAT', 'F.**?', 'F?**?.DAT*', 'F*.DAT*']:
        body += f'send -s "stat b:{filespec}\\r"\nexpect -exact "Invalid filespec"\nprompt\n'
    for option in ['$R/OX', '$SYSTEM', '$DIRX', '$', '$S EXTRA']:
        option = option.replace('$', r'\$')
        body += f'send -s "stat b:f00.dat {option}\\r"\nexpect -exact "Invalid STAT command"\nprompt\n'
    body += r'''send -s "stat b:f00.dat\r"
expect -re {00001 Recs +00002K Bytes +00001 Ext R/W B:F00 +\.DAT}
prompt
'''
    for option, result in [('$R/O', 'R/O'), ('$R/W', 'R/W'), ('$SYS', 'SYS'), ('$DIR', 'DIR')]:
        option = option.replace('$', r'\$')
        body += f'send -s "stat b:f00.dat {option}\\r"\nexpect -re {{F00 +\\.DAT set to {result}}}\nprompt\n'
    body += r'''send -s "rostat b:f00.dat \$SYS\r"
expect -re {F00 +\.DAT attribute update failed: disk is read-only}
prompt
send -s "stat b:f00.dat\r"
expect -re {00001 Recs +00002K Bytes +00001 Ext R/W B:F00 +\.DAT}
prompt
send -s "stat con:=uc1: rdr:=ur2: pun:=up2: lst:=ul1:\r"
expect -exact "CON: is UC1:"
expect -exact "RDR: is UR2:"
expect -exact "PUN: is UP2:"
expect -exact "LST: is UL1:"
prompt
send -s "stat con:=crt: rdr:=ptr: pun:=ptp: lst:=lpt:\r"
expect -exact "CON: is CRT:"
expect -exact "RDR: is PTR:"
expect -exact "PUN: is PTP:"
expect -exact "LST: is LPT:"
prompt
send -s "stat rdr:=crt:\r"
expect -exact "Invalid Assignment"
prompt
send -s "stat con:=crt:x\r"
expect -exact "Invalid Assignment"
prompt
send -s "stat con:=uc1: nonsense\r"
expect -exact "CON: is UC1:"
expect -exact "Invalid Assignment"
prompt
send -s "stat dev:\r"
expect -exact "CON: is UC1:"
expect -exact "RDR: is PTR:"
expect -exact "PUN: is PTP:"
expect -exact "LST: is LPT:"
prompt
send -s "stat b:dsk:\r"
expect {
 -exact "A: Drive Characteristics" {puts "UNEXPECTED DRIVE A"; exit 1}
 -exact "B: Drive Characteristics" {}
 timeout {exit 1}
}
expect -exact "02656: 128 Byte Record Capacity"
expect -exact "00332: Kilobyte Drive Capacity"
expect -exact "36: 128 Byte Records/Track"
expect -exact "166: Allocation Blocks"
expect -exact "64: 32 Byte Directory Entries"
expect -exact "64: Checked Directory Entries"
expect -exact "256: Records/Extent"
expect -exact "16: Records/Allocation Block"
expect -exact "6: Reserved Tracks"
prompt
send -s "stat dsk:\r"
expect -exact "A: Drive Characteristics"
expect -exact "6: Reserved Tracks"
expect {
 -exact "B: Drive Characteristics" {puts "UNLOGGED DRIVE B"; exit 1}
 -exact "A0>_ " {}
 timeout {exit 1}
}
send -s "allstat dsk:\r"
expect -exact "A: Drive Characteristics"
expect -exact "B: Drive Characteristics"
expect -exact "6: Reserved Tracks"
expect {
 -re {[CD]: Drive Characteristics} {puts "UNLOGGED DRIVE"; exit 1}
 -exact "A0>_ " {}
 timeout {exit 1}
}
send -s "b:\r"
expect -exact "B0>_ "
send -s "user 3\r"
expect -exact "B3>_ "
send -s "a:stat a:dsk:\r"
expect -exact "A: Drive Characteristics"
expect -exact "6: Reserved Tracks"
expect -exact "B3>_ "
send -s "a:stat usr:\r"
expect -re {Active User : +3\r?\nActive Files: +0 +3 +15 +31\r?\n}
expect -exact "B3>_ "
send -s "user 0\r"
expect -exact "B0>_ "
send -s "a:\r"
prompt
send -s "stat val:\r"
expect -exact "Temp R/O Disk: d:=R/O"
expect -exact "\$R/O \$R/W \$SYS \$DIR"
expect -exact "\$S (logical record count)"
expect -exact "Device Status: DEV:"
expect -exact "CON:=TTY: CRT: BAT: UC1:"
expect -exact "RDR:=TTY: PTR: UR1: UR2:"
expect -exact "PUN:=TTY: PTP: UP1: UP2:"
expect -exact "LST:=TTY: CRT: LPT: UL1:"
expect -exact "Separate multiple assignments with spaces."
expect -exact "BAT: console input uses RDR:; output uses LST:."
prompt
send -s "stat dev:\r"
expect -exact "CON: is UC1:"
expect -exact "RDR: is PTR:"
expect -exact "PUN: is PTP:"
expect -exact "LST: is LPT:"
prompt
send -s "bye\r"
expect eof
'''

    # Every required output must fail explicitly on timeout, including Tcl's
    # one-pattern expect calls which otherwise may simply return on timeout.
    body = body.replace('expect -re ', 'mustre ').replace('expect -exact ', 'mustexact ')
    body = r'''proc mustre {pattern} {
 expect {
  -re $pattern {}
  timeout {puts "MISSING REQUIRED REGEX: $pattern"; exit 1}
  eof {puts "UNEXPECTED EXIT"; exit 1}
 }
}
proc mustexact {pattern} {
 expect {
  -exact $pattern {}
  timeout {puts "MISSING REQUIRED TEXT: $pattern"; exit 1}
  eof {puts "UNEXPECTED EXIT"; exit 1}
 }
}
''' + body
    run_case(args.image_dir.resolve(), args.simulator.resolve(), 'stat-files', files, body)
    def empty_files(work):
        image = work / 'disks/driveb.dsk'
        size = len(image.read_bytes())
        image.unlink()
        image.write_bytes(bytes([0xe5]) * size)
        subprocess.run(['cpmrm', '-f', 'bettercpm-default',
                        str(work / 'disks/drivea.dsk'), '0:stat.com'],
                       cwd=work, check=True)
        return {'STAT.COM': (ROOT / 'build/utilities/STAT.COM').read_bytes()}
    empty_body = r'''
send -s "b:\r"
expect -exact "B0>_ "
send -s "a:stat usr:\r"
expect {
 -re {Active User : +0\r?\nActive Files:\r?\n} {}
 timeout {puts "EMPTY USER REPORT MISSING"; exit 1}
 eof {exit 1}
}
expect -exact "B0>_ "
send -s "bye\r"
expect eof
'''
    empty_body = body[:body.index('send -s')] + empty_body.replace('expect -exact ', 'mustexact ')
    run_case(args.image_dir.resolve(), args.simulator.resolve(), 'stat-empty-users', empty_files, empty_body)
    print('STAT populated/empty user areas, user 31 and B3 context restoration passed')
    print('STAT exact totals, 24-file star matching, attribute options, device assignments and invalid-tail rejection passed')


if __name__ == '__main__':
    main()
