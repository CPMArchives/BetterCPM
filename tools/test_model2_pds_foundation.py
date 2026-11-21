#!/usr/bin/env python3
"""Focused emitted Model II system checks; physical disk transfer is controlled."""
import argparse
from pathlib import Path
import tempfile
from version_metadata import rows
from test_z80pack_submit_xsub import input_probe

from test_model2_external import (Session, WINDOW, KEYS, ADVANCE, cpu_library,
                                  SHIM, disk)


def check(artifacts, work, z80pack):
    window=WINDOW.replace('int enable =', 'if(port!=0xff)return;\n    int enable =')
    shim=(SHIM[:SHIM.index('BYTE io_in')]+window+KEYS+
          SHIM[SHIM.index('void end_bus_request'):]+ADVANCE)
    library=cpu_library(work,z80pack,shim)
    # The first record executes; remaining records deliberately fill the TPA.
    code=bytes.fromhex('1109010e09cd0500c9')+b'NATIVE FIT PASS\r\n$'
    payload=code.ljust(57344,b'\x76')
    scratch=disk([('FIT.COM',payload),('OVER.COM',payload+bytes(128)),
                  ('ONE.SUB',b'B:FIT\r\nVER\r\n'),
                  ('INPUT.COM',input_probe(work)),
                  ('XSUB.COM',(artifacts.parent/'utilities/XSUB.COM').read_bytes()),
                  ('BATCHIO.RSX',(artifacts.parent/'rsx/BATCHIO.RSX').read_bytes()),
                  ('IN.SUB',b'B:XSUB B:\r\nB:INPUT\r\nBATCHFULL\r\nVER\r\n')])
    guest=Session(library,artifacts,
                  [(artifacts/'Model-II-System-candidate.imd').read_bytes(),scratch])
    version=next(row['implementation_version'] for row in rows() if row['component']=='BetterCP/M')
    transcript=[]
    steps=[(b'STAT MEM\r',b'57344 bytes'),
           (b'B:FIT\r',b'NATIVE FIT PASS'),
           (b'B:OVER\r',b'FILE WILL NOT FIT'),
           (b'STAT MEM\r',b'57344 bytes'),
           (b'SUBMIT B:ONE\r',b'NATIVE FIT PASS'),
           (b'RSX LOAD NDR\r',b'A0>'),
           (b'STAT MEM\r',b'Loaded RSX allocation'),
           (b'RSX UNLOAD NDR\r',b'A0>'),
           (b'STAT MEM\r',b'57344 bytes'),
           (b'CONFIG\r',b'Your choice:'),
           (b'F',b'Active H/M/V bytes: 192 0 0'),
           (b'\x03\x03',b'A0>'),
           (b'CONFIG\r',b'Your choice:'),
           (b'F',b'Active H/M/V bytes: 192 0 0'),
           (b'\x03\x03',b'A0>'),
           (b'SUBMIT B:IN\r',b'INPUT OK'),
           (b'RSX UNLOAD BATCHIO\r',b'A0>'),
           (b'STAT MEM\r',b'57344 bytes')]
    for command,witness in steps:
        text=guest.step(command,witness)
        transcript.append(text)
        assert b'RSX module or profile error' not in text
        assert b'INPUT FAILED' not in text
        if b'OVER' in command:
            assert b'NATIVE FIT PASS' not in text
        if command==b'SUBMIT B:ONE\r':
            assert text.index(b'NATIVE FIT PASS')<text.index(b'BetterCP/M '+version.encode('ascii'))
    import json
    system=json.loads((artifacts.parent/'profile/context.json').read_text())['symbols']['LY_SYS']
    assert bytes(guest.ram[system-12:system-8])==b'PD\x02\x0c'
    return b'\n'.join(transcript)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifacts',type=Path)
    parser.add_argument('--z80pack',type=Path,default=Path.home()/'projects/git/z80pack')
    parser.add_argument('--transcript',type=Path,required=True)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        result=check(args.artifacts.resolve(),Path(temporary),args.z80pack)
    args.transcript.write_bytes(result)
    print('PASS Model II checked boot, exact fit/overflow, SUBMIT/XSUB, NDR load/unload and CONFIG warm reentry; physical disk transfer controlled')
