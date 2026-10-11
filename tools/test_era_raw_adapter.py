#!/usr/bin/env python3
"""Qualify pure ERA raw-record positioning at BIOS boundaries without writes."""
import argparse
import re
import subprocess
import tempfile
from pathlib import Path
from test_bios import Z80
from test_disk_utilities import ROOT


def main():
    p=argparse.ArgumentParser();p.add_argument('--assembler',type=Path,default=Path('/Users/nathanael/bin/z80asm'));a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='era-raw-read-') as temp:
        w=Path(temp);source=w/'probe.mac';binary=w/'probe.bin';listing=w/'probe.lst'
        source.write_text('        ASEG\n        ORG 0100H\n'+(ROOT/'src/utilities/common/eraraw.inc').read_text()+'        END\n')
        subprocess.run([str(a.assembler),'-fb','-o'+str(binary),'-l'+str(listing),source.name],cwd=w,check=True)
        text=listing.read_text();data=binary.read_bytes()
        def addr(name):return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',text,re.M|re.I)[1],16)
        count=0
        for spt,off in ((36,6),(40,2),(40,0),(26,2),(80,0)):
            for record in (0,1,3,4,spt-1,spt,spt+1,4095,65535):
                cpu=Z80(b'');cpu.mem[256:256+len(data)]=data
                cpu.setword(addr('ER_DPB'),spt);cpu.setword(addr('ER_DPB')+13,off)
                # BIOS vectors recorded through a controlled port callback.
                base=0x4000;cpu.setword(addr('ER_BASE'),base)
                calls=[]
                for vector in (30,33,36,39,48):
                    # Each tiny stub identifies the BIOS operation, then returns.
                    target=base+vector;cpu.mem[target:target+3]=bytes((0xDB,vector,0xC9))
                def bios(vector):
                    vector &= 255
                    calls.append((vector,cpu.bc,cpu.de))
                    if vector==48:cpu.hl=cpu.bc
                    return 0
                cpu.port_read=bios;cpu.hl=record;cpu.de=0x3000
                cpu.run(addr('ER_READ'),limit=200000)
                assert not cpu.carry
                assert [v for v,_,_ in calls]==[30,48,33,36,39]
                assert calls[0][1]==record//spt+off
                assert calls[1][1]==record%spt and calls[1][2]==0
                assert calls[2][1]==record%spt and calls[3][1]==0x3000
                count+=1
        for entries,capacity,start,fail_at in ((64,2048,0x6000,0),
                (128,4096,0x6000,0),(1,128,0x6000,0),
                (128,4095,0x6000,0),(128,4096,0xF800,0),
                (64,2048,0x6000,2)):
            cpu=Z80(b'');cpu.mem[256:256+len(data)]=data
            cpu.setword(addr('ER_DPB'),36);cpu.setword(addr('ER_DPB')+13,6)
            cpu.setword(addr('ER_DPB')+7,entries-1)
            base=0x4000;cpu.setword(addr('ER_BASE'),base)
            calls=[];state={'track':0,'sector':0,'dma':0,'reads':0}
            for vector in (30,33,36,39,48):
                cpu.mem[base+vector:base+vector+3]=bytes((0xDB,vector,0xC9))
            def snapshot_bios(vector):
                vector &= 255;calls.append(vector)
                if vector==30:state['track']=cpu.bc
                elif vector==48:cpu.hl=cpu.bc
                elif vector==33:state['sector']=cpu.bc
                elif vector==36:state['dma']=cpu.bc
                elif vector==39:
                    state['reads']+=1
                    if state['reads']==fail_at:return 1
                    record=(state['track']-6)*36+state['sector']
                    dma=state['dma'];cpu.mem[dma:dma+128]=bytes([record])*128
                return 0
            cpu.port_read=snapshot_bios;cpu.de=start;cpu.bc=capacity
            cpu.run(addr('ER_SNAP'),limit=200000)
            rejected=capacity<((entries+3)//4)*128 or start+((entries+3)//4)*128>65535
            assert cpu.carry==bool(rejected or fail_at)
            assert 42 not in calls
            if rejected:assert not calls
            elif fail_at:assert state['reads']==fail_at
            else:
                assert cpu.hl==start and cpu.bc==entries
                expected=b''.join(bytes([n])*128 for n in range((entries+3)//4))
                assert cpu.mem[start:start+len(expected)]==expected
            count+=1
        print('PASS ERA read-only raw adapter:',count,'positioning/snapshot cases; no write vector invoked')


if __name__=='__main__':main()
