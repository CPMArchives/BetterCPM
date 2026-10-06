#!/usr/bin/env python3
"""Qualify native attribute updates against raw metadata and host extraction."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from build_ccp import assemble
from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]
PROBE = """        ASEG
        ORG 100H
        LD SP,4000H
        LD A,(80H)
        LD C,A
        LD B,0
        LD HL,80H
        ADD HL,BC
        LD A,(HL)
        SUB '0'
        LD HL,FCB+9
        LD B,3
SETBITS:
        PUSH AF
        AND 1
        JR Z,NEXTBIT
        LD A,(HL)
        OR 80H
        LD (HL),A
NEXTBIT:
        POP AF
        RRCA
        INC HL
        DJNZ SETBITS
        LD DE,FCB
        LD C,30
        CALL 5
        OR A
        JR NZ,BAD
        LD DE,80H
        LD C,26
        CALL 5
        LD DE,FCB
        LD C,17
        CALL 5
        CP 0FFH
        JR Z,BAD
        LD L,A
        LD H,0
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        LD DE,81H
        ADD HL,DE
        LD DE,FCB+1
        LD B,11
COMPARE:
        LD A,(DE)
        CP (HL)
        JR NZ,BAD
        INC HL
        INC DE
        DJNZ COMPARE
        LD DE,OK
        JR PRINT
BAD:    LD DE,FAIL
PRINT:  LD C,9
        CALL 5
        JP 0
OK:     DB 'ATTRIBUTE PASS',13,10,'$'
FAIL:   DB 'ATTRIBUTE FAIL',13,10,'$'
FCB:    DB 2,'ATTR    DAT'
        REPT 24
        DB 0
        ENDM
        END
"""


def directory(image: Path, diskdefs: Path) -> bytes:
    definition = re.search(r'diskdef bettercpm-default\n(.*?)\nend',
                           diskdefs.read_text(), re.S)[1]
    def value(key):
        return int(re.search(r'\b' + key + r'\s+(\d+)', definition)[1])
    size, sectors, boot, entries = map(value, ['seclen', 'sectrk', 'boottrk', 'maxdir'])
    skew = list(map(int, re.search(r'skewtab\s+([0-9,]+)', definition)[1].split(',')))
    raw = image.read_bytes()
    result = bytearray()
    for logical in range((entries * 32 + size - 1) // size):
        track, sector = divmod(logical, sectors)
        offset = ((boot + track) * sectors + skew[sector]) * size
        result += raw[offset:offset + size]
    return bytes(result[:entries*32])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, default=ROOT / 'build/z80pack')
    parser.add_argument('--simulator', type=Path,
                        default=Path.home() / 'projects/git/z80pack/cpmsim/cpmsim')
    parser.add_argument('--report', type=Path,
                        default=ROOT / 'build/test-results/z80pack-attributes')
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    work = report / 'runtime'
    work.mkdir()
    shutil.copytree(args.image_dir / 'disks', work / 'disks')
    shutil.copy2(args.image_dir / 'diskdefs', work / 'diskdefs')
    probe = report / 'ATTRPROB.COM'
    (report / 'attrprob.mac').write_text(PROBE)
    assemble(Path.home() / 'bin/z80asm', PROBE, probe, report / 'attrprob.lst', 0x100)
    disk_a, disk_b = work / 'disks/drivea.dsk', work / 'disks/driveb.dsk'
    subprocess.run(['cpmrm', '-T','raw','-f','bettercpm-default',str(disk_a),
                    '0:bdosprb.com'],cwd=work,check=True)
    subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk_a),
                    str(probe),'0:ATTRPROB.COM'],cwd=work,check=True)
    payload = report / 'payload.dat'
    payload.write_bytes(bytes(range(128)))
    subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk_b),
                    str(payload),'0:ATTR.DAT'],cwd=work,check=True)
    observations = []
    for mask in [0,7,1,2,4,3,5,6,0]:
        output = session(args.simulator.resolve(),work/'disks',
                         [(f'ATTRPROB {mask}\r'.encode(),b'A0>_ ',15)],
                         report / f'mask-{len(observations)}.txt')
        assert b'ATTRIBUTE PASS' in output and b'ATTRIBUTE FAIL' not in output, output
        raw = directory(disk_b, work/'diskdefs')
        matches = [raw[i:i+32] for i in range(0,len(raw),32)
                   if raw[i] == 0 and bytes(v & 127 for v in raw[i+1:i+12]) == b'ATTR    DAT']
        assert len(matches) == 1, matches
        entry = matches[0]
        expected = bytes(ord(c) | (128 if mask & (1 << n) else 0)
                         for n,c in enumerate('DAT'))
        assert entry[9:12] == expected, (mask,entry.hex())
        recovered = report / f'extracted-{len(observations)}.dat'
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk_b),
                        '0:ATTR.DAT',str(recovered)],cwd=work,check=True)
        assert recovered.read_bytes() == payload.read_bytes(), 'attributes changed payload/host access'
        if observations:
            assert entry[:9] == bytes(observations[0]['entry'][:9]) and entry[12:] == bytes(observations[0]['entry'][12:]), 'attribute change altered other metadata'
        observations.append({'mask':mask,'entry':list(entry)})
    (report/'evidence.json').write_text(json.dumps({'result':'PASS','observations':observations,
        'probe_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),
        'simulator_sha256':hashlib.sha256(args.simulator.read_bytes()).hexdigest()},indent=2)+'\n')
    print('PASS: all R/O/SYS/ARC combinations, clearing, native inspection, raw metadata and host extraction')


if __name__ == '__main__':
    main()
