#!/usr/bin/env python3
"""Qualify portable VT52 with the Model 4 screen backend on disposable media."""
import argparse
import subprocess
import tempfile
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw, add_file, build
from build_trs80_boot import FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE, DIRECTORY_ENTRIES
from run_trs80_command import key_args, DEFAULT_EMULATOR

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,default=ROOT/'build/trs80/BetterCPM-Distribution-trs80gp-80T-DS-System.dmk')
    parser.add_argument('--emulator',type=Path,default=DEFAULT_EMULATOR)
    args=parser.parse_args()
    parent=ROOT/'build/vt52-development/model4';parent.mkdir(parents=True,exist_ok=True)
    out=Path(tempfile.mkdtemp(prefix='pages-',dir=parent))
    raw=extract_raw(args.image.read_bytes())
    names={b'R3PACK  ',b'VT52    ',b'VT52TST ',b'M4SCRN  ',b'STARTUP '}
    for index in range(DIRECTORY_ENTRIES):
        offset=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE+index*32
        if bytes(raw[offset+1:offset+9]) in names:raw[offset]=229
    for name,path in [('R3PACK.RSX','build/system/R3PACK.RSX'),
                      ('M4SCRN.RSX','build/screen-backends/M4SCRN.RSX'),
                      ('VT52.RSX','build/vt52-development/VT52.RSX'),
                      ('VT52TST.COM','build/vt52-development/VT52TST.COM')]:
        add_file(raw,name,(ROOT/path).read_bytes())
    startup=b'VER /BANNER\r\nRSX LOAD M4SCRN\r\nRSX LOAD VT52\r\nVT52TST\r\nRSX UNLOAD VT52\r\nRSX UNLOAD M4SCRN\r\nRSX LIST\r\n\x1a'
    add_file(raw,'STARTUP.SUB',startup)
    image=out/'private-system.dmk';image.write_bytes(build(bytes(raw)))
    # SUBMIT serializes load/exercise/unload. Only the utility's three
    # physical keypresses are supplied by the emulator, avoiding races with
    # floppy operations and transient text during warm return.
    command=[str(args.emulator),'-m4','-batch','-turbo','-d0',str(image),'-itime','15000']
    command+=['-iw','Press a key to continue.','-id','120','-it','-ics']
    command+=key_args(' ')+['-iw','Parser reset:','-iw','Press a key to continue.','-id','120','-it','-ics']
    command+=key_args(' ')+['-iw','VT52 erase tests:','-iw','Press a key to continue.','-id','120','-it','-ics']
    command+=key_args(' ')+['-iw','No RSXs loaded','-iw','TPA available: 53K','-id','120','-it','-ics','-ix']
    subprocess.run(command,cwd=out,check=True,timeout=180)
    check_captures(out)
    print(f'PASS: trs80gp portable VT52 identification, screen positions, tab, margin, reset, erase and unload/53K; {out}')


def check_captures(out):
    captures=sorted(out.glob('trs80-text-*.bin'))
    assert len(captures)==4,captures
    page=[bytes(c&127 for c in p.read_bytes()[:1920]) for p in captures]
    marker=b'Marker: row 5, column 10.'
    assert page[0][410:410+len(marker)]==marker
    assert page[0][568:570]==b'AB'
    assert page[0][878:880]==b'AC'
    assert b'Parser reset: readable text' in page[1]
    assert page[2][320:400]==b'EOL KEEP'+b' '*72
    assert page[2][480:560]==b'EOS KEEP'+b' '*72
    assert b'No RSXs loaded' in page[3] and b'TPA available: 53K' in page[3]



if __name__=='__main__':main()
