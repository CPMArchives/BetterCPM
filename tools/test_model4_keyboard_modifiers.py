#!/usr/bin/env python3
"""Qualify physical-key debounce and Model 4 punctuation through BIOS CONIN."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from add_cpm_file_to_dmk import add_file, extract_raw
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR, ROOT, key_args
from test_sysgen_install import screen
from trs80gp_launch import run

PROBE = "        ASEG\n        ORG 0100H\n        LD HL,0F800H\n        LD DE,TITLE\n        LD B,9\nREADY:  LD A,(DE)\n        LD (HL),A\n        INC HL\n        INC DE\n        DJNZ READY\nLOOP:   CALL READ\n        PUSH AF\n        RRCA\n        RRCA\n        RRCA\n        RRCA\n        CALL HEX\n        POP AF\n        CALL HEX\n        LD A,' '\n        CALL PRINT\n        JR LOOP\nREAD:   LD HL,(1)\n        LD DE,6\n        ADD HL,DE\n        JP (HL)\nHEX:    AND 0FH\n        ADD A,'0'\n        CP ':'\n        JR C,PRINT\n        ADD A,7\nPRINT:  LD HL,(POS)\n        LD (HL),A\n        INC HL\n        LD (POS),HL\n        RET\nPOS:    DW 0F8A0H\nTITLE:  DB 'KBD READY'\n        END\n"
EXPECTED = [0x3A, 0x2A, *range(0x21, 0x2C), 0x3C, 0x3D, 0x3E, 0x3F, 0x41, 0x42, 0x01, 0x5B, 0x5D, 0x0B, 0x0A]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, default=ROOT / 'build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    args = parser.parse_args()
    out = args.report.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = out / 'keyread.mac'
    source.write_text(PROBE, encoding='ascii')
    probe = out / 'KEYREAD.COM'
    subprocess.run([str(args.assembler), '-fb', f'-o{probe}', str(source)], check=True)
    original = args.image.read_bytes()
    raw = extract_raw(original)
    add_file(raw, 'KEYREAD.COM', probe.read_bytes())
    image = out / 'private.dmk'
    image.write_bytes(build(raw))
    command = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx',
               '-d0', str(image), '-id', '3000'] + key_args('KEYREAD\r')
    command += ['-itime', '3000', '-iw', 'KBD READY']
    # Modifier changes on a held physical key must not enqueue another byte.
    command += ['-ik','5','4','-id','12','-ik','7','1','-id','12',
                '-ik','5','0','-id','12','-ik','7','0','-id','12']
    command += ['-ik','7','1','-id','12','-ik','5','4','-id','12',
                '-ik','7','0','-id','12','-ik','5','0','-id','12']
    # Explicit modifier-only intervals avoid dependence on host keyboard layout.
    for row, column in [(4, n) for n in range(1, 8)] + [(5, n) for n in range(8)]:
        command += ['-ik','7','1','-id','12','-ik',str(row),f'{1 << column:X}',
                    '-id','12','-ik',str(row),'0','-id','12','-ik','7','0','-id','12']
    command += ['-ik','0','2','-id','12','-ik','0','6','-id','12',
                '-ik','0','4','-id','12','-ik','0','0','-id','12']
    command += ['-ik','7','4','-id','12','-ik','0','2','-id','12',
                '-ik','7','0','-id','12','-ik','0','0','-id','12']
    # Up/Down supply brackets; Ctrl-K/Ctrl-J retain history navigation.
    command += ['-ik','6','8','-id','12','-ik','6','0','-id','12',
                '-ik','6','10','-id','12','-ik','6','0','-id','12',
                '-ik','7','4','-ik','1','8','-id','12',
                '-ik','1','0','-id','12','-ik','7','0','-id','12',
                '-ik','7','4','-ik','1','4','-id','12',
                '-ik','1','0','-id','12','-ik','7','0','-id','12']
    command += ['-id', '100', '-it', '-ix']
    run(command, cwd=out, timeout=180)
    captured = screen(out / 'trs80-text-0.bin')
    (out / 'screen.txt').write_text(captured + '\n')
    expected = ' '.join(f'{byte:02X}' for byte in EXPECTED)
    observed = ' '.join(captured.splitlines()[2:]).strip()
    result = {'image_sha256': hashlib.sha256(original).hexdigest(),
              'expected': expected, 'observed': observed,
              'status': 'PASS' if observed == expected else 'FAIL'}
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    if observed != expected:
        raise SystemExit(f'BIOS keyboard bytes differ: {result}')
    print('PASS: modifier edges, shifted punctuation, overlapping A/B, Control release, brackets and history chords')


if __name__ == '__main__':
    main()
