#!/usr/bin/env python3
"""Qualify STAT $S against a native Model 4 random-write fixture."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from add_cpm_file_to_dmk import extract_raw
from build_ccp import assemble
from build_trs80_boot import FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE, DIRECTORY_ENTRIES
from run_trs80_command import DEFAULT_EMULATOR
from test_disk_utilities import ROOT, medium, keys
from test_sysgen_install import screen
from trs80gp_launch import run

PROBE = '''        ORG 100H
        LD HL,80H
        LD B,128
FILL:   LD (HL),0A5H
        INC HL
        DJNZ FILL
        LD DE,FCB
        LD C,22
        CALL 5
        CP 0FFH
        JR Z,BAD
        LD A,2
        LD (FCB+34),A
        LD DE,FCB
        LD C,34
        CALL 5
        OR A
        JR NZ,BAD
        LD DE,FCB
        LD C,16
        CALL 5
        CP 0FFH
        JR Z,BAD
        LD DE,GOOD
        JR PRINT
BAD:    LD DE,FAIL
PRINT:  LD C,9
        CALL 5
        JP 0
GOOD:   DB 'SPARSE READY',13,10,'$'
FAIL:   DB 'SPARSE FAILED',13,10,'$'
FCB:    DB 0,'SPARSE  DAT'
        REPT 24
        DB 0
        ENDM
        END
'''


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)
    stat = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    (report / 'STAT.COM').write_bytes(stat)
    (report / 'sparse.mac').write_text(PROBE)
    probe = assemble(Path.home() / 'bin/z80asm', PROBE, report / 'SPMAKE.COM', report / 'sparse.lst', 0x100)
    disk = report / 'system.dmk'
    disk.write_bytes(medium((('STAT.COM', stat), ('SPMAKE.COM', probe), ('MULTI.DAT', bytes(161 * 128)))))

    def campaign(name, steps):
        work = report / name
        work.mkdir()
        invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-d0', str(disk), '-id', '3000']
        for command, completion in steps:
            invocation += keys(command + '\r') + ['-itime', '0', '-iw', completion,
                                                  '-iw', 'A0> ', '-id', '500', '-it']
        invocation += ['-ix']
        (work / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
        run(invocation, cwd=work, check=True, timeout=75)
        captures = sorted(work.glob('trs80-text-*.bin'), key=lambda path: int(path.stem.rsplit('-', 1)[1]))
        assert len(captures) == len(steps)
        results = []
        for capture, (command, _) in zip(captures, steps):
            text = screen(capture)
            capture.with_suffix('.txt').write_text(text)
            assert re.search(r'A0>\s*$', text.rstrip()), text
            if command == 'SPMAKE':
                # Require the creator's unique completion marker without
                # depending on retention of its earlier command echo.
                assert 'SPARSE READY' in text, text
                results.append(text)
            else:
                assert 'A0>' + command in text, text
                results.append(text.rsplit('A0>' + command, 1)[1])
        return results

    created = campaign('create', [('SPMAKE', 'SPARSE READY')])[0]
    assert 'SPARSE READY' in created and 'SPARSE FAILED' not in created
    before = disk.read_bytes()
    (report / 'before-inspection.dmk').write_bytes(before)
    raw = extract_raw(before)
    start = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
    entries = [raw[at:at + 32] for at in range(start, start + DIRECTORY_ENTRIES * 32, 32)
               if raw[at] == 0 and bytes(value & 127 for value in raw[at + 1:at + 12]) == b'SPARSE  DAT']
    assert len(entries) == 2 and sum(entry[15] for entry in entries) == 1, [entry.hex() for entry in entries]
    blocks = {int.from_bytes(entry[at:at + 2], 'little') for entry in entries for at in range(16, 32, 2)} - {0}
    assert len(blocks) == 1, blocks
    sparse, regular = campaign('inspect', [('STAT SPARSE.DAT $S', 'Bytes Remaining'),
                                          ('STAT MULTI.DAT $S', 'Bytes Remaining')])
    assert re.search(r'00513 +00001 Recs +00002K Bytes +00002 Ext R/W A:SPARSE +\.DAT', sparse), sparse
    assert re.search(r'00161 +00161 Recs +00022K Bytes +00002 Ext R/W A:MULTI +\.DAT', regular), regular
    assert disk.read_bytes() == before, 'STAT inspection modified sparse media'
    (report / 'evidence.json').write_text(json.dumps({
        'result': 'PASS', 'logical_records': 513, 'recorded_records': 1,
        'allocated_kib': 2, 'physical_entries': 2, 'inspection_unchanged': True,
        'stat_sha256': digest(stat), 'probe_sha256': digest(probe),
        'media_sha256': digest(before), 'emulator_sha256': digest(DEFAULT_EMULATOR.read_bytes()),
    }, indent=2) + '\n')
    print('Model 4 STAT sparse/ordinary $S, raw extent/allocation checks and unchanged inspection passed')


if __name__ == '__main__':
    main()
