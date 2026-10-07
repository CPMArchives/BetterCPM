#!/usr/bin/env python3
"""Qualify IOBYTE cold defaults and warm/reconstruction preservation."""
import argparse
import re
from pathlib import Path
from build_ccp import assemble
from test_bios import Z80
from test_z80pack_submit_xsub import run_case

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--image-dir', type=Path, required=True)
    p.add_argument('--simulator', type=Path,
                   default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    a = p.parse_args()
    # Execute the actual Model 4 stage-one prefix before its platform I/O.
    code = (ROOT/'build/trs80/stage1.bin').read_bytes()
    assert code[:5] == bytes.fromhex('3e95320300')
    m = Z80(b''); m.mem[3] = 0xFF
    m.mem[0x8000:0x8006] = code[:5]+b'\xc9'
    m.run(0x8000)
    assert m.mem[3] == 0x95
    # The actual Model 4 warm entry just delegates to the reloader. Stub its
    # destination to return, proving this entry does not initialize IOBYTE.
    bios = (ROOT/'build/bios/bios.bin').read_bytes()
    from system_layout import LAYOUT
    for value in (0, 0x6A, 0xFF):
        m = Z80(bios); m.mem[3] = value
        target = m.word(LAYOUT['BIOS']+4)
        assert m.mem[target] == 0xC3
        m.mem[m.word(target+1)] = 0xC9
        m.run(LAYOUT['BIOS']+3)
        assert m.mem[3] == value

    def files(work):
        result = {}
        for name, expected in [('IODEF',0x95),('IOKEEP',0x6A)]:
            source = f''' ORG 100H
 LD C,7
 CALL 5
 CP {expected}
 JR NZ,BAD
 LD A,(3)
 CP {expected}
 JR NZ,BAD
 LD DE,GOOD
 JR SHOW
BAD: LD DE,FAIL
SHOW: LD C,9
 CALL 5
 RET
GOOD: DB '{name} PASS',13,10,'$'
FAIL: DB '{name} FAIL',13,10,'$'
 END
'''
            result[name+'.COM'] = assemble(Path.home()/'bin/z80asm', source,
                work/(name+'.COM'),work/(name+'.lst'),0x100)
        result['IOSET.COM'] = assemble(Path.home()/'bin/z80asm',
            ' ORG 100H\n LD E,06AH\n LD C,8\n CALL 5\n RET\n END\n',
            work/'IOSET.COM',work/'IOSET.lst',0x100)
        return result

    body=r'''
send -s -- "IODEF\r"
expect -exact "IODEF PASS"
prompt
send -s -- "IOSET\r"
prompt
send -s -- "IOKEEP\r"
expect -exact "IOKEEP PASS"
prompt
send -s -- "RSX LOAD ECHO\r"
prompt
send -s -- "IOKEEP\r"
expect -exact "IOKEEP PASS"
prompt
send -s -- "BYE\r"
expect eof
'''
    for attempt in range(2):
        run_case(a.image_dir.resolve(),a.simulator.resolve(),
                 f'iobyte-{attempt}',files,body)
    print('PASS: Model 4 cold prefix/WBOOT; two cpmsim cold boots, GET/SET, WBOOT and RSX reconstruction')


if __name__ == '__main__':
    main()
