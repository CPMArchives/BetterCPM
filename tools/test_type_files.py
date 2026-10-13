#!/usr/bin/env python3
"""Exercise TYPE page-anchor file jumps, empty files and mixed navigation."""
import re
from pathlib import Path
from test_type_streaming import run
ROOT=Path(__file__).resolve().parents[1]

def main():
    listing=(ROOT/'build/utilities/type.lst').read_text()
    def addr(name):return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
    a=(1,3,b'A       TXT');b=(1,3,b'B       TXT');c=(1,3,b'C       TXT')
    def rows(name,n):return b''.join(f'{name} ROW {i:02d}\r\n'.encode() for i in range(n))+b'\x1a'
    anchor=addr('TP_ANCH');begin=addr('TP_BEGIN');observed=[]
    def observe(cpu,service):
        if service==6:observed.append((bytes(cpu.mem[anchor:anchor+13]),cpu.mem[begin]))
    files={c:(rows('C',30),2),b:(rows('B',50),1),a:(rows('A',5),0)}
    out,_=run('/P B3:*.TXT',files,responses='><.<<>>\x11',observe=observe)
    assert [value[0] for value in observed]==[bytes((1,3))+k[2] for k in (a,b,a,b,b,a,b,c)],observed
    assert [value[1] for value in observed]==[1,1,1,0,1,1,1,1],observed
    assert out.count('B ROW 00')==6 and out.count('A ROW 00')==3,out
    observed.clear()
    out,_=run('/P B3:*.TXT',files,responses='>\x12>. ,\x11'.replace(' ',''),observe=observe)
    assert [value[0] for value in observed]==[bytes((1,3))+k[2] for k in (a,b,a,b,b,b)],observed
    assert observed[-1][1]==1,'previous page after a file jump did not return to its beginning'
    # Near the start of B, < moves only back to its banner, not 23 rows into A.
    observed.clear()
    out,_=run('/P B3:*.TXT',{a:(rows('A',17),0),b:(rows('B',50),0)},responses='.<\x11',observe=observe)
    assert observed[1][0]==bytes((1,3))+b[2] and observed[1][1]==0,observed
    assert observed[2][0]==bytes((1,3))+b[2] and observed[2][1]==1,observed
    last_repaint=out.split('\x1c')[-1]
    assert last_repaint.startswith('---------- B3:B.TXT ----------') and 'A ROW' not in last_repaint,last_repaint
    empty=(1,3,b'EMPTY   TXT');last=(1,3,b'ZLAST   TXT')
    observed.clear()
    out,_=run('/P B3:*.TXT',{a:(rows('A',30),0),empty:(b'',4),last:(rows('LAST',50),0)},responses='>><\x11',observe=observe)
    assert [value[0] for value in observed]==[bytes((1,3))+k[2] for k in (a,empty,last,empty)],observed
    assert '[EMPTY]' not in out and 'B3:EMPTY.TXT' in out
    # Final EOF does not hide later anchored boundaries, including empty files.
    observed.clear()
    out,_=run('/P B3:*.TXT',{a:(rows('A',1),0),b:(b'',4),c:(rows('C',1),0)},responses='>>><<\x11',observe=observe)
    assert [value[0] for value in observed]==[bytes((1,3))+k[2] for k in (a,b,c,c,b,a)],observed
    assert out.count('\x07')==1,out
    # A boundary jump clears/homes, then starts with the banner itself.
    repaints=out.split('\x1c')
    assert repaints[2].startswith('---------- B3:B.TXT ----------'),repaints[2]
    assert repaints[3].startswith('---------- B3:C.TXT ----------'),repaints[3]
    # Across drives/user areas, next-file navigation follows the selected sequence.
    d=(2,5,b'D       TXT');observed.clear()
    run('/P [B3,C5]:*.TXT',{a:(rows('A',30),0),d:(rows('D',30),0)},responses='><\x11',observe=observe)
    assert [value[0] for value in observed]==[bytes((k[0],k[1]))+k[2] for k in (a,d,a)],observed
    # Bounds do not create phantom files or require an error prompt.
    out,_=run('/P B3:A.TXT',{a:(rows('A',30),0)},responses='<>\x11')
    assert out.count('A ROW 00')==1 and out.count('\x07')==2,out
    # Row anchors must borrow/carry across byte boundaries, without a 255-row limit.
    from test_bios import Z80
    binary=(ROOT/'build/utilities/TYPE.COM').read_bytes()
    for value in (0,16,23,258,65536,0xFFFFFFFF):
        cpu=Z80(b'');cpu.mem[0x100:0x100+len(binary)]=binary
        pointer=addr('TP_TARG');cpu.mem[pointer:pointer+4]=value.to_bytes(4,'little')
        cpu.run(addr('TP_SUB23'),limit=10000)
        assert int.from_bytes(cpu.mem[pointer:pointer+4],'little')==max(0,value-23),value
    for value in (255,65535,0xFFFFFF):
        cpu=Z80(b'');cpu.mem[0x100:0x100+len(binary)]=binary
        pointer=addr('TP_CUR');cpu.mem[pointer:pointer+4]=value.to_bytes(4,'little')
        cpu.run(addr('TP_GLOBAL'),limit=10000)
        assert int.from_bytes(cpu.mem[pointer:pointer+4],'little')==value+1,value
    print('PASS: TYPE anchor-based file jumps, current/previous behavior, row replay, empty files, DU sequence and bounds')
if __name__=='__main__':main()
