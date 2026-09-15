#!/usr/bin/env python3
"""Check the normalized default format and its host-image mappings."""
from pathlib import Path
from fdf_format import select_fdf
ROOT=Path(__file__).resolve().parents[1]
f=select_fdf(ROOT/'third_party/montezuma/DISK.FDF','California Computer Systems (40T, DS, DD, 332K)')
assert (f.cylinders,f.sides,f.physical_sectors,f.sector_bytes)==(40,2,18,256)
assert (f.image_bytes,f.reserved_records,f.block_bytes,f.dsm+1)==(368640,216,2048,166)
assert len(f.binding(3))==64 and f.binding(3)[0]==3
m=f.raw_record_map();assert len(m)==36 and sorted(m)==list(range(36))
print('PASS: CCS 40T DS DD FDF normalization, binding, and raw record map')
