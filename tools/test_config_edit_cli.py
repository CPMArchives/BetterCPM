#!/usr/bin/env python3
"""Scalar workbench CLI: bounded parsing, merged records and atomic rejection."""
from pathlib import Path
from test_bios import Z80
from test_utility_versions import address
ROOT=Path(__file__).resolve().parents[1]

def main():
    image=(ROOT/'build/utilities/CONFIG.COM').read_bytes()
    listing=(ROOT/'build/utilities/config.lst').read_text()
    a=lambda n:address(listing,n)
    def cpu(tail):
        c=Z80(b'');c.mem[256:256+len(image)]=image
        c.mem[:3]=bytes.fromhex('c3ffff');c.mem[5:8]=bytes((0xdb,254,0xc9))
        data=tail.encode();c.mem[128]=len(data);c.mem[129:129+len(data)]=data
        return c
    for value in [0,1,255,256,32767,65535]:
        c=cpu('/EDIT=B /DSM='+str(value));c.run(a('CF_PARSE'),limit=200000)
        assert not c.carry,value
        assert int.from_bytes(c.mem[a('CE_VALS')+10:a('CE_VALS')+12],'little')==value
    fields=['PHYSICAL','SPT','BSH','BLM','EXM','DSM','DRM','AL0','AL1',
            'CKS','OFF','CYLINDERS','SECTORS','SIZE','FLAGS','SIZEMAP']
    for index,key in enumerate(fields):
        c=cpu('/EDIT=D /'+key+'=17');c.run(a('CF_PARSE'),limit=200000)
        assert not c.carry,key
        assert c.mem[a('CE_SEEN'):a('CE_SEEN')+16]==bytes(int(n==index) for n in range(16))
        assert int.from_bytes(c.mem[a('CE_VALS')+2*index:a('CE_VALS')+2*index+2],'little')==17,key
    bad=['/EDIT=A /SPT=40','/EDIT=E /SPT=40','/EDIT=B','/EDIT=B/SPT=40',
         '/EDIT=B /BSH=256','/EDIT=B /DSM=65536','/EDIT=B /DSM=999999',
         '/EDIT=B /SPT=-1','/EDIT=B /SPT=+1','/EDIT=B /SPT=',
         '/EDIT=B /SPT=1 /SPT=2','/EDIT=B /SPT=40 /UNKNOWN=1',
         '/EDIT=B /SPT=40 /SHOW','/EDIT=B /SPT=40X']
    for tail in bad:
        c=cpu(tail);c.run(a('CF_PARSE'),limit=200000);assert c.carry,tail
        c=cpu(tail);out=[]
        def io(port):
            assert c.c==2,('invalid request performed I/O',tail,c.c)
            out.append(c.e);return 0
        c.port_read=io;c.run(256,limit=200000)
        assert bytes(out)==b'Invalid CONFIG usage.\r\n',tail
    for fault in [None,'get','geometry','set','unbound']:
        c=cpu('/edit=c /spt=40 /dsm=500 /bsh=4');c.run(a('CF_PARSE'),limit=200000)
        assert not c.carry
        old=bytearray(range(64));old[0]=255 if fault=='unbound' else 1
        old[16]=40;old[19]=0
        active=bytearray(old);ops=[];resets=[]
        c.mem[a('API'):a('API')+3]=bytes((0xdb,232,0xc9))
        def io(port):
            if port&255==254:
                if c.c==2:return 0
                assert c.c==37;c.z=True;resets.append(c.de);return 0
            assert port&255==232
            op=c.b;at=c.de;ops.append(op)
            if (op==3 and fault=='get') or (op==4 and fault=='set'):
                c.z=False;return 1
            if op==3:c.mem[at+1:at+65]=old
            elif op==1:c.mem[at+1:at+7]=bytes([5,35 if fault=='geometry' else 80,2,0,2,15])
            elif op==4:active[:]=c.mem[at+1:at+65]
            else:raise AssertionError(op)
            c.z=True;return 0
        c.port_read=io;c.run(a('CE_APPLY'),limit=200000)
        if fault is None:
            expected=bytearray(old);expected[1:3]=(40).to_bytes(2,'little')
            expected[3]=4;expected[6:8]=(500).to_bytes(2,'little')
            assert active==expected and ops==[3,1,4] and resets==[4]
        else:assert active==old and not resets,(fault,ops)
    print('PASS CONFIG scalar workbench CLI: bounds, pre-I/O rejection, merged commit and failures')
if __name__=='__main__':main()
