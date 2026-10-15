#!/usr/bin/env python3
"""Verify the starter, a changed profile, and rejection of bad sequence counts."""
import argparse
import tempfile
from pathlib import Path
from build_monitor_template import build,TEMPLATE
from test_vt52_foundation import symbols
from test_bios import Z80


def exercise(out,bios_path,expected):
    syms=symbols(out/'monitor.lst');bios=symbols(bios_path/'bios.lst')
    code=(out/'monitor.bin').read_bytes();carrier=(out/'MONDEMO.RSX').read_bytes()
    count=int.from_bytes(carrier[22:24],'little')
    slots=[int.from_bytes(carrier[48+2*i:50+2*i],'little') for i in range(count)]
    for base in (0x6000,0x8101):
        c=Z80(b'');origin=bios['MONRAW']-69;data=(bios_path/'bios.bin').read_bytes()
        c.mem[origin:origin+len(data)]=data;c.setword(1,origin+3)
        image=bytearray(code)
        for offset in slots:image[offset:offset+2]=(int.from_bytes(code[offset:offset+2],'little')+base-0x8000).to_bytes(2,'little')
        c.mem[base:base+len(image)]=image;entry=syms['TP_ENTRY']+base-0x8000
        emitted=[];c.port_write=lambda port,value:emitted.append(value)
        c.port_read=lambda port:1 if port&255==0 else ord('a')
        def call(op,char=0):
            stack=c.sp;c.a,c.c=op,char;c.run(entry,limit=10000);assert c.sp==stack
            return c.a
        def send(data):
            emitted.clear()
            for char in data:call(0,char)
            return bytes(emitted)
        assert send(b'Text\r\n')==b'Text\r\n'
        assert send(b'\x00\x7f')==b''
        assert send(b'\x1bH')==expected
        assert send(b'\x1b?X')==b'X'
        assert send(b'\x1b\x1bH')==expected
        assert send(b'\x1b')==b'';call(5);assert send(b'H')==b'H'
        emitted.clear();call(4);assert bytes(emitted)==b'\x1b[2J\x1b[H'
        assert send(b'\x0c')==b'\x1b[2J\x1b[H'
        assert call(1)==255 and call(2)==ord('a')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bios',type=Path,required=True)
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='monitor-template-') as tmp:
        tmp=Path(tmp);out=tmp/'default'
        build(a.assembler,TEMPLATE/'host.mac',TEMPLATE/'ansi-demo.inc','MONDEMO',out)
        exercise(out,a.bios,b'\x1b[H')
        profile=tmp/'custom.inc'
        profile.write_text((TEMPLATE/'ansi-demo.inc').read_text().replace("DB 'H',3,27,'[H'","DB 'H',2,'!',0"))
        out=tmp/'custom';build(a.assembler,TEMPLATE/'host.mac',profile,'MONDEMO',out)
        exercise(out,a.bios,b'!\x00')
        profile.write_text(profile.read_text().replace("DB 'H',2,'!',0","DB 'H',9,'!',0"))
        try:build(a.assembler,TEMPLATE/'host.mac',profile,'MONDEMO',tmp/'bad')
        except ValueError:pass
        else:raise AssertionError('bad profile count accepted')
    print('PASS: two profiles at two load addresses, counted binary output, clear/reset/input and malformed-table rejection')


if __name__=='__main__':main()
