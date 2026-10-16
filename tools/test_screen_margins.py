#!/usr/bin/env python3
"""Execute bounded-region index, reverse index and wrapping on actual carriers."""
import pyte
from test_screen_backends import fixture,ROOT
from test_vt52_foundation import symbols


def main():
    m4=symbols(ROOT/'build/bios/bios.lst');cases=0
    for name in ('M4SCRN','ANSISCRN'):
        for base in (0x6000,0x8101):
            for width,height in ([(80,24)] if name=='M4SCRN' else [(80,24),(80,25),(100,40)]):
                cpu,old,cells,wire=fixture(name,base,cpmsim_bios=ROOT/'build/audit/release-090-z80pack')
                screen=pyte.Screen(width,height);stream=pyte.Stream(screen)
                if name=='ANSISCRN':
                    def emit(port,value):
                        assert port&255==1
                        wire.append(value);stream.feed(chr(value))
                    cpu.port_write=emit
                def call(op,b=0,c=0,hl=0,de=0):
                    cpu.a,cpu.b,cpu.c,cpu.hl,cpu.de=op,b,c,hl,de
                    sp=cpu.sp;cpu.run(cpu.backend_entry,limit=300000)
                    assert cpu.sp==sp
                    return cpu.a
                def grid():
                    return bytes(cpu.mem[0xF800:0xFF80]) if name=='M4SCRN' else ''.join(screen.display).encode()
                def cursor():
                    return (cpu.mem[m4['M4COLUMN']],(cpu.word(m4['M4CURSOR'])-0xF800)//80) if name=='M4SCRN' else (screen.cursor.x,screen.cursor.y)
                for top,bottom in [(0,height-1),(1,2),(3,height-3),(height-2,height-1)]:
                    for row in sorted(set([top,bottom,(top+bottom)//2])):
                        for op in (0,1,2,3):
                            for reverse in (0,32):
                                reference=pyte.Screen(width,height);ref=pyte.Stream(reference)
                                fill='\x1b[0m'+''.join(f'\x1b[{y+1};1H'+chr(65+y%26)*width for y in range(height))
                                ref.feed(fill)
                                if name=='M4SCRN':cpu.mem[0xF800:0xFF80]=b''.join(bytes([65+y%26])*80 for y in range(24))
                                else:stream.feed(fill)
                                cpu.mem[0x4000:0x4009]=bytes([reverse]+[0]*8)
                                assert call(20,hl=0x4000)==0
                                ref.feed('\x1b[0m'+('\x1b[7m' if reverse else ''))
                                assert call(22,hl=top+1,de=bottom+1)==0
                                ref.feed(f'\x1b[{top+1};{bottom+1}r')
                                assert cursor()==(0,0)
                                col=width-1 if op==3 else 7
                                assert call(18,hl=row+1,de=col+1)==0
                                ref.feed(f'\x1b[{row+1};{col+1}H')
                                if op==3:
                                    assert call(21,c=ord('X'))==0
                                    assert call(21,c=ord('Y'))==0
                                    ref.feed('XY')
                                else:
                                    assert call(24,b=op)==0
                                    ref.feed(['\x1bD','\r\x1bD','\x1bM'][op])
                                expected=''.join(reference.display).encode()
                                assert bytes(v&127 for v in grid())==expected,(name,top,bottom,row,op)
                                assert cursor()==(reference.cursor.x,reference.cursor.y),(name,top,bottom,row,op,cursor(),reference.cursor)
                                if name=='M4SCRN':
                                    for y in range(height):
                                        for x in range(width):
                                            expected_reverse=reference.buffer[y][x].reverse
                                            # pyte creates default-attribute rows on index;
                                            # Model 4 explicitly paints canonical blank cells.
                                            blankrow=top if op==2 and row==top else bottom if op in (0,1,3) and row==bottom else None
                                            if y==blankrow and reference.buffer[y][x].data==' ':expected_reverse=bool(reverse)
                                            assert bool(grid()[y*width+x]&128)==expected_reverse,(top,bottom,row,op,y,x)
                                cases+=1
                if name=='M4SCRN':
                    # Index outside the region moves within physical bounds;
                    # it must not snap an outlying cursor into the margins.
                    assert call(22,hl=4,de=20)==0
                    for row,op,wanted in [(0,2,0),(1,2,0),(22,0,23),(23,0,23)]:
                        assert call(18,hl=row+1,de=8)==0
                        before=grid();assert call(24,b=op)==0
                        assert cursor()==(7,wanted) and grid()==before
                before=grid();n=len(wire)
                for top,bottom in [(2,2),(3,2),(65535,1)]:assert call(22,hl=top,de=bottom)==255
                for op in (3,255):assert call(24,b=op)==255
                assert grid()==before and len(wire)==n
                assert call(22,hl=0,de=0)==0 and cursor()==(0,0)
                print(f'PASS {name} {base:04X} {width}x{height}: margins/index/wrap, preserved outer rows, styled fills')
    print(f'PASS {cases} margin/index cases plus atomic rejection/default reset checks')


if __name__=='__main__':main()
