"""Listing page-header encoding must not corrupt ASCII symbol extraction."""
from pathlib import Path
import tempfile
from build_z80pack_image import symbols

with tempfile.TemporaryDirectory() as folder:
    listing=Path(folder)/'probe.lst'
    listing.write_bytes(b'\fSource file: \xaa\x12\n1000  c9  1 1 FIRST: RET\n'
                        b'\fSource file: \xff\n1234  00  2 2 SECOND: DB 0\n')
    assert symbols(listing)=={'FIRST':0x1000,'SECOND':0x1234}
print('PASS ASCII symbols with non-UTF-8 assembler page headers')
