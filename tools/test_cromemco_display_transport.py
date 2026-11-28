#!/usr/bin/env python3
"""Exercise emitted display code against a deliberately delayed FDC UART."""
import argparse
import hashlib
import json
from pathlib import Path
from build_z80pack_image import symbols
from test_bios import Z80


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=args.build_root.resolve();out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    bios=root/'build/cromemco';labels=symbols(bios/'bios.lst');base=labels['BIOS']
    results=[]
    for personality in ('ADM3A','VT52','ANSI'):
        folder=root/'build/release-tcap'/personality
        code=(folder/'native.bin').read_bytes();module=symbols(folder/'native.lst')
        cpu=Z80(b'');cpu.sp=0xb000
        cpu.mem[base:base+len((bios/'bios.bin').read_bytes())]=(bios/'bios.bin').read_bytes()
        cpu.mem[0x8000:0x8000+len(code)]=code
        cpu.setword(1,base+3)
        wire=[];state={'polls':0,'ready':False,'total':0}
        def read(port):
            assert port&255==0
            state['polls']+=1;state['total']+=1
            state['ready']=state['polls']>=4
            return 128 if state['ready'] else 0
        def write(port,value):
            assert port&255==1 and state['ready'], 'output preceded transmitter readiness'
            wire.append(value);state['polls']=0;state['ready']=False
        cpu.port_read=read;cpu.port_write=write
        # The private leaf must preserve live renderer registers and flags.
        cpu.a=65;cpu.bc=0x1234;cpu.de=0x5678;cpu.hl=0x9abc;cpu.z=True;cpu.carry=True
        cpu.run(labels['CM_TXA'])
        assert (cpu.a,cpu.bc,cpu.de,cpu.hl,cpu.z,cpu.carry)==(65,0x1234,0x5678,0x9abc,True,True)
        wire.clear();cpu.c=65
        cpu.run(module['D_PRINT'],limit=50000)
        assert 65 in wire and state['total']>=4*(len(wire)+1)
        footprint=json.loads((folder/'footprint.json').read_text())
        assert footprint['full_budgeted_path_bytes']<=footprint['full_path_limit_bytes']
        results.append({'personality':personality,'status':'PASS','bytes_emitted':len(wire),
                        'delayed_status_polls':state['total'],'footprint':footprint,
                        'native_sha256':hashlib.sha256(code).hexdigest()})
    (out/'result.json').write_text(json.dumps({'status':'PASS','modules':results},indent=2)+'\n')
    print('PASS: all integrated personalities poll the delayed UART and preserve leaf state within their footprint budgets')


if __name__=='__main__':main()
