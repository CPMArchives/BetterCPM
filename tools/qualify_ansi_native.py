#!/usr/bin/env python3
"""Qualify production portable ANSI visual pages and unload on real trs80gp."""
import argparse
import tempfile
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw,add_file,build
from build_trs80_boot import FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
from run_trs80_command import key_args,DEFAULT_EMULATOR
from trs80gp_launch import run as launch
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,default=ROOT/'build/trs80/BetterCPM-Distribution-trs80gp-80T-DS-System.dmk')
    parser.add_argument('--emulator',type=Path,default=DEFAULT_EMULATOR)
    args=parser.parse_args()
    parent=ROOT/'build/ansi-development/native-campaign';parent.mkdir(parents=True,exist_ok=True)
    out=Path(tempfile.mkdtemp(prefix='pages-',dir=parent))
    raw=extract_raw(args.image.read_bytes())
    for index in range(DIRECTORY_ENTRIES):
        offset=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE+index*32
        if raw[offset+1:offset+9] in [b'R3PACK  ',b'ANSI    ',b'ANSITST ',b'M4SCRN  ',b'STARTUP ']:raw[offset]=229
    for name,path in [('R3PACK.RSX','build/system/R3PACK.RSX'),('M4SCRN.RSX','build/screen-backends/M4SCRN.RSX'),('ANSI.RSX','build/ansi-development/ANSI.RSX'),('ANSITST.COM','build/ansi-development/ANSITST.COM')]:
        add_file(raw,name,(ROOT/path).read_bytes())
    startup=':VER /BANNER\r\nRSX LOAD M4SCRN\r\nRSX LOAD ANSI\r\nANSITST\r\nRSX UNLOAD ANSI\r\nRSX UNLOAD M4SCRN\r\nRSX LIST\r\n'
    add_file(raw,'STARTUP.SUB',startup.encode()+b'\x1a')
    image=out/'private-system.dmk';image.write_bytes(build(bytes(raw)))
    command=[str(args.emulator),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-itime','15000',
             '-iw','Marker: row 5','-iw','Press a key to continue.','-id','120','-it','-ics']
    command+=key_args(' ',delay=60)+['-iw','Parser reset: readable text','-iw','Press a key to continue.','-id','120','-it','-ics']
    command+=key_args(' ',delay=60)+['-iw','No RSXs loaded','-iw','TPA available: 53K','-id','120','-it','-ics','-ix']
    launch(command,cwd=out,check=True,timeout=240)
    captures=sorted(out.glob('trs80-text-*.bin'));assert len(captures)==3,captures
    pages=[path.read_bytes()[:1920] for path in captures]
    text=[bytes(c&127 for c in page) for page in pages]
    assert text[0][5*80+10:5*80+35]==b'Marker: row 5, column 10.'
    assert text[0][7*80:7*80+21]==b'Normal Reverse Normal'
    assert all(c&128 for c in pages[0][7*80+7:7*80+14])
    assert not any(c&128 for c in pages[0][7*80:7*80+6])
    assert text[0][9*80:10*80].rstrip()==b'Erase KEEP'
    assert b'Parser reset: readable text' in text[1]
    assert b'No RSXs loaded' in text[2] and b'TPA available: 53K' in text[2]
    print(f'PASS native Model 4 portable ANSI: positioning, reverse, erasure, parser reset and unload/53K; {out}')


if __name__=='__main__':main()
