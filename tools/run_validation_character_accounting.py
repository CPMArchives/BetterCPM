#!/usr/bin/env python3
"""Bounded production BDOS/BIOS instruction oracles for documentary I/O cards.

Synthetic BIOS/port endpoints observe bytes and call ordering. This does not
claim physical printer/UART operation or human terminal observations.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build-root','cpmsim-build','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(a.build_root/'tools'))
    from test_bios import Z80
    from test_unified_bdos import symbols
    from system_layout import LAYOUT
    s=symbols();cpu=Z80(b'');image=a.build_root/'build/bdos/bdos.bin';cpu.mem[LAYOUT['BDOS']:LAYOUT['BDOS']+image.stat().st_size]=image.read_bytes();cpu.sp=0xB000
    q=[];wire=[];printer=[];reader=[];calls=[];checks=[];resume=None
    def read(port):
        nonlocal resume
        port &=255;calls.append(('in',port))
        if port==0x31:return 255 if q else 0
        if port==0x32:
            assert q,'unexpected blocking input'
            if resume is not None and len(q)==1:
                assert wire==[], 'formatted output escaped before resume key'
                resume=True
            return q.pop(0)
        if port==0x34:return reader.pop(0)
        raise AssertionError(port)
    def write(port,value):
        port &=255;calls.append(('out',port,value));(wire if port==0x30 else printer).append(value)
    cpu.port_read,cpu.port_write=read,write
    for offset,code in ((6,bytes((0xDB,0x31,0xC9))),(9,bytes((0xDB,0x32,0xC9))),(12,bytes((0x79,0xD3,0x30,0xC9))),(15,bytes((0x79,0xD3,0x33,0xC9))),(18,bytes((0x79,0xD3,0x35,0xC9))),(21,bytes((0xDB,0x34,0xC9)))):
        target=0x9C00+offset*8;cpu.mem[target:target+len(code)]=code;cpu.mem[LAYOUT['BIOS']+offset:LAYOUT['BIOS']+offset+3]=bytes((0xC3,target&255,target>>8))
    def call(fn,arg=0):
        cpu.c,cpu.de,cpu.ix=fn,arg,0xA55A;cpu.run(LAYOUT['BDOS'],limit=100000);assert cpu.sp==0xB000 and cpu.ix==0xA55A;return cpu.a
    def reset(column=0):
        nonlocal resume
        q.clear();wire.clear();printer.clear();calls.clear();resume=None
        for label in ('UB_PENDING','UB_LISTE','UB_COLUMN'):cpu.mem[s[label]]=0
        cpu.mem[s['UB_COLUMN']]=column
    def text(value):cpu.mem[0x9200:0x9200+len(value)]=value;return 0x9200
    reset();call(2,ord('A'));call(9,text(b'B\tC$ignored'));assert bytes(wire)==b'AB'+b' '*6+b'C' and cpu.mem[s['UB_COLUMN']]==9;checks.append('Functions 2/9 share cooked state and dollar termination')
    for fn in (2,9):
        for col in (0,1,7,8,15,79):
            reset(col);call(fn,9 if fn==2 else text(b'\t$'));assert wire==[32]*(8-col%8)
        reset();q[:]=[19,ord('X')];resume=False;call(fn,ord('A') if fn==2 else text(b'ABC$'));assert resume and not q and bytes(wire)==(b'A' if fn==2 else b'ABC')
    checks.append('TAB at six columns and Ctrl-S resume precedes output for both formatted functions')
    reset();q[:]=[16,ord('A')];assert call(1)==ord('A');call(2,9);call(9,text(b'B$'));assert wire==printer and bytes(wire)==b'A'+b' '*7+b'B';checks.append('Ctrl-P enables identical Function-1/2/9 echo including expanded spaces')
    for value in (0,7,9,16,19,32,65,126,127,128,254):
        reset(3);cpu.mem[s['UB_LISTE']]=255;q[:]=[19];assert call(6,value)==0;assert wire==[value] and printer==[] and q==[19] and not any(x[0]=='in' for x in calls);assert cpu.mem[s['UB_COLUMN']]==3
    checks.append('Direct output preserves bytes, column, queued Ctrl-S and printer isolation')
    reset();assert call(6,255)==0 and not any(x==('in',0x32) for x in calls);q[:]=[ord('C')];assert call(6,255)==ord('C') and not q and wire==[];checks.append('Direct nonblocking input returns zero when empty and consumes one byte without echo')
    reset();q[:]=[ord('C')];reader[:]=[ord('R')];assert call(3)==ord('R') and q==[ord('C')];assert call(6,255)==ord('C');checks.append('Reader byte and console queue remain independent')
    reset(3);call(5,9);call(5,16);assert printer==[9,16] and not wire and cpu.mem[s['UB_COLUMN']]==3;call(2,9);assert wire==[32]*5;checks.append('LIST is literal and leaves formatted console state unchanged')
    for value in range(256):call(8,value);assert cpu.mem[3]==value and call(7)==value
    checks.append('Function 7/8 agree with page-zero IOBYTE for all 256 values')
    reset();q[:]=[ord('A'),ord('B'),13];cpu.mem[0x80:0x100]=b'\xA5'*128;call(26,0x9000);cpu.mem[0x9000:0x9080]=b'\x5A'*128;cpu.mem[0x9100:0x9110]=b'\xCC'*16;cpu.mem[0x9100]=8;call(10,0x9100);assert bytes(cpu.mem[0x9100:0x9105])==b'\x08\x02AB\xCC';assert cpu.mem[0x80:0x100]==b'\xA5'*128 and cpu.mem[0x9000:0x9080]==b'\x5A'*128;checks.append('Counted DE buffer has no appended terminator and preserves default/alternate DMA')
    reset();q[:]=[ord('K')];cpu.run(LAYOUT['BIOS']+6);assert cpu.a==255 and q==[ord('K')];cpu.run(LAYOUT['BIOS']+6);assert q==[ord('K')];cpu.run(LAYOUT['BIOS']+9);assert cpu.a==ord('K') and not wire and not q;checks.append('BIOS status polls retain input and BIOS input has no BDOS echo')
    # Execute the actual cpmsim IOBYTE routing table with synthetic host ports.
    bios=a.cpmsim_build/'build/z80pack/bios.bin';machine=Z80(bios.read_bytes());machine.sp=0xB000;ports=[]
    def port_read(port):ports.append(('in',port&255));return {0:1,1:0xC1,2:1,5:0xD2}[port&255]
    def port_write(port,value):ports.append(('out',port&255,value))
    machine.port_read,machine.port_write=port_read,port_write
    machine.run(LAYOUT['BIOS']+72)  # normal unloaded-monitor binding initialization
    route_cases=0
    for byte in range(256):
        con,rdr,pun,lst=byte&3,(byte>>2)&3,(byte>>4)&3,byte>>6;machine.mem[3]=byte
        for offset,selector,mapping in ((12,con,({0:1,1:1,2:{0:1,1:1,2:3,3:None}[lst],3:None})),(15,lst,{0:1,1:1,2:3,3:None}),(18,pun,{0:1,1:5,2:None,3:None})):
            for value in (65,9,16):
                ports.clear();machine.c=value;machine.run(LAYOUT['BIOS']+offset,limit=10000);expected=mapping[selector];assert [x for x in ports if x[0]=='out']==([] if expected is None else [('out',expected,value)]),(byte,offset,ports);route_cases+=1
        for offset,expected in ((21,{0:0x41,1:0xD2,2:0x1A,3:0x1A}[rdr]),(9,{0:0x41,1:0x41,2:{0:0x41,1:0xD2,2:0x1A,3:0x1A}[rdr],3:0x1A}[con])):
            machine.run(LAYOUT['BIOS']+offset,limit=10000);assert machine.a==expected,(byte,offset,machine.a,expected);route_cases+=1
        machine.run(LAYOUT['BIOS']+6,limit=10000);assert machine.a==(255 if con in (0,1) or (con==2 and rdr in (0,1)) else 0);assert machine.mem[3]==byte;route_cases+=1
    # Verify queue semantics through the real cpmsim BIOS, not the logical
    # providers used by the common-BDOS checks above.
    console=[0xC1];aux=[ord('R')];ports.clear();machine.mem[3]=0x95
    def queued_read(port):
        port &=255
        if port==0:return int(bool(console))
        if port==1:return console.pop(0)
        if port==5:return aux.pop(0)
        if port==2:return 1
        raise AssertionError(port)
    machine.port_read=queued_read
    for _ in range(2):machine.run(LAYOUT['BIOS']+6);assert machine.a==255 and console==[0xC1]
    machine.run(LAYOUT['BIOS']+9);assert machine.a==0x41 and not console
    machine.run(LAYOUT['BIOS']+6);assert machine.a==0
    console[:]=[ord('C')];machine.run(LAYOUT['BIOS']+21);assert machine.a==ord('R') and console==[ord('C')]
    machine.run(LAYOUT['BIOS']+9);assert machine.a==ord('C') and not console and not ports
    machine.mem[3]=(0x95&~12)|8;machine.run(LAYOUT['BIOS']+21);assert machine.a==0x1A
    # The production Model 4 supports CRT console/list, with EOF/no-output
    # for unavailable routes. Substitute only physical matrix/video endpoints.
    import re
    native_image=a.build_root/'build/bios/bios.bin';native=Z80(native_image.read_bytes());native.sp=0xB000
    listing=(a.build_root/'build/bios/bios.lst').read_text()
    for name,code in (('M4_STAT',bytes((0x3E,1,0xC9))),('M4_IN',bytes((0x3E,0xC1,0xC9))),('M4_SCROLL_OUT',bytes((0x79,0xD3,0x30,0xC9)))):
        address=int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16);native.mem[address:address+len(code)]=code
    native_wire=[]
    def native_output(port,value):assert port&255==0x30;native_wire.append(value)
    native.port_write=native_output;native.run(LAYOUT['BIOS']+72);native_cases=0
    for byte in range(256):
        native.mem[3]=byte;con,lst=byte&3,byte>>6
        for offset,emitted in ((12,con==1 or (con==2 and lst==1)),(15,lst==1),(18,False)):
            for value in (65,9,16):
                native_wire.clear();native.c=value;native.run(LAYOUT['BIOS']+offset,limit=10000);assert native_wire==([value] if emitted else []),(byte,offset,native_wire);native_cases+=1
        for offset,expected in ((6,255 if con==1 else 0),(9,0x41 if con==1 else 0x1A),(21,0x1A),(45,255 if lst==1 else 0)):
            native.run(LAYOUT['BIOS']+offset,limit=10000);assert native.a==expected,(byte,offset,native.a);native_cases+=1
        assert native.mem[3]==byte
    shutil.copy2(__file__,w/'executed-runner.py')
    result={'status':'PASS','checks':checks,'cpmsim_route_cases':route_cases,'native_route_cases':native_cases,'real_bios_queued_status_reader_and_absent_provider':True,'native_bios_sha256':hashlib.sha256(native_image.read_bytes()).hexdigest(),'bdos_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'bios_sha256':hashlib.sha256(bios.read_bytes()).hexdigest(),'cards':['0059','0060','0061','0062','0063','0064','0065','0066','0075','0076','0077','0078','0079','0081','0082','0091','0102','0123','0420','0436','0438','0440','0442','0444','0468','0469','0470','0471'],'scope':'Production instructions; synthetic logical BIOS and host-port endpoints. Not live printer/FIFO or physical-terminal qualification; flow ordering rather than wall-clock timing.'};(w/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
