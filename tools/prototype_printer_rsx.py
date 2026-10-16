#!/usr/bin/env python3
"""Isolated printer hook/filter prototype; never install into production images.

Runs real BDOS and BIOS code with a laboratory binding at 7000h. Lifecycle
publication is driven by this harness, not the production RSX manager. Generated
carrier is for format/size measurement only: PLST/PSET are not manager bindings.
"""
import argparse
import hashlib
import json
from pathlib import Path

from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module
from system_layout import LAYOUT
from test_bios import Z80
from test_utility_versions import address

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    args = parser.parse_args()
    out = ROOT/'build/audit/printer-prototype'
    out.mkdir(parents=True, exist_ok=True)
    source = (ROOT/'tools/prototypes/printer-filter.mac').read_text()
    def asm(name, text, base):
        return assemble(args.assembler, text, out/(name+'.bin'), out/(name+'.lst'), base)
    code = asm('filter', source, 0x8000)
    alternate = asm('filter-alt', source.replace('08000H', '08101H'), 0x8101)
    relocs = relocation_offsets(code, alternate, 0x101)
    listing = (out/'filter.lst').read_text()
    labels = {n: address(listing, n) for n in ('OUT', 'SET', 'MODE', 'PREV', 'LINE', 'COL')}
    carrier = make_module(name='PRNPRO', version=(0, 1), services=[],
                          linked_base=0x8000, code=code, relocations=relocs,
                          reconstruction_class='STATEFUL', callable_services=[
                              (b'PLST', 1, 0, labels['OUT']-0x8000, 0),
                              (b'PSET', 1, 0, labels['SET']-0x8000, 0)])
    (out/'PRNPRO.experimental').write_bytes(carrier)
    cpu = Z80((ROOT/'build/bios/bios.bin').read_bytes())
    bios_listing = (ROOT/'build/bios/bios.lst').read_text(errors='replace')
    raw = address(bios_listing, 'BIOLIST')
    hook = asm('hook', f''' ORG 7000H
LISTCALL: LD HL,(BINDING)
 JP (HL)
LISTRAW: JP {raw}
LISTBASE: LD HL,LISTRAW
LISTPUB: LD (BINDING),HL
 RET
BINDING: DW 0
 END
''', 0x7000)
    hlst = (out/'hook.lst').read_text()
    h = {n: address(hlst, n) for n in ('LISTCALL', 'LISTRAW', 'LISTBASE', 'LISTPUB', 'BINDING')}
    assert h['LISTRAW'] == 0x7004
    cpu.mem[0x7000:0x7000+len(hook)] = hook
    # Replace only the existing LIST vector target in this private CPU image.
    cpu.setword(LAYOUT['BIOS']+16, h['LISTCALL'])
    image = (ROOT/'build/bdos/bdos.bin').read_bytes()
    cpu.mem[LAYOUT['BDOS']:LAYOUT['BDOS']+len(image)] = image
    bdos_listing = (ROOT/'build/bdos/bdos.lst').read_text()
    echo = address(bdos_listing, 'UB_LISTE')
    emitted = []
    # Capture the raw leaf, allowing adversarial register destruction.
    cpu.mem[raw:raw+3] = bytes((0xdb, 241, 0xc9))
    def capture(port):
        if port & 255 == 241:
            emitted.append(cpu.c)
            cpu.bc, cpu.de, cpu.hl = 0xFFFF, 0xEEEE, 0xDDDD
        return 0
    cpu.port_read = capture
    cpu.mem[LAYOUT['BIOS']+6:LAYOUT['BIOS']+8] = bytes((0xaf, 0xc9))
    cpu.mem[LAYOUT['BIOS']+12] = 0xc9  # console rendering outside this fixture
    cpu.mem[0x8000:0x8000+len(code)] = code
    base = 0x8000
    def loc(name):
        return labels[name] + base-0x8000
    def bind():
        cpu.hl = loc('OUT')
        cpu.run(h['LISTPUB'])
    def configure(mode, page=66, width=8):
        cpu.a, cpu.b, cpu.d, cpu.e = 1, mode, page, width
        cpu.run(loc('SET'))
        assert cpu.a == 0
    def send(data, service=None):
        for ch in data:
            cpu.mem[echo] = int(service in (2, 9))
            if service is None:
                cpu.c = ch
                target = LAYOUT['BIOS']+15
            else:
                cpu.c, cpu.de = service, ch
                if service == 9:
                    cpu.mem[0x9000:0x9002] = bytes((ch, 36))
                    cpu.de = 0x9000
                target = LAYOUT['BDOS']
            before = cpu.sp
            cpu.run(target, limit=500000)
            assert cpu.sp == before
    cpu.run(h['LISTBASE'])
    send(b'R')
    assert emitted == list(b'R')
    bind()
    coverage = []
    for service in (None, 5, 2, 9):
        configure(1)
        emitted.clear()
        send(b'\r\nX', service)
        assert emitted == list(b'\rX'), (service, emitted)
        coverage.append({'service': 'direct BIOS' if service is None else service,
                         'input': 'CR LF X', 'output': 'CR X'})
    cases = [
        (0, 66, 8, b'A\r\nB\t\f', b'A\r\nB\t\f'),
        (1, 66, 8, b'\r\n\n', b'\r\n'),
        (4, 66, 8, b'A\tB', b'A       B'),
        (4, 66, 3, b'ABC\tD', b'ABC   D'),
        (2, 4, 8, b'A\r\nB\f', b'A\r\nB\n\n\n'),
        (2, 4, 8, b'\f', b'\n'*4),
        (7, 4, 8, b'A\t\r\n\f', b'A       \r\n\n\n'),
        (0, 66, 8, bytes(range(256)), bytes(range(256))),
        (6, 255, 255, b'A\t\f', b'A'+b' '*254+b'\n'*255),
        (2, 1, 1, b'\n\f', b'\n\n'),
    ]
    for mode, page, width, data, expected in cases:
        configure(mode, page, width)
        emitted.clear()
        send(data)
        assert bytes(emitted) == expected, (mode, bytes(emitted), expected)
    # Invalid settings must not partially change configuration or counters.
    configure(7, 4, 3)
    send(b'A')
    saved = bytes(cpu.mem[loc('MODE'):loc('COL')+1])
    for mode, page, width in ((8, 4, 3), (7, 0, 3), (7, 4, 0)):
        cpu.a, cpu.b, cpu.d, cpu.e = 1, mode, page, width
        cpu.run(loc('SET'))
        assert cpu.a == 255
        assert bytes(cpu.mem[loc('MODE'):loc('COL')+1]) == saved
    # Query is read-only; caller must resolve again after a profile change.
    cpu.a = 0
    cpu.run(loc('SET'))
    assert cpu.hl == loc('MODE')
    # Detach before copying/repair. Preserve counters, relocate instruction
    # operands using the same directory carried by the experimental module.
    cpu.run(h['LISTBASE'])
    moved = bytearray(cpu.mem[base:base+len(code)])
    delta = 0xA000-base
    for offset in relocs:
        value = int.from_bytes(moved[offset:offset+2], 'little')+delta
        moved[offset:offset+2] = value.to_bytes(2, 'little')
    cpu.mem[0xA000:0xA000+len(moved)] = moved
    cpu.mem[base:base+len(code)] = b'\xff'*len(code)
    emitted.clear()
    send(b'R')  # detached fallback must not enter poisoned old storage
    assert emitted == list(b'R')
    base = 0xA000
    bind()
    emitted.clear()
    send(b'\t')  # retained column=1, width=3 => two spaces
    assert emitted == list(b'  ')
    cpu.run(h['LISTBASE'])
    cpu.mem[base:base+len(code)] = b'\xff'*len(code)
    emitted.clear()
    send(b'U')
    assert emitted == list(b'U')
    # Exercise real platform IOBYTE dispatch separately from the adversarial
    # raw sink above. Stub only physical screen output on Model 4; cpmsim
    # executes the production chario include and actual OUT instructions.
    routing = []
    for platform in ('trs80m4', 'z80pack'):
        c = Z80((ROOT/'build/bios/bios.bin').read_bytes())
        c.mem[0x7000:0x7000+len(hook)] = hook
        c.mem[0x8000:0x8000+len(code)] = code
        c.setword(LAYOUT['BIOS']+16, h['LISTCALL'])
        if platform == 'trs80m4':
            screen = address(bios_listing, 'MH_OUT')
            c.mem[screen:screen+4] = bytes((0x79, 0xd3, 1, 0xc9))
            con = LAYOUT['BIOS']+12
            # Production BIOCONOT jumps to BIOLIST's body, not its vector.
            # An integrated hook must retain BIOLIST as the wrapper label and
            # rename the original body. Retarget that internal jump here.
            start = address(bios_listing, 'BIOCONOT')
            end = address(bios_listing, 'IO_CON')
            needle = bytes((0xc3, raw & 255, raw >> 8))
            jump = bytes(c.mem[start:end]).index(needle)+start
            c.setword(jump+1, h['LISTCALL'])
        else:
            chario = (ROOT/'src/platform/z80pack/chario.inc').read_text()
            chario = chario.replace('BIOLIST:', 'RAWLIST:')
            fragment = asm('chario', f" ORG 6000H\nBIOLIST EQU {LAYOUT['BIOS']+15}\n"
                           "MH_OUT: LD A,C\n OUT (1),A\n RET\n"
                           "MC_CALL: XOR A\n RET\n"+chario+"\n END\n", 0x6000)
            c.mem[0x6000:0x6000+len(fragment)] = fragment
            table = (out/'chario.lst').read_text()
            c.setword(h['LISTRAW']+1, address(table, 'RAWLIST'))
            con = address(table, 'BIOCONOT')
        c.run(h['LISTBASE'])
        c.hl = labels['OUT']
        c.run(h['LISTPUB'])
        c.a, c.b, c.d, c.e = 1, 4, 66, 8
        c.run(labels['SET'])
        ports = []
        c.port_write = lambda port, value: ports.append((port & 255, value))
        # Normal CRT console must bypass the list filter.
        c.mem[3] = 0x41
        c.c = 9
        c.run(con, limit=500000)
        assert ports == [(1, 9)], (platform, ports)
        ports.clear()
        # CON=LST must enter the filter once; raw output avoids recursion.
        c.mem[3] = 0x42
        c.c = 9
        c.run(con, limit=500000)
        assert ports == [(1, 32)]*8, (platform, ports)
        if platform == 'z80pack':
            ports.clear()
            c.mem[3] = 0x81  # LST=LPT, CON=CRT
            c.c = 65
            c.run(LAYOUT['BIOS']+15, limit=500000)
            assert ports == [(3, 65)], ports
        routing.append(platform)
    report = {'status': 'isolated prototype, not production manager integration',
              'hook_bytes': len(hook), 'additional_cold_call_bytes': 3,
              'model4_slot_overflow_if_appended': len(hook)+3,
              'payload_bytes': len(code), 'state_bytes': 6,
              'relocation_words': len(relocs),
              'runtime_allocation_bytes': int.from_bytes(carrier[14:16], 'little'),
              'callable_descriptors_bytes': 20, 'carrier_bytes': len(carrier),
              'bdos_sha256': hashlib.sha256(image).hexdigest(),
              'coverage': coverage, 'transformation_cases': len(cases),
              'iobyte_routing_platforms': routing,
              'lifecycle': ['detach fallback', 'relocate preserving state',
                            'republish', 'unload with poisoned storage'],
              'not_qualified': ['production manager validation/publication/rollback',
                                'BIOS slot recovery and whole-system fit',
                                'physical readiness/status and capability integration',
                                'CONFIG persistence', 'native assembly and emulator boot']}
    (out/'results.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
