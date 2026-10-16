#!/usr/bin/env python3
"""Execute ADM-3A foundation at multiple load addresses; not full MM qualification."""
import re
from pathlib import Path
from system_layout import LAYOUT
from test_bios import Z80

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/monitor-development'


def symbols(path):
    return {name:int(address,16) for address,name in re.findall(
        r'^([0-9a-f]{4})\s+.*?\b([A-Z][A-Z0-9_]*):',path.read_text(errors='replace'),re.M)}


def bind_backend(cpu, base, table):
    from test_screen_backends import load
    directory=ROOT/'build/screen-backends'
    backend=0x5000
    syms=load(cpu,directory,'M4SCRN',backend)
    cpu.setword(base+12,syms['S_ENTRY']+backend-0x8000)


def set_position(cpu, base, table, bios, address):
    # Directed fixtures set both sides of the portable cursor precondition.
    cpu.setword(bios['M4CURSOR'],address)
    offset=address-0xF800
    cpu.mem[table['AM_ROWPOS']+base-0x8000]=offset//80
    cpu.mem[table['AM_COLPOS']+base-0x8000]=offset%80


def main():
    blob=(OUT/'ADM3A.RSX').read_bytes()
    code=(OUT/'adm3a.bin').read_bytes()
    table=symbols(OUT/'adm3a.lst')
    bios=symbols(ROOT/'build/bios/bios.lst')
    count=int.from_bytes(blob[22:24],'little')
    slots=[int.from_bytes(blob[48+2*i:50+2*i],'little') for i in range(count)]
    for base in [0x6000,0x8101]:
        cpu=Z80((ROOT/'build/bios/bios.bin').read_bytes())
        relocated=bytearray(code)
        for slot in slots:
            value=int.from_bytes(code[slot:slot+2],'little')+base-0x8000
            relocated[slot:slot+2]=value.to_bytes(2,'little')
        cpu.mem[base:base+len(code)]=relocated
        bind_backend(cpu,base,table)
        cpu.setword(1,LAYOUT['BIOS']+3)
        entry=table['AM_ENTRY']+base-0x8000
        def call(op,c=0):
            cpu.a,cpu.c=op,c
            sp=cpu.sp
            cpu.run(entry,limit=15000)
            assert cpu.sp==sp
            return cpu.a
        for row in range(256):
            for col in range(256):
                for char in [27,ord('='),row,col]:call(0,char)
                r=min((row-32)&255,23);c=min((col-32)&255,79)
                assert cpu.word(bios['M4CURSOR'])==0xF800+80*r+c
                assert cpu.mem[bios['M4COLUMN']]==c
        cursor=cpu.word(bios['M4CURSOR'])
        display=bytes(cpu.mem[0xF800:0xFF80])
        for prefix in [b'\x1b',b'\x1b=',b'\x1b=!']:
            for char in prefix:call(0,char)
            call(5)
            assert cpu.mem[table['AM_STATE']+base-0x8000]==0
            assert cpu.word(bios['M4CURSOR'])==cursor
            assert bytes(cpu.mem[0xF800:0xFF80])==display
        for char in b'\x1b0':call(0,char)
        assert call(3)==0
        hidden_screen=bytes(cpu.mem[0xF800:0xFF80])
        hidden_cursor=cpu.word(bios['M4CURSOR'])
        call(3,ord('X'))
        assert cpu.word(bios['M4CURSOR'])==hidden_cursor
        assert bytes(cpu.mem[0xF800:0xFF80])==hidden_screen
        call(5)
        assert call(3)==0
        for char in b'\x1b1':call(0,char)
        assert call(3)==1
        cpu.setword(bios['M4_PENDING'],0xA55A)
        call(4)
        assert cpu.word(bios['M4_PENDING'])==0xA55A
        assert cpu.word(bios['M4CURSOR'])==0xF800
        assert cpu.mem[0xF800:0xFF80]==b' '*1920
        call(0,ord('A'))
        assert cpu.mem[0xF800]==ord('A')
        for char in b'\x1b?':call(0,char)
        assert cpu.word(bios['M4CURSOR'])==0xF801
        assert call(6)==255
    test_utility(code, table, slots, bios)
    print('PASS: development utility preflight, addressing, reset, visual pages, bell and keyboard input')
    print('PASS: 131072 address sequences, relocation, parser reset, cursor visibility, basic clear and raw bypass')


