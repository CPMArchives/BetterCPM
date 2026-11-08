#!/usr/bin/env python3
"""Execute fresh personality activation and the CCP return newline."""
import ctypes as C
import shutil
import subprocess
from pathlib import Path
from build_ccp import assemble
from build_integrated_display import source
from build_z80pack_image import symbols
from test_usq import SHIM

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/personality-activation-test'
OUT.mkdir(parents=True, exist_ok=True)
core = Path.home() / 'projects/git/z80pack/z80core'
cpuout = OUT / 'cpu'
cpuout.mkdir(exist_ok=True)
(cpuout/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
for name in ('simmem.h', 'simport.h'):
    shutil.copy2(core.parent/'z80sim/srcsim'/name, cpuout/name)
shim = SHIM.replace('void io_out(BYTE l, BYTE h, BYTE d) {}',
    'unsigned wirelen; BYTE wire[65536];\n'
    'void io_out(BYTE l, BYTE h, BYTE d) { if(l==1 && wirelen<65536)wire[wirelen++]=d; }')
(cpuout/'shim.c').write_text(shim)
subprocess.run(['cc','-shared','-fPIC','-O2',f'-I{cpuout}',f'-I{core}',
    str(cpuout/'shim.c'),str(core/'simglb.c'),*map(str,sorted(core.glob('simz80*.c'))),
    '-o',str(cpuout/'core.so')],check=True)
lib = C.CDLL(str(cpuout/'core.so'))

class Native:
    def __init__(self):
        self.mem = (C.c_ubyte*65536).in_dll(lib,'memory')
        C.memset(self.mem,0,65536)
        C.c_ushort.in_dll(lib,'SP').value=0x7000
        self.length=C.c_uint.in_dll(lib,'wirelen')
        self.length.value=0
        self.output=(C.c_ubyte*65536).in_dll(lib,'wire')
    def word(self,at):
        return self.mem[at] | self.mem[at+1]<<8
    def setword(self,at,value):
        self.mem[at:at+2]=value.to_bytes(2,'little')
    def run(self,entry,limit):
        result=lib.test_run(entry,limit)
        assert result>=0,result

for platform in ('cpmsim', 'model4', 'model2'):
    for personality in ('ADM3A', 'VT52', 'ANSI'):
        host = platform == 'cpmsim'
        prefix = 'M2BANK EQU %d\nCRT_POS EQU 06000H\nCRT_COL EQU 06002H\n' % (platform == 'model2')
        text = prefix + source(personality, 'host' if host else 'crt')
        key = platform + '-' + personality
        code = assemble(Path.home() / 'bin/z80asm', text,
                        OUT / (key+'.bin'), OUT / (key+'.lst'), 0x8000)
        table = symbols(OUT / (key+'.lst'))
        m = Native()
        m.mem[0x8000:0x8000+len(code)] = code
        screen = b''.join(bytes([65+row])*80 for row in range(24))
        m.mem[0xf800:0xf800+1920] = screen
        m.setword(0x6000, 0xf800+5*80+17)
        m.mem[0x6002] = 17
        m.run(table['D_ACTIVATE'], limit=10000)
        assert bytes(m.mem[0xf800:0xf800+1920]) == screen, key
        wire = bytes(m.output[:m.length.value])
        if host:
            assert wire == b'\x1b[24;1H', (key, wire)
            assert m.word(table['H_RC']) == 23, key
        else:
            assert m.word(0x6000) == 0xf800+23*80 and m.mem[0x6002] == 0, key
        # A load entered on the bottom row must have the same outcome.
        if host:
            m.setword(table['H_RC'], (17 << 8) | 23)
        else:
            m.setword(0x6000, 0xf800+23*80+17)
            m.mem[0x6002] = 17
        m.run(table['D_ACTIVATE'], limit=10000)
        assert bytes(m.mem[0xf800:0xf800+1920]) == screen, key
        m.length.value=0
        for char in (13, 10):
            C.c_ubyte.in_dll(lib,'C').value=char
            m.run(table['D_OUTPUT'], limit=100000)
        wire = bytes(m.output[:m.length.value])
        if host:
            assert m.word(table['H_RC']) == 23, key
            assert b'\x1b[2J' not in wire and b'\x1b[J' not in wire, (key, wire)
            assert b'\n' in wire or b'\x1b[1M' in wire or b'\x1bD' in wire, (key, wire)
        else:
            assert bytes(m.mem[0xf800:0xf800+23*80]) == screen[80:], key
            assert bytes(m.mem[0xf800+23*80:0xf800+1920]) == b' '*80, key
            assert m.word(0x6000) == 0xf800+23*80 and m.mem[0x6002] == 0, key
        # Ordinary cursor-home behavior remains separate from activation.
        m.run(table['D_HOME'], limit=10000)
        assert (m.word(table['H_RC']) == 0 if host else m.word(0x6000) == 0xf800), key
        print('PASS', key, 'bottom activation, return scroll, screen retention, explicit home')
