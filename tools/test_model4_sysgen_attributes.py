#!/usr/bin/env python3
"""Verify Model 4 SYSTEM.SYS installation preserves all attribute combinations."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw
from build_ccp import assemble
from build_montezuma_extended_790k import build, RAW_SIZE
from build_system_package import compose
from build_trs80_boot import install_files, FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE
from run_trs80_command import DEFAULT_EMULATOR, key_args
from test_disk_utilities import medium
import test_sysgen_install
from trs80gp_launch import run as run_trs80gp

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    # Use the established physical-first compatible B: setup, preserving its listing.
    test_sysgen_install.OUT = report
    setup = test_sysgen_install.setup_program()
    checks = []
    fcbs = []
    for mask in range(8):
        checks.append(f'''        LD DE,FCB{mask}
        LD C,17
        CALL 5
        CP 0FFH
        JP Z,BAD
        LD L,A
        LD H,0
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        LD DE,81H
        ADD HL,DE
        LD DE,FCB{mask}+1
        LD B,11
        CALL COMPARE
''')
        name = f'ATTR{mask}   '.encode() + bytes(ord(c) | (128 if mask & (1 << n) else 0)
                                               for n,c in enumerate('DAT'))
        fcbs.append(f'FCB{mask}: DB 2,' + ','.join(map(str,name)) + '\n        REPT 24\n        DB 0\n        ENDM\n')
    source = '''        ASEG
        ORG 100H
        LD SP,4000H
        LD DE,80H
        LD C,26
        CALL 5
''' + ''.join(checks) + '''        LD DE,OK
        JR PRINT
COMPARE:
        LD A,(DE)
        CP (HL)
        JP NZ,BAD
        INC DE
        INC HL
        DJNZ COMPARE
        RET
BAD:    LD DE,FAIL
PRINT:  LD C,9
        CALL 5
        JP 0
OK:     DB 'ATTRIBUTE MEDIA PASS',13,10,'$'
FAIL:   DB 'ATTRIBUTE MEDIA FAIL',13,10,'$'
''' + ''.join(fcbs) + '        END\n'
    (report / 'attrcheck.mac').write_text(source)
    binary = report / 'ATTRCHK.COM'
    assemble(Path.home() / 'bin/z80asm', source, binary, report / 'attrcheck.lst', 0x100)
    # DS emits FF-filled reservations in this assembler. CP/M extent fields
    # must start at zero; check the emitted FCBs before launching any emulator.
    listing = (report / 'attrcheck.lst').read_text()
    emitted = binary.read_bytes()
    for mask in range(8):
        match = re.search(rf'^([0-9a-f]{{4}}).*\bFCB{mask}:', listing, re.M)
        assert match is not None
        offset = int(match[1], 16) - 0x100
        assert emitted[offset+12:offset+36] == bytes(24), 'FCB state is not initialized'
    package, _ = compose()
    (report / 'SYSTEM.SYS').write_bytes(package)
    boot = medium((('SETBSYS.COM', setup), ('ATTRCHK.COM', binary.read_bytes()),
                   ('SYSTEM.SYS', package)))
    raw = bytearray([0xE5]) * RAW_SIZE
    payload = bytes(range(128))
    install_files(raw, [(f'ATTR{mask}.DAT', payload) for mask in range(8)])
    reserved = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
    for mask in range(8):
        offset = reserved + mask * 32
        assert raw[offset+1:offset+12] == f'ATTR{mask}   DAT'.encode()
        for n in range(3):
            if mask & (1 << n):
                raw[offset+9+n] |= 128
    target = build(bytes(raw))
    (report / 'source.dmk').write_bytes(boot)
    (report / 'target-before.dmk').write_bytes(target)
    (report / 'target.dmk').write_bytes(target)
    base = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo',
        '-d0', str(report / 'source.dmk'), '-d1', str(report / 'target.dmk'), '-id', '3000']
    inspect = report / 'inspect'
    inspect.mkdir()
    inspection = base + key_args('SETBSYS\r') + ['-id', '3000']
    inspection += key_args('ATTRCHK\r') + ['-id', '3000', '-it', '-ix']
    (inspect / 'invocation.json').write_text(json.dumps(inspection, indent=2)+'\n')
    run_trs80gp(inspection, cwd=inspect, check=True, timeout=30)
    text = test_sysgen_install.screen(inspect / 'trs80-text-0.bin')
    (inspect / 'inspection.txt').write_text(text)
    assert 'B SYSTEM READY' in text, text
    assert 'ATTRIBUTE MEDIA PASS' in text and 'ATTRIBUTE MEDIA FAIL' not in text, text
    # Do not proceed to installation if native fixture inspection fails.
    invocation = base + key_args('SETBSYS\r') + ['-id', '3000', '-it']
    invocation += key_args('SYSGEN SYSTEM.SYS B:\r') + ['-id', '3000', '-it']
    invocation += key_args('Y') + ['-id', '35000', '-it', '-ix']
    (report / 'invocation.json').write_text(json.dumps(invocation, indent=2)+'\n')
    run_trs80gp(invocation, cwd=report, check=True, timeout=80)
    texts = []
    for path in sorted(report.glob('trs80-text-*.bin')):
        text = test_sysgen_install.screen(path)
        path.with_suffix('.txt').write_text(text)
        texts.append(text)
    assert any('B SYSTEM READY' in text for text in texts), texts
    assert any('System installed and verified' in text for text in texts), texts
    after = extract_raw((report / 'target.dmk').read_bytes())
    assert after[:reserved] != raw[:reserved]
    assert after[reserved:] == raw[reserved:], 'installation changed filesystem metadata/payload'
    cold = report / 'cold'
    cold.mkdir()
    cold_invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo',
        '-d0', str(report / 'target.dmk'), '-id', '4000', '-it', '-ix']
    (cold / 'invocation.json').write_text(json.dumps(cold_invocation, indent=2)+'\n')
    run_trs80gp(cold_invocation, cwd=cold, check=True, timeout=25)
    text = test_sysgen_install.screen(cold / 'trs80-text-0.bin')
    (cold / 'boot.txt').write_text(text)
    assert 'A0>' in text, text
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS',
        'package_sha256': hashlib.sha256(package).hexdigest(),
        'emulator_sha256': hashlib.sha256(DEFAULT_EMULATOR.read_bytes()).hexdigest(),
        'filesystem_sha256': hashlib.sha256(after[reserved:]).hexdigest(),
        'attributes': list(range(8)), 'reserved_bytes': reserved}, indent=2)+'\n')
    print('PASS: Model 4 native attribute inspection, SYSTEM.SYS filesystem preservation, installed cold boot')


if __name__ == '__main__':
    main()
