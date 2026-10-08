#!/usr/bin/env python3
"""Check STAT summary bounds and preservation beyond the available workspace."""
import re
import subprocess
from test_bios import Z80
from test_disk_utilities import ROOT
from test_z80pack_stat_files import capacity_probe


def main():
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)
    capacity_probe()
    listing = (ROOT / 'build/utilities/stat.lst').read_text()
    def address(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':', listing, re.M | re.I)[1], 16)
    binary = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    for slots in (0, 1, 100, 128, 384):
        cpu = Z80(b'')
        cpu.mem[0x100:0x100 + len(binary)] = binary
        cpu.setword(address('DPB'), 0x8000)
        cpu.setword(address('DIRENT'), 0x8100)
        cpu.mem[0x8006] = 1
        cpu.mem[address('KSHIFT')] = 1
        cpu.setword(address('SUMCAP'), slots)
        end = address('SUMMARY') + slots * 16
        guard = bytes(range(64))
        cpu.mem[end:end + len(guard)] = guard
        for number in range(slots + 1):
            cpu.mem[0x8100:0x8120] = bytes(32)
            cpu.mem[0x8101:0x810c] = f'N{number:07}DAT'.encode()
            cpu.mem[0x810f] = 1
            cpu.setword(0x8110, number + 1)
            cpu.run(address('SUMEXTENT'), limit=200000)
        assert cpu.word(address('SUMCOUNT')) == slots
        assert cpu.mem[address('SUMFULL')] == 1
        assert cpu.mem[end:end + len(guard)] == guard, ('workspace overrun', slots)
    print('STAT zero/one/100/128/384-slot overflow preserves workspace boundary guards')


if __name__ == '__main__':
    main()
