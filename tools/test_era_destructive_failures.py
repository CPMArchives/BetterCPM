#!/usr/bin/env python3
"""Inject data/scrub failures into production ERA code at the BIOS boundary."""
import re
import struct
from pathlib import Path
from test_bios import Z80
from test_disk_utilities import ROOT


def main():
    listing=(ROOT/'build/utilities/era.lst').read_text();binary=(ROOT/'build/utilities/ERA.COM').read_bytes()
    def addr(name):return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
    cases=[('data-skip','data',False,'S'),('data-retry','data',False,'R'),
           ('scrub-skip','scrub',False,'S'),('scrub-abort','scrub',False,'A'),
           ('scrub-retry','scrub',False,'R'),('scrub-unattended','scrub',True,''),
           ('scrub-ctrl-c','scrub',False,'\x03'),('scrub-unattended-drive-b','scrub',True,'')]
    for label,kind,unattended,choice in cases:
        c=Z80(b'');c.mem[256:256+len(binary)]=binary
        c.mem[0:3]=bytes((0xC3,255,255));c.mem[5:8]=bytes((0xDB,254,0xC9))
        base=0x8000;c.setword(1,base+3)
        c.mem[base+3:base+6]=bytes((0xC3,255,255))
        for vector in (27,30,33,36,39,42,48):
            c.mem[base+vector:base+vector+3]=bytes((0xDB,vector,0xC9))
        dph=0x8100;dpb=0x8200;c.setword(dph+10,dpb)
        data=bytearray(15);struct.pack_into('<H',data,0,26);data[2:5]=bytes((3,7,0))
        struct.pack_into('<HH',data,5,7,3);data[9]=128;struct.pack_into('<H',data,13,2)
        c.mem[dpb:dpb+15]=data
        disk=bytearray(b'Z'*(64*128));directory=bytearray([229])*128
        for n,user,name,block in ((0,1,b'FILE    DAT',2),(1,7,b'OTHER   DAT',4),(2,1,b'FILE    DAT',4)):
            row=bytearray(32);row[0]=user;row[1:12]=name;row[12]=n;row[16]=block
            directory[n*32:n*32+32]=row
        disk[:128]=directory;before=bytes(disk)
        drive=int(label.endswith('drive-b'))
        heap=addr('E_HEAP');c.mem[heap:heap+32]=bytes(32);c.mem[heap]=drive;c.mem[heap+1]=1
        c.mem[heap+2:heap+13]=b'FILE    DAT';c.mem[heap+14]=2
        c.setword(addr('E_CURRENT'),heap);c.setword(addr('E_NEXT'),heap+32);c.setword(addr('E_LIMIT'),0x7000)
        c.mem[addr('E_DESTRUCT')]=1;c.mem[addr('E_ALLOW')]=255
        c.mem[addr('E_YES')]=int(unattended);c.mem[addr('E_ONCE')]=1
        state={'track':0,'sector':0,'dma':0,'failed':False,'response':False,'writes':0}
        output=bytearray();resets=[]
        def io(port):
            vector=port&255
            if vector==254:
                if c.c==2:
                    output.append(c.e)
                    if output.endswith(b'R/S/A/? '):state['response']=True
                elif c.c==6:
                    if state['response']:
                        assert not unattended
                        state['response']=False
                        return ord(choice)
                    return 0
                elif c.c in (19,30):raise AssertionError('Destructive ERA used ordinary delete/attribute mutation')
                elif c.c==29:c.hl=0
                elif c.c==17:
                    c.mem[addr('E_DMA'):addr('E_DMA')+32]=disk[:32];return 0
                elif c.c==18:return 255
                elif c.c==37:resets.append(c.de)
                return 0
            if vector==27:c.hl=dph
            elif vector==30:state['track']=c.bc
            elif vector==48:c.hl=c.bc
            elif vector==33:state['sector']=c.bc
            elif vector==36:state['dma']=c.bc
            elif vector in (39,42):
                record=(state['track']-2)*26+state['sector'];offset=record*128
                assert 0<=record<64,(label,record)
                dma=state['dma']
                if vector==39:c.mem[dma:dma+128]=disk[offset:offset+128]
                else:
                    state['writes']+=1
                    if not state['failed'] and ((kind=='data' and record==18) or (kind=='scrub' and record==0)):
                        state['failed']=True
                        if kind=='scrub':disk[:32]=c.mem[dma:dma+32]
                        return 1
                    disk[offset:offset+128]=c.mem[dma:dma+128]
            return 0
        c.port_read=io;c.run(addr('E_TRY'),limit=2000000)
        assert state['failed'],label
        assert disk[4*8*128:5*8*128]==before[4*8*128:5*8*128],label
        assert disk[32:64]==before[32:64],label
        if choice=='R':
            assert disk[:32]==bytes((229,))+bytes(31) and disk[64:96]==bytes((229,))+bytes(31),label
            assert disk[2*8*128:3*8*128]==bytes(8*128),label
            assert c.word(addr('E_SHARED'))==1 and c.word(addr('E_NFAIL'))==0,label
            assert b'erased; shared blocks retained' in output,label
        elif kind=='data':
            assert disk[:128]==directory,label
            assert not resets,label
        else:
            assert disk[:32]==bytes((229,))+bytes(31) and disk[64:96]==directory[64:96],label
            assert b'Incomplete destructive erase.' in output and resets==[1<<drive],(label,resets)
        if unattended:assert b'R/S/A/?' not in output
    print('PASS /D production failure injection:',len(cases),'data/scrub retry, skip, abort and unattended cases')

if __name__=='__main__':main()
