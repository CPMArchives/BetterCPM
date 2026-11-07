#!/usr/bin/env python3
"""Inject physical errors at FD1791 ports while executing the shipping Z80 code."""
import argparse
import ctypes as C
import hashlib
import json
import tempfile
from pathlib import Path

from build_z80pack_image import symbols
from test_model2_screen import cpu_library
from test_usq import SHIM

PORTS = """
static BYTE (*read_port)(BYTE);
static void (*write_port)(BYTE,BYTE);
void set_ports(BYTE (*r)(BYTE), void (*w)(BYTE,BYTE)) {read_port=r;write_port=w;}
BYTE io_in(BYTE l, BYTE h) { return read_port(l); }
void io_out(BYTE l, BYTE h, BYTE d) { write_port(l,d); }
"""


def check(out, library):
    disk = (out/'disk.bin').read_bytes()
    base = json.loads((out.parent/'profile/context.json').read_text())['symbols']['LY_DISK']
    names = symbols(out/'disk.lst')
    ram = (C.c_ubyte*65536).in_dll(library,'memory')
    regs = {name:C.c_ubyte.in_dll(library,name) for name in 'ACDEHL'}
    sp = C.c_ushort.in_dll(library,'SP')
    rd,wr = C.CFUNCTYPE(C.c_ubyte,C.c_ubyte),C.CFUNCTYPE(None,C.c_ubyte,C.c_ubyte)
    library.set_ports.argtypes = [rd,wr]
    library.test_run.argtypes = [C.c_ushort,C.c_int]
    results = []
    scenarios = {'healthy':[0], 'CRC then success':[8,0], 'miss then CRC then success':[16,8,0],
                 'persistent lost data':[4,4,4], 'controller timeout then success':[None,0],
                 'three controller timeouts':[None,None,None], 'seek failure then success':['seek',0]}
    for cyl, size in [(0,128),(76,512)]:
        for command in (0x80,0xa0):
            cases = dict(scenarios)
            if command == 0xa0:
                cases['write protected'] = [64]
                cases['CRC then write protection'] = [8,64]
            for title, script in cases.items():
                attempts,aborts,restores,transfers = [],[],[],[]
                chip = {'command':None,'track':0,'data':0,'sector':0,'drive':0,'dma':[]}
                @wr
                def write(port,value):
                    if port==0xef:
                        chip['drive']=value
                    elif port==0xe7:
                        chip['data']=value
                    elif port==0xe6:
                        chip['sector']=value
                    elif port==0xf8:
                        chip['dma'].append(value)
                    elif port==0xe4:
                        chip['command']=value
                        if value==0x08:
                            restores.append(value)
                            attempts.append(script[min(len(attempts),len(script)-1)])
                            chip['track']=0
                        elif value==0x18:
                            chip['track']=chip['data']
                        elif value in (0x80,0xa0):
                            transfers.append((value,chip['drive'],chip['sector'],chip['track'],bytes(chip['dma'])))
                            chip['dma'].clear()
                        elif value==0xd0:
                            aborts.append(value)
                            chip['dma'].clear()
                @rd
                def read(port):
                    status = attempts[-1] if attempts else 0
                    if port==0xe5:
                        return chip['track']
                    if port==0xe0:
                        return 0 if status is None else 1
                    if port==0xe4:
                        if chip['command'] in (8,0x18):
                            return 16 if status=='seek' else 0
                        return status if isinstance(status,int) else 0
                    return 0
                library.set_ports(read,write)
                ram[base:base+len(disk)] = disk
                buf = bytes((i*11)&255 for i in range(size))
                ram[0x6000:0x6000+size] = buf
                for k,v in dict(A=2,D=cyl,E=1,C=command,H=0x60,L=0).items():regs[k].value=v
                sp.value=0xb000
                steps=library.test_run(names['M2_XFER'],3000000)
                context = (title,cyl,command,attempts,regs['A'].value)
                assert steps>=0 and attempts==script and sp.value==0xb000, context
                assert (regs['A'].value==0)==(script[-1]==0), context
                assert len(aborts)==sum(s!=0 for s in script) and len(restores)==len(script), context
                assert len(transfers)==sum(s!='seek' for s in script), context
                for op,drive,sector,track,dma in transfers:
                    assert (op,drive,sector,track)==(command,0x4b if cyl==0 else 0xcb,1,cyl), context
                    assert dma[6:8]==(size-1).to_bytes(2,'little') and dma[11:13]==b'\0\x60', context
                assert bytes(ram[0x6000:0x6000+size]) == buf
                if script[-1]==0:
                    assert (regs['H'].value<<8 | regs['L'].value) == 0x6000+size, context
                else:
                    assert ram[names['M2_LAST']]==255, context
                results.append({'case':title,'operation':'read' if command==0x80 else 'write',
                                'size':size,'attempts':len(attempts),'aborts':len(aborts),'return':regs['A'].value})
    return {'status':'PASS','disk_code_sha256':hashlib.sha256(disk).hexdigest(),
            'scope':'Real controller instructions, synthetic status/interrupt ports, observed DMA setup; guest media tests separately exercise the data transfer.','cases':results}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('artifacts',type=Path)
    p.add_argument('--z80pack',type=Path,default=Path.home()/'projects/git/z80pack')
    a=p.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        start=SHIM.index('BYTE io_in')
        end=SHIM.index('void end_bus_request',start)
        lib=cpu_library(Path(tmp),a.z80pack,SHIM[:start]+PORTS+SHIM[end:])
        print(json.dumps(check(a.artifacts,lib),indent=2))
