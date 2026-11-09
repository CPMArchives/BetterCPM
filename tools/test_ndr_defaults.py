#!/usr/bin/env python3
"""Execute /DEFAULT against file transactions, failures and embedded carriers."""
from collections import Counter
from pathlib import Path
from test_ndr import Guest
from checked_carriers import rsx_metadata
from build_stateful_test_rsx import symbols

ROOT = Path(__file__).resolve().parents[1]
FILE_FUNCTIONS = {15,16,17,19,20,21,22,23,30}


class DiskGuest(Guest):
    """Record-oriented BDOS fixture with named failure points and attributes."""
    def __init__(self):
        super().__init__()
        self.attrs = {}
        self.calls = Counter()
        self.faults = {}
        self.corrupt_readback = False

    def key(self, address):
        c = self.cpu
        drive = c.mem[address] or self.drive+1
        name = bytes(v & 127 for v in c.mem[address+1:address+12])
        return drive, self.user, name

    def put(self, data, stem='NDR', extension='RSX', drive=1, user=0, attrs=(0,0,0)):
        key = drive,user,(stem.ljust(8)+extension.ljust(3)).encode()
        self.files[key] = bytearray(data.ljust((len(data)+127)//128*128,b'\x1a'))
        self.attrs[key] = bytes(8)+bytes(attrs) if len(attrs)==3 else bytes(attrs)
        return key

    def bdos(self, port, value):
        c = self.cpu
        fn, de = c.c, c.de
        if fn not in FILE_FUNCTIONS:
            return super().bdos(port,value)
        key = self.key(de)
        name = key[2].decode()
        self.calls[fn,name] += 1
        fault = self.faults.get((fn,name,self.calls[fn,name]))
        if fault is not None:
            c.a = fault
            return
        c.a = 0
        if fn == 15:
            c.a = 0 if key in self.files else 255
            if not c.a:
                for i,a in enumerate(self.attrs.get(key,bytes(11))):
                    c.mem[de+1+i] = (c.mem[de+1+i]&127)|a
        elif fn == 17:
            c.a = 2 if key in self.files else 255
            if key in self.files:
                entry = bytearray(32);entry[0]=self.user;entry[1:12]=key[2]
                for i,a in enumerate(self.attrs.get(key,bytes(11))): entry[1+i]|=a
                c.mem[self.dma+64:self.dma+96]=entry
        elif fn == 16:
            c.a = 0 if key in self.files else 255
        elif fn == 22:
            if key in self.files: c.a=255
            else:
                self.files[key]=bytearray();self.attrs[key]=bytes(11)
        elif fn == 19:
            if key not in self.files: c.a=255
            else:
                del self.files[key];self.attrs.pop(key,None)
        elif fn in (20,21):
            record = c.mem[de+32]
            if key not in self.files:
                c.a=255;return
            if fn == 20:
                data = self.files[key][128*record:128*(record+1)]
                c.a=0 if len(data)==128 else 1
                if not c.a:
                    c.mem[self.dma:self.dma+128]=data
                    if self.corrupt_readback and key[2].endswith(b'$ND'):
                        c.mem[self.dma]^=1
            else:
                self.files[key][128*record:128*(record+1)]=c.mem[self.dma:self.dma+128]
            if not c.a:c.mem[de+32]+=1
        elif fn == 23:
            target = self.key(de+16)
            if key not in self.files or target in self.files:c.a=255
            else:
                self.files[target]=self.files.pop(key)
                self.attrs.pop(key,None)
                self.attrs[target]=bytes(v&128 for v in c.mem[de+17:de+28])
        elif fn == 30:
            if key not in self.files:c.a=255
            else:self.attrs[key]=bytes(v&128 for v in c.mem[de+1:de+12])


def versions():
    carrier=bytearray((ROOT/'build/rsx/NDR.RSX').read_bytes())
    meta=int.from_bytes(carrier[30:32],'little')
    metadata=carrier[meta:]
    if carrier[4]==3:
        metadata=bytearray(metadata[:12]+metadata[32:])
        metadata[4]=1;metadata[7]-=1;metadata[8:10]=len(metadata).to_bytes(2,'little')
    carrier[4]=2
    v2=bytes(carrier[:meta])+bytes(metadata)
    carrier[4]=3
    v3=bytes(carrier[:meta])+rsx_metadata('NDR',bytes(metadata),{})
    return v2,v3


def checksum(data):
    n=int.from_bytes(data[12:14],'little')
    data[44:46]=(sum(data[512:512+n])&65535).to_bytes(2,'little')


def setup(carrier=None,**location):
    g=DiskGuest()
    assert 'updated' in g.run('COMMANDS A0:')
    assert 'updated' in g.run('UTILS P31:')
    key=g.put(carrier or versions()[0],**location)
    return g,key


def verify(old,new,table):
    offset=512+symbols(ROOT/'build/rsx/ndr.lst')['NR_TABLE']-0x8000
    expected=bytearray(old);expected[offset:offset+320]=table;checksum(expected)
    assert bytes(new)==bytes(expected), 'unrelated carrier bytes changed'


def main():
    count=0
    for carrier in versions():
        for prefix in ('',' ','   '):
            g,key=setup(carrier,drive=2,user=31,attrs=(0,128,128))
            table=g.table();old=bytes(g.files[key])
            output=g.run(prefix+'/default B31:NDR',leading_space=False)
            assert 'defaults saved' in output,output
            assert g.table()==table and (g.drive,g.user)==(0,0)
            assert set(g.files)=={key} and g.attrs[key]==bytes(8)+bytes((0,128,128))
            verify(old,g.files[key],table)
            assert 'updated' in g.run('/DEL UTILS')
            old=bytes(g.files[key]);table=g.table()
            assert 'defaults saved' in g.run('/DEFAULT B31:NDR.RSX')
            verify(old,g.files[key],table);assert set(g.files)=={key}
            g.carrier=bytes(g.files[key]);size=int.from_bytes(g.carrier[12:14],'little')
            g.cpu.mem[g.base:g.base+size]=g.carrier[512:512+size]
            for off in g.relocations:
                g.cpu.setword(g.base+off,g.cpu.word(g.base+off)+g.base-0x8000)
            assert g.table()==table and g.lookup('COMMANDS')==(0,0x100)
            count+=1
    # Also retain CP/M's user attribute bits in the filename, not only R/S/A.
    attrs=bytes((128,0,128,0,0,0,0,0,0,128,128))
    g,key=setup(attrs=attrs)
    assert 'defaults saved' in g.run('/DEFAULT NDR.RSX') and g.attrs[key]==attrs
    count+=1
    g,key=setup(drive=3,user=7);g.drive=2;g.user=7
    assert 'defaults saved' in g.run('/DEFAULT NDR') and (g.drive,g.user)==(2,7)
    count+=1
    g,key=setup();del g.files[key];table=g.table()
    assert 'failed' in g.run('/DEFAULT NDR.RSX') and not g.files and g.table()==table
    count+=1
    g,key=setup();g.run('/CLEAR');old=bytes(g.files[key])
    assert 'defaults saved' in g.run('/DEFAULT NDR.RSX')
    verify(old,g.files[key],bytes(320));count+=1
    g,key=setup()
    for tail in ('/DEFAULT','/DEFAULT A0:','/DEFAULT *.RSX','/DEFAULT NDR.NDR',
                 '/DEFAULT NDR.RSX EXTRA','/DEFAULTX NDR.RSX'):
        before={k:bytes(v) for k,v in g.files.items()};table=g.table()
        assert 'defaults saved' not in g.run(tail)
        assert before==g.files and g.table()==table
        count+=1
    v2,v3=versions()
    bad=[]
    for base in (v2,v3):
        for at in (0,5,8,10,12,14,16,18,20,22,24,28,30,32,40,48,512,600,len(base)-1):
            value=bytearray(base);value[at]^=1
            if at>=512:checksum(value)
            bad.append(value)
        value=bytearray(base);value[44]^=1;bad.append(value)
        bad.extend([base[:128],base[:-128],base.ljust((len(base)+127)//128*128,b'\x1a')+bytes(128)])
    for carrier in bad:
        g,key=setup(carrier);before=bytes(g.files[key]);table=g.table()
        assert 'unchanged' in g.run('/DEFAULT NDR.RSX')
        assert g.files[key]==before and set(g.files)=={key} and g.table()==table
        count+=1
    g,key=setup(attrs=(128,0,0));old=bytes(g.files[key])
    assert 'read-only' in g.run('/DEFAULT NDR.RSX')
    assert g.files[key]==old;count+=1
    for suffix in ('$ND','$NB'):
        g,key=setup();g.put(b'KEEP',extension=suffix);before={k:bytes(v) for k,v in g.files.items()}
        assert 'file exists' in g.run('/DEFAULT NDR.RSX')
        assert g.files==before;count+=1
    g,key=setup();g.cpu.mem[g.base+g.table_off]=ord('!');old=bytes(g.files[key])
    assert 'unchanged' in g.run('/DEFAULT NDR.RSX') and g.files[key]==old;count+=1
    faults=[(15,'NDR     RSX',1,255),(20,'NDR     RSX',1,2),
            (20,'NDR     RSX',9,2),(16,'NDR     RSX',1,255),
            (22,'NDR     $ND',1,255),(21,'NDR     $ND',1,1),
            (21,'NDR     $ND',4,1),(21,'NDR     $ND',8,1),
            (16,'NDR     $ND',1,255),(15,'NDR     $ND',1,255),
            (20,'NDR     $ND',1,2),(20,'NDR     $ND',9,2),
            (16,'NDR     $ND',2,255),(30,'NDR     $ND',1,255),
            (23,'NDR     RSX',1,255),(23,'NDR     $ND',1,255)]
    for fn,name,n,status in faults:
        g,key=setup();old=bytes(g.files[key]);table=g.table()
        g.faults[fn,name,n]=status
        output=g.run('/DEFAULT NDR.RSX')
        assert g.calls[fn,name]>=n, (fn,name,n,g.calls)
        assert 'failed' in output or 'unchanged' in output, (fn,name,n,output)
        assert g.files=={key:old} and g.table()==table,(fn,name,n,g.files.keys())
        count+=1
    g,key=setup();g.corrupt_readback=True;old=bytes(g.files[key])
    assert 'failed' in g.run('/DEFAULT NDR.RSX') and g.files=={key:old};count+=1
    g,key=setup();old=bytes(g.files[key]);table=g.table()
    g.faults[23,'NDR     $ND',1]=255;g.faults[23,'NDR     $NB',1]=255
    output=g.run('/DEFAULT NDR.RSX')
    assert 'Original is .$NB' in output,output
    backup=key[:2]+(b'NDR     $NB',);temp=key[:2]+(b'NDR     $ND',)
    assert set(g.files)=={backup,temp} and g.files[backup]==old
    verify(old,g.files[temp],table);assert g.table()==table;count+=1
    g,key=setup();old=bytes(g.files[key]);g.corrupt_readback=True
    g.faults[19,'NDR     $ND',1]=255
    assert 'remove stale .$ND' in g.run('/DEFAULT NDR.RSX') and g.files[key]==old;count+=1
    g,key=setup();old=bytes(g.files[key]);table=g.table()
    g.faults[19,'NDR     $NB',1]=255
    assert 'saved; original retained as .$NB' in g.run('/DEFAULT NDR.RSX')
    verify(old,g.files[key],table);assert g.files[key[:2]+(b'NDR     $NB',)]==old;count+=1
    print(f'PASS NDR /DEFAULT: {count} carrier, persistence, validation and transaction cases')


if __name__=='__main__':main()
