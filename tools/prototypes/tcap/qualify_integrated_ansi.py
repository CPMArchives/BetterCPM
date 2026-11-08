"""Compare the combined ANSI controller with the existing executable ANSI stack.

Both implementations run on the real Z80 CPU core. Compare cells, attributes,
logical cursor, wrap, partial-sequence isolation, margins and public operations.
"""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import random
import re
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
import pyte
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_integrated_display import source
from build_z80pack_image import symbols
from test_model2_screen import cpu_library
from test_screen_backends import fixture,load
from test_usq import SHIM


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference-workspace',type=Path,default=ROOT)
    p.add_argument('--cpmsim-bios',type=Path,required=True)
    a=p.parse_args();reference=a.reference_workspace.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    cpudir=out/'cpu';cpudir.mkdir()
    shim=SHIM.replace('void io_out(BYTE l, BYTE h, BYTE d) {}',
        'BYTE wire[65536]; unsigned wirelen,badport,low_sp;\n'
        'void io_out(BYTE l,BYTE h,BYTE d){if(l==1){if(wirelen<65536)wire[wirelen++]=d;}else if(l!=0x90)badport++;}')
    shim=shim.replace('cpu_error=0; tmax=100000000;','cpu_error=0; tmax=100000000; low_sp=SP;')
    shim=shim.replace('if(PC==65535) return i;','if(SP<low_sp)low_sp=SP; if(PC==65535) return i;')
    lib=cpu_library(cpudir,Path.home()/'projects/git/z80pack',shim)
    mem=(C.c_ubyte*65536).in_dll(lib,'memory');wire=(C.c_ubyte*65536).in_dll(lib,'wire')
    nwire=C.c_uint.in_dll(lib,'wirelen');sp=C.c_ushort.in_dll(lib,'SP');low=C.c_uint.in_dll(lib,'low_sp')
    regs={k:C.c_ubyte.in_dll(lib,k) for k in 'ABCDEHL'}
    assembler=Path.home()/'bin/z80asm';checks=0;cases=[];maxstack=0
    colors=dict(zip(('black','red','green','brown','blue','magenta','cyan','white'),
        ('000000','cd0000','00cd00','cdcd00','0000ee','cd00cd','00cdcd','e5e5e5')))
    colors.update(dict(zip(('brightblack','brightred','brightgreen','brightbrown','brightblue','brightmagenta','brightcyan','brightwhite'),
        ('7f7f7f','ff0000','00ff00','ffff00','5c5cff','ff00ff','00ffff','ffffff'))))
    colors['bfightmagenta']='ff00ff'  # Installed pyte's SGR-105 spelling.
    def normalize(char):
        # Foreground color on a plain, non-reversed space has no rendered pixels.
        fg='default' if char.data==' ' and not (char.reverse or char.underscore or char.strikethrough) else colors.get(char.fg,char.fg)
        return char._replace(fg=fg,bg=colors.get(char.bg,char.bg))
    import test_screen_backends
    test_screen_backends.OUT=reference/'build/screen-backends'
    bios=symbols(reference/'build/bios/bios.lst')
    for backend in ('crt','host'):
        folder=out/backend;folder.mkdir()
        text=('M2BANK EQU 0\nCRT_POS EQU 0%04XH\nCRT_COL EQU 0%04XH\n'%(bios['M4CURSOR'],bios['M4COLUMN']))+source('ANSI',backend)
        code=assemble(assembler,text,folder/'native.bin',folder/'native.lst',0x8000)
        alt=assemble(assembler,text.replace('08000H','08101H'),folder/'alt.bin',folder/'alt.lst',0x8101)
        labels=symbols(folder/'native.lst');fixes=relocation_offsets(code,alt,0x101)
        for base in (0x9000,0xa001):
            old,_,_,_=fixture('M4SCRN' if backend=='crt' else 'ANSISCRN',0x4000,model4_bios=reference/'build/bios',cpmsim_bios=a.cpmsim_bios.resolve())
            oldlabels=load(old,reference/'build/ansi-development','ansi',0x6000)
            old.setword(0x600c,old.backend_entry)
            images=[bytearray(old.mem),bytearray(old.mem)]
            patch=bytearray(code)
            for at in fixes:patch[at:at+2]=(int.from_bytes(patch[at:at+2],'little')+base-0x8000).to_bytes(2,'little')
            images[1][base:base+len(patch)]=patch
            entries=[oldlabels['AN_ENTRY']-0x8000+0x6000,labels['D_ENTRY']-0x8000+base]
            screens=[pyte.Screen(80,24),pyte.Screen(80,24)];streams=[pyte.Stream(s) for s in screens]
            def invoke(which,op,c=0,b=0,portable=False):
                nonlocal checks,maxstack
                C.memmove(C.addressof(mem),(C.c_ubyte*65536).from_buffer(images[which]),65536)
                regs['A'].value,regs['B'].value,regs['C'].value=op,b,c
                regs['D'].value,regs['E'].value=0x53,0x79
                sp.value=0x3000;nwire.value=0
                entry=labels['D_TCAP']+base-0x8000 if portable else entries[which]
                result=lib.test_run(entry,2000000)
                assert result>=0 and sp.value==0x3000,(backend,which,op,c,result,hex(sp.value))
                if which:maxstack=max(maxstack,0x3000-low.value)
                assert C.c_uint.in_dll(lib,'badport').value==0
                if backend=='host':
                    packet=bytes(wire[:nwire.value])
                    # SCX defines omitted bottom as the endpoint's full height.
                    # Installed pyte treats any omitted margin as a full reset;
                    # make that 80x24 endpoint default explicit for the reference.
                    if which==0:packet=re.sub(rb'\x1b\[(\d+);r',lambda m:b'\x1b['+m.group(1)+b';24r',packet)
                    streams[which].feed(packet.decode('latin1'))
                images[which][:]=bytes(mem);checks+=1
                return regs['A'].value,bytes(wire[:nwire.value])
            def equal(context):
                if backend=='crt':
                    cells=[bytes(i[0xf800:0xff80]) for i in images]
                    assert cells[0]==cells[1],(backend,context,[(i,a,b) for i,(a,b) in enumerate(zip(*cells)) if a!=b][:8])
                else:
                    logical=tuple(images[1][labels['H_RC']+base-0x8000:labels['H_RC']+base-0x8000+2])
                    assert logical==(screens[1].cursor.y,min(79,screens[1].cursor.x)),('logical',context,logical,screens[1].cursor.y,screens[1].cursor.x)
                    for r in range(24):
                        for c in range(80):
                            assert normalize(screens[0].buffer[r][c])==normalize(screens[1].buffer[r][c]),(backend,context,r,c,screens[0].buffer[r][c],screens[1].buffer[r][c])
                    assert (screens[0].cursor.y,screens[0].cursor.x)==(screens[1].cursor.y,screens[1].cursor.x),(context,[(s.cursor.y,s.cursor.x,s.margins) for s in screens],{k:images[1][labels[k]+base-0x8000] for k in ('A_TOP','A_BOTTOM','A_P1','A_P2')})
            def send(data,context='stream'):
                for at,c in enumerate(data):
                    for i in (0,1):invoke(i,0,c)
                    equal((context,at,c))
            for i in (0,1):invoke(i,4)
            equal('clear')
            send(b'\x1b[0m\x1b[r')
            for row in range(24):send(f'\x1b[{row+1};1H'.encode()+bytes((65+row,))*80,('fill',row))
            for position in ((1,1),(1,80),(24,1),(24,80),(12,40)):
                for command in (b'1A',b'2B',b'3C',b'4D',b'0A',b'65535C',b'0J',b'1J',b'2J',b'0K',b'1K',b'2K'):
                    send(('\x1b[%d;%dH'%position).encode()+b'\x1b['+command,('position',position,command))
            send(b'\x1b[0m\x1b[r\x1b[H'+b'A'*81+b'\bB\rC\nDE')
            send(b'\x1b[3;1HAAA\x1b[4;1HBBB\x1b[5;1HCCC\x1b[3;5r\x1b[5;1H\x1bD\x1b[3;1H\x1bM\x1bE')
            # SGR, full foreground/background colors, conceal and reusable saves.
            for sgr in (b'7',b'27',b'8',b'28',b'1;3;4;5;7',b'22;23;24;25;27',b'31;44',b'38;5;196;48;5;21',b'38;2;10;128;250;48;2;8;9;10',b'39;49',b'0'):
                send(b'\x1b['+sgr+b'mX',('sgr',sgr))
            for sgr in list(range(10))+list(range(22,30))+list(range(30,38))+list(range(40,48))+[39,49]+list(range(90,98))+list(range(100,108)):
                send(('\x1b[0m\x1b[%dmX'%sgr).encode(),('rendition',sgr))
            send(b'\x1b[r\x1b[1;7;38;2;10;128;250m\x1b[10;20H\x1b7\x1b[0m\x1b[2;2H\x1b8R\x1b8S\x1b[s\x1b[0m\x1b[1;1H\x1b[uT')
            for bad in (b'1;38;5',b'0;38;2;1;2',b'1;38;2;256;0;0',b'0;48;3;5',b'65536',b';'*16):
                send(b'\x1b['+bad+b'mQ',('bad-sgr',bad))
            for seq in (b'\x1b[6n',b'\x1b[c',b'\x1b[?7h',b'\x1b[?1049h',b'\x1b]title\x07',b'\x1bPdata\x1b\\',b'\x1bc',b'\x1b[3J',b'\x1b[1;2;3H',b'\x1b[2;3A',b'\x1b[1;2K'):
                send(seq,('refuse',seq))
            for n in list(range(41))+[64,255,1000]:
                send(b'\x1b['+b'1'*n+b'm',('bounded',n))
            for prefix in (b'\x1b',b'\x1b[',b'\x1b[12;',b'\x1b[?25',b'\x1b]title',b'\x1bPdata'):
                for i in (0,1):invoke(i,5)
                before=[bytes(i[0xf800:0xff80]) for i in images]
                wires=[b'',b'']
                for c in prefix:
                    for i in (0,1):wires[i]+=invoke(i,0,c)[1]
                assert wires==[b'',b''] and before==[bytes(i[0xf800:0xff80]) for i in images],prefix
                for i in (0,1):invoke(i,5)
                send(b'\x1b[0m\x1b[r\x1b[HX')
            send(b'\x1b[12\x18\x1b[12\x1a\x1b[12\x1b[H')
            rng=random.Random(20261108)
            for _ in range(200):
                command=rng.choice(('A','B','C','D','H','f','J','K','r','m'))
                param=str(rng.randrange(100)) if command not in 'Hfr' else '%d;%d'%(rng.randrange(30),rng.randrange(90))
                send(('\x1b['+param+command+'TEXT').encode(),('random',command,param))
            # Public operations must reject invalid positions without mutation,
            # use normal/reverse emphasis, and retain fact-query BC/DE.
            for op in (6,1,4,3,5,7):assert invoke(1,op,portable=True)[0]==0
            for b,c in ((24,0),(0,80),(255,255)):
                before=bytes(images[1]);assert invoke(1,2,c,b,True)[0]==3
                assert images[1][0xf800:0xff80]==before[0xf800:0xff80]
            assert invoke(1,0,0x39,0x27,True)[0]==0
            assert (regs['B'].value,regs['C'].value,regs['D'].value,regs['E'].value)==(0x27,0x39,0x53,0x79)
            for op in (8,255):assert invoke(1,op,portable=True)[0]==255
            # MCON 3 follows Function 178: reverse presentation advances like
            # ordinary output, with the personality and renderer kept together.
            assert invoke(1,1,portable=True)[0]==0
            assert invoke(1,2,3,2,True)[0]==0
            before=bytes(images[1][0xf800:0xff80])
            if backend=='host':
                assert invoke(1,3)[0]==0 and invoke(1,3,ord('X'))[0]==0
                assert bytes(images[1][0xf800:0xff80])==before
            else:
                assert invoke(1,3)[0]==1
                assert invoke(1,3,ord('X'))[0]==1
                assert (regs['D'].value,regs['E'].value)==(0x53,0x79)
                assert images[1][0xf800+163]==(ord('X')|128)
                ptr=int.from_bytes(images[1][bios['M4CURSOR']:bios['M4CURSOR']+2],'little')
                assert ptr==0xf800+164 and images[1][bios['M4COLUMN']]==4
                assert invoke(1,2,79,2,True)[0]==0
                assert invoke(1,3,ord('Y'))[0]==1
                invoke(1,0,ord('Z'))
                assert images[1][0xf800+239]==(ord('Y')|128) and images[1][0xf800+240]==ord('Z')
                for c in b'\x1b[?25l':invoke(1,0,c)
                before=bytes(images[1][0xf800:0xff80])
                assert invoke(1,3)[0]==0 and invoke(1,3,ord('Q'))[0]==0
                assert bytes(images[1][0xf800:0xff80])==before
            cases.append({'backend':backend,'base':base,'payload_bytes':len(code),'relocation_words':len(fixes),'payload_sha256':hashlib.sha256(code).hexdigest()})
    assert maxstack<=32,maxstack
    report={'status':'PASS combined ANSI CPU differential and public operations','checks':checks,'cases':cases,'maximum_external_stack_bytes':maxstack,'scope':'fixed 80x24 seven-bit ANSI; historical eight-bit raw-BIOS bypass is outside the terminal protocol; real boot/install are separate gates'}
    (out/'qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
