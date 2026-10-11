#!/usr/bin/env python3
"""Qualify actual Model 4 /D writes and shared-block preservation on a private DMK."""
import argparse
import json
import struct
from pathlib import Path
from test_disk_utilities import ROOT, medium, keys
from test_sysgen_install import screen
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build, SECTOR_SIZE
from build_trs80_boot import FILESYSTEM_FIRST_SECTOR, DIRECTORY_ENTRIES


def main():
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);p.add_argument('--verify-existing',action='store_true');a=p.parse_args()
    w=a.report.resolve();disk=w/'a.dmk';directory=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
    if not a.verify_existing:
        w.mkdir(parents=True,exist_ok=False)
        extras=[('WIPE.DAT',b'W'*128),('SHARED.DAT',b'S'*4096),('KEEP.DAT',b'K'*2048),('RONLY.DAT',b'R'*128)]
        extras += [(n,(ROOT/'build/utilities'/n).read_bytes()) for n in ('ERA.COM','SUBMIT.COM')]
        commands=[':ERA /D /Y WIPE.DAT', ':ERA /D /Y SHARED.DAT', ':ERA /D /Y /R RONLY.DAT[$RO]', 'FINISH']
        extras += [('CASE.SUB', ('\r\n'.join(c.replace('$','$$') for c in commands)+'\r\n').encode()+b'\x1a')]
        finish=b'\x11\x0b\x01\x0e\x09\xcd\x05\x00\xc3\x00\x00\r\nERA FINISH\r\n$'
        extras += [('FINISH.COM',finish)]
        raw=extract_raw(medium(extras));selected={};keep=None
        for offset in range(directory,directory+DIRECTORY_ENTRIES*32,32):
            name=bytes(v&127 for v in raw[offset+1:offset+12])
            if name in (b'WIPE    DAT',b'SHARED  DAT',b'RONLY   DAT'):selected[name.decode()]=offset
            if name==b'KEEP    DAT':keep=offset;raw[offset]=2
            if name==b'RONLY   DAT':raw[offset+9]|=128
        assert keep is not None and len(selected)==3
        shared_block=struct.unpack_from('<H',raw,keep+16)[0]
        struct.pack_into('<H',raw,selected['SHARED  DAT']+18,shared_block)
        (w/'before.raw').write_bytes(raw)
        (w/'fixture.json').write_text(json.dumps({'entries':selected,'keep':keep,'shared_block':shared_block},indent=2)+'\n')
        disk.write_bytes(build(raw))
        invocation=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(disk),'-id','3000']
        invocation+=keys('SUBMIT CASE\r')+['-itime','0','-iw','ERA FINISH','-id','3000','-it','-ix']
        (w/'invocation.json').write_text(json.dumps(invocation,indent=2)+'\n')
        run(invocation,cwd=w,timeout=900,check=True)
    text='\n'.join(screen(p) for p in sorted(w.glob('trs80-text-*.bin')))
    (w/'transcript.txt').write_text(text)
    assert 'ERA FINISH' in text and 'SHARED BLOCKS RETAINED' in text.upper(),text
    before=(w/'before.raw').read_bytes();after=extract_raw(disk.read_bytes());fixture=json.loads((w/'fixture.json').read_text())
    shared=fixture['shared_block'];keep=fixture['keep']
    assert after[keep:keep+32]==before[keep:keep+32]
    blockbase=directory+shared*2048
    assert after[blockbase:blockbase+2048]==before[blockbase:blockbase+2048]
    for name,offset in fixture['entries'].items():
        assert after[offset:offset+32]==bytes((229,))+bytes(31),(name,after[offset:offset+32])
        blocks=set(struct.unpack_from('<8H',before,offset+16))-{0,shared}
        for block in blocks:
            start=directory+block*2048
            assert after[start:start+2048]==bytes(2048),(name,block)
    print('PASS Model 4 /D: zeroed unshared blocks, E5/zero scrub, other-user shared data and metadata preserved')

if __name__=='__main__':main()
