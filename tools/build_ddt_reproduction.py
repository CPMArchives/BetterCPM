#!/usr/bin/env python3
"""Rebuild historical DDT code/map and source-derived PIP memory residue.

DDT.COM is opened only after the candidate has been generated. Reserved bytes
come from an independently compiled CP/M 2.0 PIP image, not from DDT.COM.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LENGTH = 0xFBC
MONITOR = 0x680
BASES = (0, 0x100, 0x3100)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(args, **kwargs):
    result = subprocess.run([str(x) for x in args], capture_output=True, **kwargs)
    if result.returncode:
        raise RuntimeError(f'{args}: {result.stdout!r} {result.stderr!r}')
    return result


def source_bytes(path: Path, base: int | None = None) -> bytes:
    raw = path.read_bytes()
    # DDT1ASM has trailing NUL record padding after END; no program text changes.
    text = raw.split(b'\0', 1)[0].rstrip(b'\x1a').decode('ascii')
    if base is not None:
        assert text.count('ORG\t0000H') == 1
        text = text.replace('ORG\t0000H', f'ORG\t{base:05X}H')
    return text.encode('ascii') + b'\x1a'


def ihex(data: bytes) -> dict[int, int]:
    memory = {}
    eof = False
    for line in data.split(b'\x1a', 1)[0].splitlines():
        if not line.strip():
            continue
        assert line.startswith(b':'), line
        record = bytes.fromhex(line[1:].decode('ascii'))
        count, kind = record[0], record[3]
        assert len(record) == count + 5 and sum(record) % 256 == 0
        if kind == 1 or (kind == 0 and count == 0):
            eof = True
            break
        assert kind == 0, kind
        address = int.from_bytes(record[1:3], 'big')
        for index, value in enumerate(record[4:4 + count]):
            assert address + index not in memory
            memory[address + index] = value
    assert eof
    return memory


def ranges(offsets):
    result = []
    for x in sorted(offsets):
        if result and result[-1][1] + 1 == x:
            result[-1][1] = x
        else:
            result.append([x, x])
    return [{'first': a, 'last': b, 'length': b - a + 1} for a, b in result]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, default=ROOT/'third_party/dri-ddt')
    parser.add_argument('--output', type=Path, default=ROOT/'build/ddt-reproduction')
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    base = Path.home()/'projects/git/z80pack/cpmsim'
    parser.add_argument('--cpmsim', type=Path, default=base/'cpmsim')
    parser.add_argument('--system-disk', type=Path, default=base/'disks/library/cpm22-62khd.dsk')
    parser.add_argument('--disk-template', type=Path, default=base/'disks/library/cpm22-1.dsk')
    args = parser.parse_args()
    inputs = args.inputs.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    sources = out/'sources'
    sources.mkdir(exist_ok=True)
    modules = {'MOV': ('DDT0MOV.ASM', None)}
    for origin in BASES:
        for kind, original in [('A', 'DDT1ASM.ASM'), ('M', 'DDT2MON.ASM')]:
            modules[f'{kind}{origin >> 8:02X}'] = (original, origin)
    cross = {}
    for name, (original, origin) in modules.items():
        path = sources/(name+'.ASM')
        path.write_bytes(source_bytes(inputs/original, origin))
        result = run([args.assembler.resolve(), '-8', '-fb', f'-o{out/name}.bin',
                      f'-l{out/name}.lst', path])
        (out/(name+'-cross.log')).write_bytes(result.stdout + result.stderr)
        assert b'0 error(s)' in result.stdout + result.stderr
        cross[name] = (out/(name+'.bin')).read_bytes()
    # One fresh 8-inch work disk per module avoids listing/source disk overflow.
    for name in modules:
        with tempfile.TemporaryDirectory(prefix='ddt-native-', dir=out) as temp:
            work = Path(temp)
            disks = work/'disks'
            disks.mkdir()
            shutil.copyfile(args.system_disk, disks/'drivea.dsk')
            shutil.copyfile(args.disk_template, disks/'driveb.dsk')
            run(['mkfs.cpm', '-f', 'ibm-3740', disks/'driveb.dsk'])
            for path in [inputs/'MAC.COM', sources/(name+'.ASM')]:
                run(['cpmcp', '-f', 'ibm-3740', disks/'driveb.dsk', path, '0:'+path.name])
            script = ['set timeout 30', f'spawn {{{args.cpmsim.resolve()}}} -z -d {{{disks}}}',
                      'expect "A>"', 'send -- "B:\\r"', 'expect "B>"',
                      f'send -- "MAC {name}\\r"', 'expect "END OF ASSEMBLY"',
                      'expect "B>"', 'send "\\034"', 'expect eof']
            env = dict(os.environ)
            env['PATH'] = str(args.cpmsim.resolve().parent/'srctools')+os.pathsep+env.get('PATH','')
            result = run(['expect', '-c', '\n'.join(script)], cwd=work, env=env, timeout=45)
            (out/(name+'-native.log')).write_bytes(result.stdout + result.stderr)
            assert b'ERROR' not in result.stdout, result.stdout
            for ext in ['HEX', 'PRN']:
                run(['cpmcp', '-f', 'ibm-3740', disks/'driveb.dsk', '0:'+name+'.'+ext, out/(name+'.'+ext)])
    native = {name: ihex((out/(name+'.HEX')).read_bytes()) for name in modules}
    for name, (_, origin) in modules.items():
        start = 0x100 if name == 'MOV' else origin
        # PRN error flags occupy column 1; valid lines start blank or formfeed.
        listing = (out/(name+'.PRN')).read_bytes().split(b'\x1a', 1)[0]
        errors = [line for line in listing.splitlines() if line and 65 <= line[0] <= 90
                  and not line.startswith(b'CP/M MACRO ASSEM')]
        assert not errors, (name, errors[:5])
        assert all(cross[name][a-start] == v for a, v in native[name].items()), name
    payloads = {}
    coverage = None
    for origin in BASES:
        a = native[f'A{origin >> 8:02X}']
        m = native[f'M{origin >> 8:02X}']
        assert not set(a).intersection(m)
        memory = {k-origin: v for k, v in (a | m).items()}
        assert min(memory) == 0 and max(memory) == LENGTH-1
        assert min(m) - origin == MONITOR
        assert len(cross[f'M{origin >> 8:02X}']) == LENGTH
        if coverage is None:
            coverage = set(memory)
        assert coverage == set(memory)
        data = bytes(memory.get(i, 0) for i in range(LENGTH))
        payloads[origin] = data
        (out/f'payload-{origin:04x}.bin').write_bytes(data)
    marks = [i for i in range(LENGTH) if payloads[0][i] != payloads[0x100][i]]
    bitmap = bytearray((LENGTH+7)//8)
    for i in marks:
        assert i in coverage
        bitmap[i//8] |= 0x80 >> (i%8)
    # A second, distant page bias proves the generated map reproduces assembly.
    for origin in BASES[1:]:
        relocated = bytearray(payloads[0])
        for i in marks:
            relocated[i] = (relocated[i] + (origin >> 8)) & 255
        assert bytes(relocated) == payloads[origin]
    (out/'relocation.bitmap').write_bytes(bitmap)
    (out/'relocation-offsets.json').write_text(json.dumps(marks)+'\n')
    stub_memory = {a-0x100: v for a, v in native['MOV'].items()}
    assert 1 not in stub_memory and 2 not in stub_memory
    stub_memory[1], stub_memory[2] = LENGTH & 255, LENGTH >> 8
    from build_ddt_seed import build_seed
    seed = build_seed(inputs/'reproduction', out/'seed', args.cpmsim)
    seed_code = set(json.loads((out/'seed/initialized-code-offsets.json').read_text()))
    seed_hash = json.loads((inputs/'reproduction/provenance.json').read_text())['recipe']['seed_sha256']
    assert sha(seed) == seed_hash
    # A PIP load at 0100H leaves its bytes beneath a sparse DDT build at 0800H.
    # Exporting 0800H..1AFFH makes seed offsets file_offset+0700H.
    work_origin = 0x800
    memory = bytearray(65536)
    memory[0x100:0x100+len(seed)] = seed
    (out/'memory-before-overlay.bin').write_bytes(memory)
    residue_provenance = []
    for i in range(256+LENGTH):
        emitted = i in stub_memory if i < 256 else i-256 in coverage
        if not emitted:
            assert i+0x700 in seed_code
            residue_provenance.append({'file_offset': i, 'seed_file_offset': i+0x700,
                                       'memory_address': work_origin+i,
                                       'value': memory[work_origin+i]})
    for i, value in stub_memory.items():
        memory[work_origin+i] = value
    for i in coverage:
        memory[work_origin+256+i] = payloads[0][i]
    map_start = work_origin+256+LENGTH
    memory[map_start:map_start+len(bitmap)] = bitmap
    end = map_start+len(bitmap)
    file_length = (end-work_origin+127)//128*128
    memory[end:work_origin+file_length] = bytes(work_origin+file_length-end)
    candidate = bytes(memory[work_origin:work_origin+file_length])
    (out/'memory-after-overlay.bin').write_bytes(memory)
    (out/'residue-provenance.json').write_text(json.dumps(residue_provenance,indent=2)+'\n')
    (out/'DDT-source-candidate.COM').write_bytes(candidate)
    (out/'DDT-reproduced.COM').write_bytes(candidate)
    zero_control = bytearray(candidate)
    for item in residue_provenance:
        zero_control[item['file_offset']] = 0
    (out/'DDT-zero-filled-control.COM').write_bytes(zero_control)
    # Reference access starts here, after all output bytes have been generated.
    reference = (args.reference or inputs/'DDT.COM').read_bytes()
    assert sha(reference) == 'd79890f0a637aee317a255bdac6b27215b1ad4452a1b6da822828bcba5a49ecf'
    assert len(candidate) == len(reference) == 4864
    defined = set(stub_memory) | {256+i for i in coverage}
    defined |= set(range(256+LENGTH, len(candidate)))
    differences = [{'file_offset': i, 'load_address': i+0x100,
                    'expected': a, 'actual': b,
                    'source_defined': i in defined}
                   for i, (a, b) in enumerate(zip(reference, candidate)) if a != b]
    unknown = sorted(set(range(256+LENGTH)) - defined)
    report = {
        'status': 'PASS' if not differences else 'FAIL_BYTE_MISMATCH',
        'full_file_identical': not differences,
        'residue_source': 'CP/M 2.0 PIP source compiled by PL/M-80 V3.1; LOCATE stacksize(64)',
        'residue_seed_sha256': sha(seed), 'residue_bytes_explained': len(residue_provenance),
        'memory_work_origin': work_origin, 'all_residue_from_initialized_pip_code': True,
        'zero_control_differing_bytes': sum(a != b for a,b in zip(zero_control,reference)),
        'source_defined_bytes_identical': not any(x['source_defined'] for x in differences),
        'cross_native_emitted_bytes_identical': True,
        'reference_sha256': sha(reference), 'candidate_sha256': sha(candidate),
        'file_length': len(candidate), 'payload_length': LENGTH,
        'payload_emitted_bytes': len(coverage),
        'payload_uninitialized_bytes': LENGTH-len(coverage),
        'relocation_marks': len(marks), 'bitmap_size': len(bitmap),
        'bitmap_identical': bytes(bitmap) == reference[256+LENGTH:256+LENGTH+len(bitmap)],
        'differing_bytes': len(differences), 'uninitialized_file_ranges': ranges(unknown),
        'differences': differences,
        'inputs': {p.name: sha(p.read_bytes()) for p in inputs.iterdir() if p.is_file()},
        'tools': {str(p): sha(p.read_bytes()) for p in
                  [args.assembler, args.cpmsim, args.system_disk, args.disk_template]},
        'policy': 'Reserved bytes come only from independently compiled PIP source at the reconstructed memory offsets. '
                  'DDT.COM is comparison-only; no production utility integration or adaptation.'}
    (out/'qualification.json').write_text(json.dumps(report, indent=2)+'\n')
    assert report['source_defined_bytes_identical']
    assert report['bitmap_identical']
    print(json.dumps({k: v for k, v in report.items() if k not in
                      ['differences','inputs','tools','uninitialized_file_ranges']}, indent=2))
    raise SystemExit(0 if report['full_file_identical'] else 1)


if __name__ == '__main__':
    main()
