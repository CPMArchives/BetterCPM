#!/usr/bin/env python3
"""Prove the independent disk audit rejects wrong users, files and allocations."""
import argparse
from pathlib import Path
from build_utilities_disk import COMPONENTS
from build_z80pack_image import DEFAULT_FORMAT
from fdf_format import select_fdf
from test_utilities_inventory import inspect
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--image',type=Path,required=True);a=p.parse_args()
    files={n:(a.artifacts/path).read_bytes() for n,path in COMPONENTS.items()}
    fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT);raw=a.image.read_bytes();mapping=fmt.raw_record_map()
    def position(record):
        track,slot=divmod(record,fmt.spt);return (track*fmt.spt+mapping[slot])*128
    directory=position(fmt.reserved_records);first=raw[directory:directory+32]
    block=first[16];data=position(fmt.reserved_records+(block<<fmt.bsh))
    inspect(raw,fmt,files)
    def wrong_user(b):b[directory]=7
    def wrong_name(b):b[directory+1]=ord('Z')
    def reserved_block(b):b[directory+16]=0
    def changed_code(b):b[data]^=255
    def duplicate(b):
        for i in range(fmt.drm+1):
            at=position(fmt.reserved_records+i//4)+(i%4)*32
            if b[at]==0xe5:b[at:at+32]=first;return
        raise AssertionError('no empty test slot')
    for mutate in (wrong_user,wrong_name,reserved_block,changed_code,duplicate):
        damaged=bytearray(raw);mutate(damaged)
        try:inspect(bytes(damaged),fmt,files)
        except AssertionError:continue
        raise AssertionError('invalid disk accepted: '+mutate.__name__)
    print('PASS: five malformed inventory, allocation and payload cases rejected')


if __name__=='__main__':main()
