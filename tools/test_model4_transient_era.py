#!/usr/bin/env python3
"""Qualify transient ERA on a disposable Model 4 image; inspect directory state."""
import argparse
import json
from pathlib import Path
from test_disk_utilities import ROOT, medium, keys
from test_sysgen_install import screen
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build, SECTOR_SIZE
from build_trs80_boot import FILESYSTEM_FIRST_SECTOR, DIRECTORY_ENTRIES


def main():
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True)
    p.add_argument('--verify-existing',action='store_true');a=p.parse_args()
    w=a.report.resolve()
    if not a.verify_existing:w.mkdir(parents=True,exist_ok=False)
    disk=w/'a.dmk';directory=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
    names=('NORMAL.DAT','READONLY.DAT','SYSTEM.DAT','BOTH.DAT','KEEP.DAT')
    if not a.verify_existing:
        extras=[(n,b'X'*(33024 if n=='NORMAL.DAT' else 128)) for n in names]
        extras += [(n,(ROOT/'build/utilities'/n).read_bytes()) for n in ('ERA.COM','SUBMIT.COM')]
        commands=[':ERA /VER', 'CHECK', ':ERA /Y [A0,E0]:KEEP.DAT',
                  ':ERA /Y A0:*.DAT', ':ERA /Y A0:READONLY.DAT[$RO]',
                  ':ERA /Y /R A0:*.DAT[$SYS,$RO]',
                  ':ERA /Y /R A0:BOTH.DAT[!$DIR+!$RW]', 'FINISH']
        # Keep fixture outside the destructive test selection to prove rejection.
        commands[3]=':ERA /Y A0:N*.DAT'
        extras += [('CASE.SUB', ('\r\n'.join(c.replace('$','$$') for c in commands)+'\r\n').encode()+b'\x1a')]
        finish=b'\x11\x0b\x01\x0e\x09\xcd\x05\x00\xc3\x00\x00\r\nERA FINISH\r\n$'
        extras += [('FINISH.COM',finish),('CHECK.COM',finish.replace(b'ERA FINISH',b'ERA CHECK!'))]
        raw=extract_raw(medium(extras))
        for offset in range(directory,directory+DIRECTORY_ENTRIES*32,32):
            name=bytes(v&127 for v in raw[offset+1:offset+12])
            if name in (b'READONLYDAT',b'BOTH    DAT'):raw[offset+9]|=128
            if name in (b'SYSTEM  DAT',b'BOTH    DAT'):raw[offset+10]|=128
        disk.write_bytes(build(raw))
        invocation=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(disk),'-id','3000']
        invocation+=keys('SUBMIT CASE\r')+['-itime','0','-iw','ERA CHECK!','-it','-iw','ERA FINISH','-id','3000','-it','-ix']
        (w/'invocation.json').write_text(json.dumps(invocation,indent=2)+'\n')
        run(invocation,cwd=w,timeout=900,check=True)
    text='\n'.join(screen(p) for p in sorted(w.glob('trs80-text-*.bin')))
    (w/'transcript.txt').write_text(text)
    assert 'ERA FINISH' in text and 'INVALID DRIVE' in text
    assert 'BETTERCP/M ERA 1.0 (BUILD 002)' in text.upper()
    raw=extract_raw(disk.read_bytes());remaining=set()
    for offset in range(directory,directory+DIRECTORY_ENTRIES*32,32):
        if raw[offset]!=0:continue
        name=bytes(v&127 for v in raw[offset+1:offset+12])
        remaining.add(name[:8].decode().rstrip()+'.'+name[8:].decode().rstrip())
    assert remaining.intersection(names)=={'KEEP.DAT'},remaining
    print('PASS Model 4 transient ERA: admission, /R, invalid-domain atomicity, multi-extent erase')


if __name__=='__main__':main()
