#!/usr/bin/env python3
"""Reject bindings that would overflow cpmsim's resident checksum vectors."""
from pathlib import Path
import argparse
import tempfile

from build_ccp import assemble
from fdf_format import select_fdf
from system_layout import LAYOUT
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    args = parser.parse_args()
    # Assemble the actual platform overlay, including the shared CPX tail.
    # BIOS link addresses are unused by these configuration-only requests.
    source = (ROOT/'src/platform/z80pack/config.mac').read_text()
    source = source.replace('        INCLUDE bioslinks.inc', '\n'.join(
        name + ' EQU 07000H' for name in
        ('BIO_DRIVE', 'BIO_TRACK', 'BIO_SECTOR', 'BIO_DMA', 'BIO_QUART')))
    source = source.replace('        INCLUDE cpxlinks.inc',
                            'EX_RETURN EQU 07010H\nBCX_MVAL EQU 07020H')
    source = source.replace('ZP_PHYSICAL EQU 0FFFFH', 'ZP_PHYSICAL EQU 07100H')
    tail = (ROOT/'src/bios/config.mac').read_text().split('CPTCOUNT EQU',1)[1].split('CF_GETPH:',1)[0]
    source += 'CPTCOUNT EQU' + tail + '\n        END\n'
    with tempfile.TemporaryDirectory(prefix='bettercpm-csv-') as directory:
        directory = Path(directory)
        image = assemble(args.assembler, source, directory/'config.bin',
                         directory/'config.lst', LAYOUT['CONFIG'])
    assert len(image) <= 1024
    fmt = select_fdf(ROOT/'metadata/DISK.FDF', 'MMF017')
    original = bytes((i*37+11)&255 for i in range(576))
    for cks, expected in ((0,0), (16,0), (32,0), (33,2), (48,2), (255,2), (256,1)):
        cpu = Z80(b'')
        cpu.mem[LAYOUT['CONFIG']:LAYOUT['CONFIG']+len(image)] = image
        base = LAYOUT['TABLES']
        cpu.mem[base:base+len(original)] = original
        cpu.mem[0x7100:0x7118] = bytes((5,80,2,0,0,0))*4
        request = bytearray(bytes((1,)) + fmt.binding(1))
        request[13:15] = cks.to_bytes(2,'little')
        cpu.mem[0x7200:0x7200+len(request)] = request
        cpu.ix = 0x7200
        # Match Z_API's saved IX before dispatching overlay operation 4.
        entry = LAYOUT['CONFIG']+3
        cpu.mem[0x6000:0x6005] = bytes((0xdd,0xe5,0xc3,entry&255,entry>>8))
        cpu.run(0x6000, limit=100000)
        assert cpu.hl == expected, (cks, cpu.hl)
        after = bytes(cpu.mem[base:base+len(original)])
        if expected:
            assert after == original, ('rejected binding modified resident tables', cks)
        else:
            wanted = bytearray(original)
            wanted[96:160] = request[1:]
            assert after == wanted, ('accepted binding changed unrelated state', cks)
        assert cpu.ix == 0x7200
    print('PASS: CKS 0/16/32 accepted; 33/48/255 rejected, 256 invalid; rejected bindings preserve all tables and vectors')


if __name__ == '__main__':
    main()
