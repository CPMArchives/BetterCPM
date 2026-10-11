#!/usr/bin/env python3
"""Execute ERA's pure allocation planner against independent ownership fixtures."""
import re
import struct
import subprocess
import tempfile
from pathlib import Path
from test_bios import Z80
from test_disk_utilities import ROOT


def main():
    with tempfile.TemporaryDirectory(prefix='era-plan-') as temp:
        w=Path(temp);source=w/'probe.mac';binary=w/'probe.bin';listing=w/'probe.lst'
        source.write_text('        ASEG\n        ORG 0100H\n'+''.join((ROOT/'src/utilities/common'/n).read_text() for n in ('eraraw.inc','eraplan.inc'))+'        END\n')
        subprocess.run(['/Users/nathanael/bin/z80asm','-fb','-o'+str(binary),'-l'+str(listing),source.name],cwd=w,check=True)
        text=listing.read_text();image=binary.read_bytes()
        def addr(name):return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',text,re.M|re.I)[1],16)
        def entry(user,name,blocks,dsm=99,attrs=0):
            data=bytearray(32);data[0]=user
            stem,ext=name.split('.');data[1:12]=stem.ljust(8).encode()+ext.ljust(3).encode()
            if attrs&1:data[9]|=128
            if attrs&2:data[10]|=128
            if attrs&4:data[11]|=128
            for n,block in enumerate(blocks):
                if dsm<256:data[16+n]=block
                else:struct.pack_into('<H',data,16+n*2,block)
            return bytes(data)
        cases=[
            ('unique',[entry(3,'FILE.DAT',[4,5]),entry(4,'OTHER.DAT',[6])],99,{4,5},set(),0),
            ('shared-other-user',[entry(3,'FILE.DAT',[4,5]),entry(7,'OTHER.DAT',[5])],99,{4},{5},0),
            ('shared-other-first',[entry(7,'OTHER.DAT',[5]),entry(3,'FILE.DAT',[4,5])],99,{4},{5},0),
            ('all-shared',[entry(3,'FILE.DAT',[4,5]),entry(2,'OTHER.DAT',[4,5])],99,set(),{4,5},0),
            ('multiple-extents',[entry(3,'FILE.DAT',[4,5]),entry(3,'FILE.DAT',[6,7],attrs=3),entry(2,'OTHER.DAT',[6])],99,{4,5,7},{6},0),
            ('empty',[entry(3,'FILE.DAT',[])],99,set(),set(),0),
            ('missing',[entry(2,'FILE.DAT',[4])],99,set(),set(),3),
            ('out-of-range',[entry(3,'FILE.DAT',[100])],99,set(),set(),2),
            ('directory-block',[entry(3,'FILE.DAT',[1])],99,set(),set(),2),
            ('duplicate-target-block',[entry(3,'FILE.DAT',[4,4])],99,set(),set(),2),
            ('duplicate-extents',[entry(3,'FILE.DAT',[4]),entry(3,'FILE.DAT',[4])],99,set(),set(),2),
            ('word-pointers',[entry(3,'FILE.DAT',[257,258],511),entry(31,'OTHER.DAT',[258],511)],511,{257},{258},0),
            ('deleted-other',[entry(3,'FILE.DAT',[4]),entry(229,'OLD.DAT',[4])],99,{4},set(),0),
            ('reserved-extra',[entry(3,'FILE.DAT',[15])],99,set(),set(),2),
            ('capacity',[entry(3,'FILE.DAT',[4])],99,set(),set(),1),
            ('bad-bsh',[entry(3,'FILE.DAT',[4])],99,set(),set(),1),
            ('bad-blm',[entry(3,'FILE.DAT',[4])],99,set(),set(),1),
            ('record-overflow',[entry(3,'FILE.DAT',[4])],8191,set(),set(),1),
            ('unrelated-corrupt',[entry(3,'FILE.DAT',[4]),entry(8,'OTHER.DAT',[100])],99,set(),set(),2),
        ]
        for label,rows,dsm,unique,shared,error in cases:
            c=Z80(b'');c.mem[256:256+len(image)]=image
            dpb=bytearray(15);struct.pack_into('<H',dpb,0,36);dpb[2:5]=bytes((4,15,1))
            struct.pack_into('<HH',dpb,5,dsm,63);dpb[9:11]=bytes((0xC0,1 if label=='reserved-extra' else 0))
            if label=='bad-bsh':dpb[2]=2
            if label=='bad-blm':dpb[3]=14
            c.mem[addr('ER_DPB'):addr('ER_DPB')+15]=dpb
            directory=b''.join(rows)+bytes([229])*32*(64-len(rows))
            c.mem[0x3000:0x3000+len(directory)]=directory
            c.mem[0x4000:0x4000+12]=bytes((3,))+b'FILE    DAT'
            c.hl=0x3000;c.bc=64;c.de=0x4000;c.ix=0x5000;c.setword(addr('EG_LIMIT'),0x5060 if label=='capacity' else 0x6000)
            c.run(addr('EG_PLAN'),limit=1000000)
            assert c.carry==bool(error),(label,c.mem[addr('EG_ERROR')])
            assert c.mem[addr('EG_ERROR')]==error,label
            assert bytes(c.mem[0x3000:0x3000+len(directory)])==directory,label
            if error:continue
            table=c.mem[0x5000:0x5000+dsm+1]
            assert {n for n,b in enumerate(table) if b&3==1}==unique,label
            assert {n for n,b in enumerate(table) if b&3==3}==shared,label
            assert c.word(addr('EG_UNIQUE'))==len(unique) and c.word(addr('EG_SHARED'))==len(shared),label
            expected=[int(row[0]==3 and bytes(v&127 for v in row[1:12])==b'FILE    DAT') for row in rows]+[0]*(64-len(rows))
            marks=c.word(addr('EG_MARK'))
            assert list(c.mem[marks:marks+64])==expected,label
        print('PASS destructive ERA planner:',len(cases),'ownership/map cases; input metadata unchanged; no disk I/O')


if __name__=='__main__':main()
