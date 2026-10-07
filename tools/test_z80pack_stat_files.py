#!/usr/bin/env python3
"""Check exact STAT totals on private multi-extent and many-file media."""
import argparse
import subprocess
import re
from pathlib import Path
from test_z80pack_submit_xsub import ROOT, run_case


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
    for i in range(65):
        cpu.mem[0x8100:0x8120] = bytes(32)
        cpu.mem[0x8101:0x810c] = f'N{i:07}DAT'.encode()
        cpu.mem[0x810f] = 1
        cpu.mem[0x8110] = i + 1
        cpu.run(address('SUMEXTENT'), limit=20000)
    assert cpu.mem[address('SUMCOUNT')] == 64
    assert cpu.mem[address('SUMFULL')] == 1
    for i in range(64):
        offset = address('SUMMARY') + i * 16
        assert cpu.mem[offset:offset + 11] == f'N{i:07}DAT'.encode()
        assert cpu.word(offset + 11) == 1
        assert cpu.word(offset + 13) == 2
        assert cpu.mem[offset + 15] == 1
    # The reported SYSTEM.SYS case uses EXM=0: two physical entries.
    cpu.mem[address('SUMCOUNT')] = 0
    cpu.mem[address('SUMFULL')] = 0
    for extent, records, blocks in ((0, 128, 8), (1, 33, 3)):
        cpu.mem[0x8100:0x8120] = bytes(32)
        cpu.mem[0x8101:0x810c] = b'SYSTEM  SYS'
        cpu.mem[0x810c] = extent
        cpu.mem[0x810f] = records
        for i in range(blocks):
            cpu.setword(0x8110 + i * 2, 1 + extent * 8 + i)
        cpu.run(address('SUMEXTENT'), limit=20000)
    offset = address('SUMMARY')
    assert cpu.mem[address('SUMCOUNT')] == 1
    assert cpu.word(offset + 11) == 161
    assert cpu.word(offset + 13) == 22
    assert cpu.mem[offset + 15] == 2
    print('STAT EXM=0 two-entry totals, 64-summary boundary and overflow passed')


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
        fixtures.update({f'F{i:02}.DAT': 128 for i in range(24)})
        for name, size in fixtures.items():
            source = work / name
            source.write_bytes(bytes(size))
            subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(image), str(source), '0:' + name], cwd=work, check=True)
        stat = (ROOT / 'build/utilities/STAT.COM').read_bytes()
        # Test-only trampoline marks the selected drive R/O at SETATTR entry.
        listing = (ROOT / 'build/utilities/stat.lst').read_text()
        entry = int(re.search(r'^([0-9a-f]{4})\s+.*?\bSETATTR:', listing, re.M | re.I)[1], 16)
        rostat = bytearray(stat)
        original = bytes(rostat[entry - 0x100:entry - 0x100 + 3])
        rostat[entry - 0x100:entry - 0x100 + 3] = bytes((0xc3, 0, 0x18))
        target = entry + 3
        wrapper = bytes.fromhex('0e 1c cd 05 00') + original + bytes((0xc3, target & 255, target >> 8))
        rostat += bytes(0x1700 - len(rostat)) + wrapper
        return {'STAT.COM': stat, 'ROSTAT.COM': rostat}

    body = r'''
send -s "stat b:system.sys\r"
expect -re {00161 Recs +00022K Bytes +00001 Ext R/W B:SYSTEM +\.SYS}
prompt
send -s "stat b:long.dat\r"
expect -re {00513 Recs +00066K Bytes +00003 Ext R/W B:LONG +\.DAT}
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
    body += r'''send -s "rostat b:f00.dat \$sys\r"
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
send -s "bye\r"
expect eof
'''

    run_case(args.image_dir.resolve(), args.simulator.resolve(), 'stat-files', files, body)
    print('STAT exact totals, 24-file star matching, attribute options, device assignments and invalid-tail rejection passed')


if __name__ == '__main__':
    main()
