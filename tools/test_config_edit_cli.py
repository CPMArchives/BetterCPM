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
        old[16]=40;old[19]=0;old[52]=0
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
    for tail in ['/EDIT=B /SLOT=0 /ID=1','/EDIT=B /SLOT=33 /ID=1',
                 '/EDIT=B /SLOT=256 /ID=1','/EDIT=B /SLOT=1',
                 '/EDIT=B /ID=1','/EDIT=B /CODE=2',
                 '/EDIT=B /SLOT=2 /ID=256','/EDIT=B /SLOT=2 /CODE=4',
                 '/EDIT=B /SLOT=2 /CODE=65535',
                 '/EDIT=B /SLOT=2 /CODE=1 /CODE=2']:
        c=cpu(tail);c.run(a('CF_PARSE'),limit=200000);assert c.carry,tail
        c=cpu(tail);out=[]
        def invalid_io(port):
            assert c.c==2,('invalid map performed I/O',tail,c.c)
            out.append(c.e);return 0
        c.port_read=invalid_io;c.run(256,limit=200000)
        assert bytes(out)==b'Invalid CONFIG usage.\r\n'
    for mixed in [False,True]:
        for slot in range(1,33):
            for code in range(4):
                # All packed bit positions, first mixed seeding, existing-map
                # preservation and ID range endpoints share the menu engine.
                c=cpu('/EDIT=B /CODE='+str(code)+' /ID=255 /SLOT='+str(slot))
                c.run(a('CF_PARSE'),limit=200000);assert not c.carry,(slot,code)
                old=bytearray(range(64));old[18]=2;old[52]=int(mixed)
                c.mem[a('EDCOPY'):a('EDCOPY')+64]=old
                c.run(a('CE_MAP'),limit=200000)
                expected=bytearray(old);expected[20+slot-1]=255
                if not mixed:expected[53:61]=bytes([0xaa])*8
                expected[52]=1
                pos=53+(slot-1)//4;shift=2*((slot-1)%4)
                expected[pos]=(expected[pos]&~(3<<shift))|(code<<shift)
                assert c.mem[a('EDCOPY'):a('EDCOPY')+64]==expected,(mixed,slot,code)
    c=cpu('/EDIT=B /SLOT=32 /ID=0');c.run(a('CF_PARSE'),limit=200000)
    old=bytearray(range(64));c.mem[a('EDCOPY'):a('EDCOPY')+64]=old
    c.run(a('CE_MAP'),limit=200000);old[51]=0
    assert c.mem[a('EDCOPY'):a('EDCOPY')+64]==old
    for ok in [False,True]:
        c=cpu('');c.mem[a('REQ')+53]=1;calls=[]
        def map_io(port):
            assert c.c==183 and c.b==2
            calls.append(c.ix)
            c.hl=0x4644 if ok else 0xffff
            return 0
        c.port_read=map_io;c.run(a('EDCHECK'),limit=200000)
        assert c.z==ok and calls==[a('REQ')]
    # The same validation must precede the menu and CLI setter calls.
    source=(ROOT/'src/utilities/config.mac').read_text()
    assert any('CALL EDCHECK\n        '+jump+' NZ,EDINVALID' in source for jump in ('JP','JR'))
    assert 'CALL EDCHECK\n        JP NZ,CL_ERROR' in source
    print('PASS CONFIG workbench CLI: scalar bounds, map packing, pre-I/O rejection, merged commit and explicit-map validation')
if __name__=='__main__':main()
