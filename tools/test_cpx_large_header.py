#!/usr/bin/env python3
"""Qualify three-sector BCPX carriers without modifying the native loader."""
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
from pathlib import Path

from build_ccp import assemble
from build_cpx_module import make_module, relocation_offsets
from run_trs80_command import DEFAULT_EMULATOR
from test_disk_utilities import ROOT, keys, medium
from test_sysgen_install import screen
from test_z80pack_sysgen_install import session
from trs80gp_launch import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--platform', choices=('z80pack', 'model4'), required=True)
    parser.add_argument('--image-dir', type=Path)
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    (report / 'harness.py').write_bytes(Path(__file__).read_bytes())
    # Test both old boundaries and the new bounded builder capacity.
    for count in (232, 233, 488, 489, 744):
        carrier = make_module(name='BOUND', version=(0, 1), commands=['BOUND'],
                              linked_base=0x8000, code=bytes(2048),
                              relocations=list(range(0, count * 2, 2)))
        assert struct.unpack_from('<H', carrier, 24)[0] == ((48 + count * 2 + 511) // 512) * 512
    try:
        make_module(name='BOUND', version=(0, 1), commands=['BOUND'],
                    linked_base=0x8000, code=bytes(2048),
                    relocations=list(range(0, 745 * 2, 2)))
    except SystemExit as error:
        assert 'reserved area' in str(error)
    else:
        raise AssertionError('builder accepted an oversized relocation directory')

    source = (ROOT / 'src/cpx/hello.mac').read_text()
    source = source.replace('        LD      (HC_ARGPTR),DE',
                            '        LD      (HC_ARGPTR),DE\n        CALL    LH_CHECK', 1)
    probe = '''
LH_CHECK:
        LD HL,LH_WORDS
        LD DE,HC_MESSAGE
        LD BC,489
LH_LOOP:
        LD A,(HL)
        CP E
        JR NZ,LH_FAIL
        INC HL
        LD A,(HL)
        CP D
        JR NZ,LH_FAIL
        INC HL
        DEC BC
        LD A,B
        OR C
        JR NZ,LH_LOOP
        LD DE,LH_GOOD
        JR LH_PRINT
LH_FAIL:
        LD DE,LH_BAD
LH_PRINT:
        LD C,9
        JP BDOS
LH_GOOD: DB 13,10,'HEADER RELOCS PASS',13,10,'$'
LH_BAD: DB 13,10,'HEADER RELOCS FAIL',13,10,'$'
LH_WORDS:
'''+('        DW HC_MESSAGE\n' * 489)
    source = source.replace('        .DEPHASE', probe + '        .DEPHASE')
    source = source.replace('        CSEG\n        .PHASE  ', '        ASEG\n        ORG     ').replace('        .DEPHASE\n', '')
    (report / 'probe.mac').write_text(source)
    assembler = Path('/Users/nathanael/bin/z80asm')
    code = assemble(assembler, source, report / 'probe.bin', report / 'probe.lst', 0x8000)
    alternate = assemble(assembler, source.replace('CPXBASE         EQU     08000H',
                                                   'CPXBASE         EQU     08101H'),
                         report / 'alternate.bin', report / 'alternate.lst', 0x8101)
    offsets = relocation_offsets(code, alternate, 0x101)
    assert 488 < len(offsets) <= 744
    carrier = make_module(name='LARGE', version=(0, 1), commands=['HELLO'],
                          linked_base=0x8000, code=code, relocations=offsets)
    assert struct.unpack_from('<H', carrier, 24)[0] == 1536
    module = report / 'LARGE.CPX'
    module.write_bytes(carrier)
    commands = ['CPX UNLOAD RCP', 'CPX LOAD LARGE', 'HELLO FIRST',
                'HELLO SECOND', 'CPX UNLOAD LARGE', 'CPX LOAD LARGE', 'HELLO RELOAD']
    if args.platform == 'z80pack':
        assert args.image_dir, '--image-dir required for z80pack'
        shutil.copytree(args.image_dir / 'disks', report / 'disks')
        shutil.copy2(args.image_dir / 'diskdefs', report / 'diskdefs')
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default',
                        str(report / 'disks/drivea.dsk'), str(module), '0:LARGE.CPX'],
                       cwd=report, check=True)
        transcript = session(Path.home() / 'projects/git/z80pack/cpmsim/cpmsim',
                             report / 'disks', [(c.encode()+b'\r', b'A0>_ ', 60) for c in commands],
                             report / 'transcript.txt').decode(errors='replace')
        assert transcript.count('HEADER RELOCS PASS') == 3
    else:
        # Native SUBMIT avoids timing-sensitive entry of the individual commands.
        finish = b'\x11\x0b\x01\x0e\x09\xcd\x05\x00\xc3\x00\x00\r\nHEADER FINISH\r\n$'
        extras = [('LARGE.CPX', carrier), ('CPX.COM', (ROOT / 'build/utilities/CPX.COM').read_bytes()),
                  ('SUBMIT.COM', (ROOT / 'build/utilities/SUBMIT.COM').read_bytes()),
                  ('FINISH.COM', finish), ('CASE.SUB', ('\r\n'.join(commands+['FINISH'])+'\r\n').encode()+b'\x1a')]
        disk = report / 'a.dmk'
        disk.write_bytes(medium(extras))
        invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-d0', str(disk), '-id', '3000', '-it']
        invocation += keys('SUBMIT CASE\r')
        for suffix in ('FIRST', 'SECOND', 'RELOAD'):
            invocation += ['-itime', '0', '-iw', 'Hello from HELLO.CPX '+suffix, '-it']
        invocation += ['-itime', '0', '-iw', 'HEADER FINISH', '-id', '3000', '-it', '-ix']
        (report / 'invocation.json').write_text(json.dumps(invocation, indent=2)+'\n')
        run(invocation, cwd=report, timeout=900, check=True)
        snapshots = [screen(p) for p in sorted(report.glob('trs80-text-*.bin'))]
        transcript = '\n'.join(snapshots)
        (report / 'transcript.txt').write_text(transcript)
        assert 'HEADER FINISH' in snapshots[-1] and snapshots[-1].rstrip().endswith('A0>')
        for suffix in ('FIRST', 'SECOND', 'RELOAD'):
            assert any('HEADER RELOCS PASS' in t and 'Hello from HELLO.CPX '+suffix in t for t in snapshots),suffix
    assert 'HEADER RELOCS FAIL' not in transcript
    for suffix in ('FIRST', 'SECOND', 'RELOAD'):
        assert 'Hello from HELLO.CPX '+suffix in transcript
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS', 'platform': args.platform,
        'header_bytes': 1536, 'relocations': len(offsets), 'payload_bytes': len(code),
        'carrier_sha256': hashlib.sha256(carrier).hexdigest(),
        'checked_words_per_invocation': 489, 'successful_invocations': 3,
        'coverage': ['builder boundaries', 'initial load', 'WBOOT reconstruction', 'unload/reload'],
        'loader_changed': False}, indent=2)+'\n')
    print('Three-sector BCPX loading, relocation, WBOOT and reload: PASS')


if __name__ == '__main__':
    main()