def test_utility(code, table, slots, bios):
    """Run the real utility with controlled BDOS and real provider output."""
    image=(OUT/'ADMTST.COM').read_bytes()
    for available,bad_key in [(False,False),(True,False),(True,True)]:
        cpu=Z80((ROOT/'build/bios/bios.bin').read_bytes())
        cpu.mem[256:256+len(image)]=image
        cpu.setword(1,LAYOUT['BIOS']+3)
        cpu.mem[0]=0xC3
        cpu.mem[LAYOUT['BIOS']+3:LAYOUT['BIOS']+6]=bytes.fromhex('c3ffff')
        cpu.mem[5:8]=bytes.fromhex('d3fec9')
        base=0x6000
        relocated=bytearray(code)
        for slot in slots:
            value=int.from_bytes(code[slot:slot+2],'little')+base-0x8000
            relocated[slot:slot+2]=value.to_bytes(2,'little')
        cpu.mem[base:base+len(code)]=relocated
        bind_backend(cpu,base,table)
        entry=table['AM_ENTRY']+base-0x8000
        output=bytearray()
        pauses=[]
        answers=iter(b'    X' if bad_key else b'    A:[]')
        pulses=[]
        def emit(char):
            saved={k:getattr(cpu,k) for k in ['a','b','c','d','e','h','l','pc','z','carry']}
            cpu.a,cpu.c=0,char
            cpu.run(entry,limit=120000)
            for k,v in saved.items():setattr(cpu,k,v)
        def bdos(port,value):
            if port&255==0x90:
                pulses.append(value)
                return
            assert port&255==254
            if cpu.c==182:
                assert bytes(cpu.mem[cpu.de+4:cpu.de+10])==b'MCON\x01\x00'
                cpu.setword(cpu.de+12,entry)
                cpu.a=0 if available else 255
            elif cpu.c==6:
                output.append(cpu.e)
                if available:emit(cpu.e)
            elif cpu.c==1:
                pauses.append(bytes(cpu.mem[0xF800:0xFF80]))
                cpu.a=next(answers)
            else:raise AssertionError(f'unexpected BDOS function {cpu.c}')
        cpu.port_write=bdos
        cpu.run(256,limit=150000)
        if available and bad_key:
            assert len(pauses)==5
            assert b'Keyboard mismatch.' in output
            assert b'ADMTST keyboard checks passed.' not in output
        elif available:
            assert len(pauses)==8
            assert pauses[0][410:].startswith(b'Marker: row 5, column 10 (zero-based).'), repr(pauses[0][400:480])
            assert b'Parser reset: this text should remain readable.' in pauses[1]
            assert bytes(cpu.mem[0xF800:0xFF80]).startswith(b'ADMTST keyboard checks passed.')
            assert len(pulses)==51200
            assert pauses[2][160:164]==b'LEFT',repr(pauses[2])
            assert pauses[2][248:250]==b'AB'
            assert pauses[2][320:325]==b'RIGHT'
            assert pauses[3][800:806]==b'LINE A'
            assert pauses[3][880:960]==b' '*80
            assert pauses[3][960:966]==b'LINE C'
            assert pauses[3][1040:1046]==b'LINE D'
            assert cpu.mem[table['AM_STATE']+base-0x8000]==0
        else:
            assert not pauses
            assert output.startswith(b'No MCON provider loaded.')


if __name__=='__main__':main()
