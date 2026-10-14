#!/usr/bin/env python3
"""Execute explicit internal clear and prompt/reconstruction reset boundaries."""
import re
from pathlib import Path
from system_layout import LAYOUT
from test_bios import Z80
from test_ccp import cpu as command_cpu, symbol as command_symbol

ROOT = Path(__file__).resolve().parents[1]


def symbol(path, name):
    text = path.read_text(errors='replace')
    return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+r':',text,re.M|re.I)[1],16)


def bind(cpu):
    base = LAYOUT['BIOS']
    cpu.mem[base:base+757] = (ROOT/'build/bios/bios.bin').read_bytes()
    binding = symbol(ROOT/'build/bios/bios.lst','MP_MON')
    # Record operation, discard pending continuation, deliberately clobber scratch
    # registers. No literal output-control byte is involved.
    provider = bytes((0x32,0,0x71,0xAF,0x32,2,0x71,
                      0x21,0x34,0x12,0x11,0x78,0x56,0x01,0xBC,0x9A,0xC9))
    cpu.mem[0x7000:0x7000+len(provider)] = provider
    cpu.setword(binding,0x7000)
    cpu.setword(1,base+3)
    cpu.mem[0x7100:0x7103] = b'\xCC\0\x01'


def main():
    for stem in ['config','dup','sysgen']:
        cpu = Z80(b'')
        image = (ROOT/f'build/utilities/{stem.upper()}.COM').read_bytes()
        cpu.mem[0x100:0x100+len(image)] = image
        bind(cpu)
        cpu.hl, cpu.de, cpu.bc, cpu.a = 0x2345,0x3456,0x4567,0x81
        cpu.z, cpu.carry = True,True
        entry = symbol(ROOT/f'build/utilities/{stem}.lst','UI_CLEAR')
        before = (cpu.hl,cpu.de,cpu.bc,cpu.a,cpu.z,cpu.carry,cpu.sp)
        cpu.run(entry)
        assert cpu.mem[0x7100] == 4
        assert (cpu.hl,cpu.de,cpu.bc,cpu.a,cpu.z,cpu.carry,cpu.sp) == before
    # TYPE uses the same shared utility routine.
    cpu = Z80(b'')
    image = (ROOT/'build/utilities/TYPE.COM').read_bytes()
    cpu.mem[0x100:0x100+len(image)] = image
    bind(cpu)
    cpu.run(symbol(ROOT/'build/utilities/type.lst','UI_CLEAR'))
    assert cpu.mem[0x7100] == 4
    # The prompt loop covers resident handlers that return without warm boot.
    cpu = command_cpu()
    bind(cpu)
    cpu.mem[5:8] = b'\xc3\xff\xff'  # observe first prompt-output boundary
    cpu.run(command_symbol('CCP_LOOP'))
    assert cpu.mem[0x7100] == 5 and cpu.mem[0x7102] == 0
    # Reconstructing a disposed command environment resets before its first BDOS
    # operation, after establishing the safe reconstruction stack.
    cpu = Z80(b'')
    image = (ROOT/'build/trs80/ccpreload.bin').read_bytes()
    cpu.mem[LAYOUT['RELOADER']:LAYOUT['RELOADER']+len(image)] = image
    bind(cpu)
    cpu.mem[LAYOUT['BDOS']:LAYOUT['BDOS']+3] = b'\xc3\xff\xff'
    cpu.run(symbol(ROOT/'build/trs80/ccpreload.lst','CRBODY'))
    assert cpu.mem[0x7100] == 5 and cpu.mem[0x7102] == 0
    print('PASS: explicit clear preserves utility registers; prompt and reconstruction reset before output')


if __name__ == '__main__':
    main()
