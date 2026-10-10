#!/usr/bin/env python3
"""Execute shared selector components in relocated production RCP payloads."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from test_bios import Z80
from test_disk_utilities import ROOT


def main():
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);args=p.parse_args()
    report=args.report.resolve();report.mkdir(parents=True,exist_ok=False)
    carrier=(ROOT/'build/cpx/RCP.CPX').read_bytes()
    listing=(ROOT/'build/cpx/rcp.lst').read_text()
    linked,size=struct.unpack_from('<HH',carrier,10)
    count,header,payload,table=struct.unpack_from('<4H',carrier,22)
    original=carrier[payload:payload+size]
    def address(name,base):
        value=int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
        return value-linked+base
    def cpu(base,text):
        image=bytearray(original)
        for n in range(count):
            offset=struct.unpack_from('<H',carrier,table+n*2)[0]
            word=struct.unpack_from('<H',image,offset)[0]
            struct.pack_into('<H',image,offset,(word+base-linked)&65535)
        c=Z80(b'');c.mem[base:base+len(image)]=image
        c.mem[0x2000:0x2000+len(text)]=text.encode();c.hl=0x2000;c.b=len(text);c.d=1;c.e=2
        return c
    results=[]
    for base in (0x4000,0x8101,0xA000):
        a=lambda name:address(name,base)
        for text,pairs,tail in [
            ('*.COM',[(1,2)],'*.COM'),('P31:FOO.DAT',[(15,31)],'FOO.DAT'),
            ('B[-]:',[(1,u) for u in range(32)],''),
            ('[A0,C[3,5,7-11],5]:F?*.DAT',[(0,0),(1,5)]+[(2,u) for u in (3,5,7,8,9,10,11)],'F?*.DAT')]:
            c=cpu(base,text);c.run(a('DU_PARSE'),limit=100000)
            expected=bytearray(64)
            for d,u in pairs:expected[d*4+u//8]|=1<<(u%8)
            assert not c.carry and bytes(c.mem[a('DU_MAP'):a('DU_MAP')+64])==expected,text
            assert bytes(c.mem[c.hl:c.hl+c.b]).decode()==tail
            assert bytes(c.mem[0x2000:0x2000+len(text)]).decode()==text
            c.bc=0;found=[]
            while True:
                c.run(a('DU_NEXT'),limit=100000)
                if c.carry:break
                found.append((c.d,c.e))
            assert found==sorted(set(pairs)) and c.bc==512
        for text in ('B32:','B[*]:','[A0,B[3,32]]:','B[1,]:','B[3'):
            c=cpu(base,text);c.mem[a('DU_MAP'):a('DU_MAP')+64]=bytes([255])*64
            c.run(a('DU_PARSE'),limit=100000)
            assert c.carry and bytes(c.mem[a('DU_MAP'):a('DU_MAP')+64])==bytes(64)
            assert 0<=c.hl-0x2000<=len(text)
        c=cpu(base,'');c.mem[a('DU_MAP'):a('DU_MAP')+64]=bytes([255])*64;c.bc=0
        for n in range(512):
            c.run(a('DU_NEXT'),limit=10000)
            assert not c.carry and (c.d,c.e)==divmod(n,32) and c.bc==n+1
        c.run(a('DU_NEXT'),limit=10000);assert c.carry and c.bc==512
        for text,body,expr,mask in [('F?*.DAT[$ARC+!$SYS]','F?*.DAT','$ARC+!$SYS',0x30),
                                     ('FOO.COM','FOO.COM','',255),
                                     ('*.COM[$RO,$SYS]','*.COM','$RO,$SYS',0xEE)]:
            c=cpu(base,text);c.run(a('OQ_SPLIT'),limit=10000)
            assert not c.carry and bytes(c.mem[c.hl:c.hl+c.b]).decode()==body
            ptr=c.word(a('OQ_PTR'));length=c.mem[a('OQ_LEN')]
            assert bytes(c.mem[ptr:ptr+length]).decode()==expr
            if expr:
                c.hl,c.b=ptr,length;c.run(a('AT_PARSE'),limit=10000)
                assert not c.carry and c.a==mask
        for text in ('F[]','F[$RO','F[$RO]X','F[[$RO]]','F[$RO ]'):
            c=cpu(base,text);c.run(a('OQ_SPLIT'),limit=10000)
            assert c.carry and c.word(a('OQ_PTR'))==0 and c.mem[a('OQ_LEN')]==0
        for text in ('$WHL','$ARC++$RO','$SYS,','!'):
            c=cpu(base,text);c.run(a('AT_PARSE'),limit=10000)
            assert c.carry and c.a==0 and c.mem[a('AT_RESULT')]==0
            assert 0<=c.hl-0x2000<=len(text)
        for text,valid in [('F?*.DAT',True),('F***.DAT',True),('F*A.DAT',False),('F**?.DAT',False),('TOOLONGNM.COM',False)]:
            c=cpu(base,text);c.mem[a('BC_COFCP'):a('BC_COFCP')+2]=a('BC_FCB').to_bytes(2,'little')
            c.mem[a('BC_MVFLAG')]=0;c.run(a('BC_CVALID'),limit=10000)
            assert (not c.carry)==valid,text
        results.append({'base':base,'result':'PASS','iterator_positions':512})
    (report/'RCP.CPX').write_bytes(carrier)
    (report/'rcp.lst').write_text(listing)
    (report/'harness.py').write_bytes(Path(__file__).read_bytes())
    (report/'evidence.json').write_text(json.dumps({'result':'PASS','components_only':True,
        'carrier_sha256':hashlib.sha256(carrier).hexdigest(),'bytes':size,'header':header,
        'relocations':count,'origins':results},indent=2)+'\n')
    print('Relocated RCP DU/qualifier/predicate components and bounded wildcard validation: PASS')


if __name__=='__main__':main()
