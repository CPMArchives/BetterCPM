#!/usr/bin/env python3
"""Execute the real Model 4 configuration entry through profile admission."""
import argparse
import re
from pathlib import Path
from test_bios import Z80

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build-root',type=Path,default=ROOT/'build')
    a=p.parse_args();folder=a.build_root/'system'
    def symbol(file,name):
        match=re.search(r'^([0-9a-f]{4}).*?\b'+name+r':',file.read_text(),re.M|re.I)
        assert match,name
        return int(match[1],16)
    listing=folder/'config.lst'
    entry=symbol(listing,'CF_LOG')
    links=(folder/'disklink.inc').read_text()
    def external(name):
        match=re.search(r'^'+name+r' EQU 0([0-9A-F]+)H',links,re.M)
        assert match,name
        return int(match[1],16)
    count=0
    for physical in range(4):
        for adapter in (0,1,2,255):
            for incoming_zero in (False,True):
                c=Z80(b'');c.sp=0x3f00;c.ix=0x7600;c.z=incoming_zero
                image=(folder/'config.bin').read_bytes()
                assert len(image)<=1024
                c.mem[0xf000:0xf000+len(image)]=image
                c.mem[c.ix]=1;c.mem[c.ix+1]=physical;c.mem[c.ix+62]=adapter
                # Model the resident lookup's successful DPH result. Trap the
                # subsequent physical lookup or rejection, before later policy.
                at=external('DC_LOG');c.mem[at:at+5]=bytes.fromhex('37210090c9')
                for name,port in (('DC_PHY',254),('DC_UNSUPPORTED',255)):
                    at=external(name);c.mem[at:at+3]=bytes((0xd3,port,0xc9))
                observed=[]
                def trap(port,value):
                    observed.append((port&255,c.a));c.pc=65535
                c.port_write=trap
                c.run(entry)
                assert observed==([(254,physical)] if adapter==0 else [(255,physical)]),(physical,adapter,incoming_zero,observed)
                count+=1
    print(f'PASS Model 4 configuration admission: {count} physical/adapter/flag cases; device preserved; overlay <=1024 bytes')

if __name__=='__main__':main()
