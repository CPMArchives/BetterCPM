"""Build a read-only BDOS 33 verifier for recorded data beyond sequential EOF."""
from pathlib import Path
import subprocess


def build_verifier(records, output, negative=False):
    lines = ['        ASEG', '        ORG 0100H', '        LD SP,STACKTOP']
    data = []
    for i, (name, record, expected) in enumerate(records):
        user, filename = name.split(':')
        assert user == '0' and len(expected) == 128 and 0 <= record < 65536
        stem, _, suffix = filename.upper().partition('.')
        fcb = bytes([2])+stem.ljust(8).encode()+suffix.ljust(3).encode()+bytes(21)+record.to_bytes(3,'little')
        assert len(fcb) == 36
        if negative and i == 0:
            expected = bytes([expected[0]^1])+expected[1:]
        lines += [f'        LD DE,FCB{i}', '        LD C,15', '        CALL 5',
                  '        CP 255', '        JP Z,FAIL', '        LD DE,DMA',
                  '        LD C,26', '        CALL 5', f'        LD DE,FCB{i}',
                  '        LD C,33', '        CALL 5', '        OR A', '        JP NZ,FAIL',
                  '        LD HL,DMA', f'        LD DE,DATA{i}', '        LD B,128',
                  f'LOOP{i}: LD A,(DE)', '        CP (HL)', '        JP NZ,FAIL',
                  '        INC DE', '        INC HL', f'        DJNZ LOOP{i}']
        for label, payload in [(f'FCB{i}', fcb), (f'DATA{i}', expected)]:
            data += [label+':']
            data += ['        DB '+','.join(str(x) for x in payload[j:j+16])
                     for j in range(0,len(payload),16)]
    lines += ['        LD DE,GOOD', '        JR PRINT', 'FAIL:   LD DE,BAD',
              'PRINT:  LD C,9', '        CALL 5', '        JP 0',
              "GOOD:   DB 'Random records PASS',13,10,'$'",
              "BAD:    DB 'Random records FAIL',13,10,'$'"]
    lines += data+['DMA:    DS 128', '        DS 128', 'STACKTOP:', '        END']
    source = output.with_suffix('.mac');source.write_text('\n'.join(lines)+'\n')
    subprocess.run([str(Path.home()/'bin/z80asm'),'-e32','-fb',f'-o{output}',str(source)],check=True)
    binary=output.read_bytes()
    if binary[:256] == bytes(256):output.write_bytes(binary[256:])
