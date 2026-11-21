#!/usr/bin/env python3
"""Execute private helper fixups, raw resolver rebasing and corrupt-slot rejection."""
from pathlib import Path
from build_z80pack_image import symbols
from private_rsx_rebase import HELPERS, PREFIX
from rsx_container import NAMES
from system_layout import LAYOUT as L
from test_bios import Z80

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/system'


def expected(image,bits,delta):
    data=bytearray(image)
    for offset in range(1012):
        if bits[offset//8] & (1 << (offset%8)):
            value=int.from_bytes(data[offset:offset+2],'little')
            data[offset:offset+2]=((value+delta)&65535).to_bytes(2,'little')
    return bytes(data)


def main():
    labels=symbols(OUT/'r3cache.lst')
    worker=(OUT/'r3cache.bin').read_bytes()
    for delta in (0,-128,-832,192):
        for slot,_stem,_file,_symbol in HELPERS:
            image=(OUT/(NAMES[slot]+'.RSX')).read_bytes()
            bits=worker[labels[f'RB_MAP{slot}']-0x1000:labels[f'RB_MAP{slot}']-0x1000+128]
            cpu=Z80(b'')
            cpu.mem[0x1000:0x1000+len(worker)]=worker
            cpu.mem[0x3000:0x3400]=image
            cpu.setword(L['EXTENSIONS']+0xa3,L['RSX']+delta)
            cpu.setword(labels['CRC'],0xbeef)
            cpu.ix=0x789a
            cpu.hl=0x3000
            cpu.a=slot*8
            cpu.run(labels['REBASE'],limit=300000)
            assert cpu.a==0 and cpu.ix==0x789a
            assert bytes(cpu.mem[0x3000:0x3400])==expected(image,bits,delta)
            assert cpu.word(labels['CRC'])==0xbeef
            # Corruption must be rejected before a single staged fixup.
            damaged=bytearray(image);damaged[1]^=1
            cpu.mem[0x3000:0x3400]=damaged
            cpu.hl=0x3000;cpu.a=slot*8
            cpu.run(labels['REBASE'],limit=300000)
            assert cpu.a and bytes(cpu.mem[0x3000:0x3400])==damaged
            assert cpu.ix==0x789a and cpu.word(labels['CRC'])==0xbeef
        # Real raw resolver prologue rebases once and replaces itself by JP.
        image=(OUT/'rsxresolver.bin').read_bytes()
        bits=image[-128:]
        wanted=expected(image,bits,delta)
        cpu=Z80(b'');base=L['RSX']+delta
        cpu.mem[base:base+len(image)]=image
        cpu.setword(L['EXTENSIONS']+0xa3,base)
        cpu.de=0x6000                     # invalid service ABI, deterministic return
        cpu.ix=0x789a
        cpu.sp=0x7000
        cpu.run(base,limit=100000)
        assert cpu.word(base+1)==base+PREFIX and cpu.mem[base]==0xc3
        assert cpu.ix==0x789a and cpu.sp==0x7000
        for offset in range(len(image)-128):
            if bits[offset//8] & (1 << (offset%8)):
                assert bytes(cpu.mem[base+offset:base+offset+2])==wanted[offset:offset+2]
        before=bytes(cpu.mem[base:base+len(image)])
        cpu.de=0x6000
        cpu.run(base,limit=100000)
        assert bytes(cpu.mem[base:base+len(image)])==before, 'resolver rebased twice'
    print('PASS all private helper maps at default/expanded/disabled-history windows; corrupt-slot rejection; raw resolver rebases exactly once')


if __name__=='__main__':
    main()
