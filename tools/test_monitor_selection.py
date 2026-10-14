#!/usr/bin/env python3
"""Execute production monitor selection through real RSX preparation/commit.

Synthetic providers test binding and movement, not terminal rendering.
"""
import argparse
import re
import tempfile
from pathlib import Path
from build_rsx_module import make_module
from system_layout import LAYOUT
from test_bios import Z80
import test_rsx_stage3 as stage

ROOT = Path(__file__).resolve().parents[1]


def provider(name, capabilities=1):
    # Unclaimed BDOS dispatch chains through the loader-owned next pointer.
    code = b'\0'*8 + bytes((0x2A, 0, 0x90, 0xE9, 0xC9, 0x79, 0xC9))
    return make_module(name=name, version=(0, 1), services=[], linked_base=0x9000,
                       code=code, relocations=[9], reconstruction_class='STATEFUL',
                       callable_services=[(b'MCON', 1, 0, 13, capabilities)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--z80pack-build', type=Path)
    args = parser.parse_args()
    bios = args.z80pack_build or ROOT/'build/bios'
    output = ROOT/'build/test-results/monitor-selection'
    output.mkdir(parents=True, exist_ok=True)
    first, second = provider('MONTEST', 2 if args.z80pack_build else 1), provider('MONOTHER', 2 if args.z80pack_build else 1)
    (output/'MONTEST.RSX').write_bytes(first)
    (output/'MONOTHER.RSX').write_bytes(second)
    stage.FILES = (("R3PACK  ", "build/system/R3PACK.RSX"),
                   ("HELLO   ", "build/rsx/HELLO.RSX"),
                   ("MONTEST ", str((output/'MONTEST.RSX').relative_to(ROOT))),
                   ("MONOTHER", str((output/'MONOTHER.RSX').relative_to(ROOT))))
    sources = (0x7800, 0xB400, 0xB800, 0xBC00)
    cpu = Z80((bios/'bios.bin').read_bytes())
    for (_, relative), address in zip(stage.FILES, sources):
        image = (ROOT/relative).read_bytes()
        cpu.mem[address:address+len(image)] = image
    with tempfile.TemporaryDirectory() as temporary:
        stub = stage.file_stub(Path(temporary), sources)
    cpu.mem[LAYOUT['FILE']:LAYOUT['FILE']+len(stub)] = stub
    cpu.mem[LAYOUT['BIOS']+60:LAYOUT['BIOS']+63] = b'\xAF\xC9\0'
    bootstrap = (ROOT/'build/system/r3entry.bin').read_bytes()
    listing = (bios/'bios.lst').read_text(errors='replace')
    binding = int(re.search(r'^([0-9a-f]{4})\s+.*\bMP_MON:',listing,re.M)[1],16)
    cpu.run(LAYOUT['BIOS']+72)
    basic = cpu.word(binding)
    cpu.setword(stage.HEAD,0)
    cpu.setword(stage.LOW,LAYOUT['RSX'])
    cpu.setword(stage.TPA,LAYOUT['TPA'])
    cpu.setword(6,LAYOUT['TPA'])
    cpu.setword(stage.GEN,1)
    cpu.mem[stage.RSTCOUNT:stage.RSTCOUNT+41] = bytes(41)
    stage.invoke(cpu,bootstrap,1,b'HELLO   ')
    assert cpu.a == 0 and cpu.word(binding) == basic
    stage.invoke(cpu,bootstrap,1,b'MONTEST ')
    old = cpu.word(stage.LOW)
    assert cpu.a == 0 and cpu.word(binding) == old+13
    cpu.mem[old+30] = 0xA5
    before = bytes(cpu.mem[old:LAYOUT['RSX']])
    generation = cpu.word(stage.GEN)
    stage.invoke(cpu,bootstrap,1,b'MONOTHER')
    assert cpu.a != 0 and cpu.word(binding) == old+13
    assert cpu.word(stage.GEN) == generation
    assert bytes(cpu.mem[old:LAYOUT['RSX']]) == before
    container = cpu.mem.find(b'R3PACK  ', LAYOUT['FILE'], LAYOUT['FILE']+len(stub))
    cpu.mem[container] = ord('X')
    stage.invoke(cpu,bootstrap,2,b'HELLO   ')
    assert cpu.a != 0 and cpu.word(binding) == old+13
    assert cpu.word(stage.GEN) == generation
    assert bytes(cpu.mem[old:LAYOUT['RSX']]) == before
    cpu.mem[container] = ord('R')
    # Corrupt live descriptor/header facts cannot redefine the retained service.
    for address, damaged in [(old+4, b'\x02'), (old+5, b'\x01'),
                              (old+6, b'\xff\xff'),
                              (old+256-10+6, b'\x0e\0'),
                              (old+256-10+8, b'\0\0')]:
        saved = bytes(cpu.mem[address:address+len(damaged)])
        cpu.mem[address:address+len(damaged)] = damaged
        damaged_image = bytes(cpu.mem[old:LAYOUT['RSX']])
        stage.invoke(cpu,bootstrap,2,b'HELLO   ')
        assert cpu.a != 0 and cpu.word(binding) == old+13
        assert cpu.word(stage.GEN) == generation
        assert bytes(cpu.mem[old:LAYOUT['RSX']]) == damaged_image
        cpu.mem[address:address+len(saved)] = saved
    # An otherwise valid changed carrier must not redefine a retained live entry.
    record = sources[2] + first.index(b'MCON') + 6
    original = cpu.word(record)
    cpu.setword(record,14)
    stage.invoke(cpu,bootstrap,2,b'HELLO   ')
    assert cpu.a != 0 and cpu.word(binding) == old+13
    assert cpu.word(stage.GEN) == generation
    assert bytes(cpu.mem[old:LAYOUT['RSX']]) == before
    cpu.setword(record,original)
    stage.invoke(cpu,bootstrap,2,b'HELLO   ')
    new = cpu.word(stage.LOW)
    assert cpu.a == 0 and new > old and cpu.word(binding) == new+13
    assert cpu.mem[new+30] == 0xA5
    stage.invoke(cpu,bootstrap,1,b'HELLO   ')
    assert cpu.a == 0 and cpu.word(binding) == new+13
    assert cpu.mem[new+30] == 0xA5
    stage.invoke(cpu,bootstrap,2,b'HELLO   ')
    assert cpu.a == 0 and cpu.word(binding) == new+13
    stage.invoke(cpu,bootstrap,2,b'MONTEST ')
    assert cpu.a == 0 and cpu.mem[stage.RSTCOUNT] == 0
    assert cpu.word(binding) == basic and cpu.word(6) == LAYOUT['TPA']
    stage.invoke(cpu,bootstrap,1,b'MONTEST ')
    assert cpu.a == 0
    stage.REQUEST = cpu.word(stage.LOW) + 64  # retiring provider owns its durable request
    cpu.mem[0:3] = b'\xc3\xff\xff'  # observe self-retirement's warm-boot boundary
    stage.invoke(cpu,bootstrap,4,b'MONTEST ')
    assert cpu.mem[stage.RSTCOUNT] == 0 and cpu.word(binding) == basic
    assert cpu.word(6) == LAYOUT['TPA']
    print('PASS: real MCON selection, duplicate/changed-carrier rejection,')
    print('retained movement/state preservation, unload and core TPA restoration')


if __name__ == '__main__':
    main()
