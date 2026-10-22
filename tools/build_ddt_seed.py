#!/usr/bin/env python3
"""Compile the independent CP/M 2.0 PIP image which explains DDT's residue.

Only source/tool archives are inputs. No DDT image is opened or executed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, **kwargs):
    result = subprocess.run([str(x) for x in command], capture_output=True, **kwargs)
    if result.returncode:
        raise RuntimeError(f'{command}: {result.stderr!r}')
    return result


def build_seed(inputs, output, cpmsim, stack_size=64, source=None):
    inputs, output, cpmsim = Path(inputs), Path(output), Path(cpmsim).resolve()
    output.mkdir(parents=True, exist_ok=True)
    provenance = json.loads((inputs/'provenance.json').read_text())
    archive = inputs/'cpm22src.tgz'
    source = Path(source) if source else inputs/'PIP20.PLM'
    assert sha(archive) == provenance['tool_archive']['sha256']
    if source == inputs/'PIP20.PLM':
        assert sha(source) == provenance['pip_source']['extracted_sha256']
    env = dict(os.environ)
    env['PATH'] = str(cpmsim.parent/'srctools')+os.pathsep+env.get('PATH','')
    commands = [
        'pip c:trint.src=i:os5trint.src', 'pip c:=i:pip.plm',
        'fixeof c:pip.plm', 'isx', ':f0:asm80 :f2:trint.src',
        ':f1:plm80 :f2:pip.plm',
        ':f1:link :f2:pip.obj,:f2:trint.obj,:f1:x0100,:f1:plm80.lib to :f2:pip.mod',
        f':f1:locate :f2:pip.mod code(0100H) stacksize({stack_size})',
        ':f1:cpm', 'objcpm c:pip', 'type done.txt']
    script_source = '\r\n'.join(commands).encode('ascii')+b'\r\n\x1a'
    (output/'SEED.SUB').write_bytes(script_source)
    with tempfile.TemporaryDirectory(prefix='ddt-pip-seed-', dir=output) as temp:
        work = Path(temp)
        disks = work/'disks'
        disks.mkdir()
        with tarfile.open(archive) as tar:
            for drive, name in [('a','cpm22-src-1.dsk'), ('b','cpm22-src-2.dsk'),
                                ('i','hd-cpm22src.dsk')]:
                member = tar.extractfile('disks/library/'+name)
                (disks/f'drive{drive}.dsk').write_bytes(member.read())
        for drive in 'cd':
            shutil.copyfile(disks/'drivea.dsk', disks/f'drive{drive}.dsk')
            run(['mkfs.cpm', '-f', 'ibm-3740', disks/f'drive{drive}.dsk'])
        run(['cpmrm', '-f', 'z80pack-hd', disks/'drivei.dsk', '0:PIP.PLM'])
        run(['cpmcp', '-f', 'z80pack-hd', disks/'drivei.dsk', source, '0:PIP.PLM'])
        run(['cpmcp', '-f', 'ibm-3740', disks/'drivea.dsk', output/'SEED.SUB', '0:SEED.SUB'])
        marker = work/'DONE.TXT'
        marker.write_bytes(b'PIP-SEED-BUILD-DONE\r\n\x1a')
        run(['cpmcp', '-f', 'ibm-3740', disks/'drivea.dsk', marker, '0:DONE.TXT'])
        expect_script = '\n'.join([
            'set timeout 30', f'spawn {{{cpmsim}}} -z -d {{{disks}}}',
            'expect "A>"', 'send -- "SUBMIT SEED\\r"',
            'expect "PIP-SEED-BUILD-DONE"', 'expect "A>"',
            'send "\\034"', 'expect eof'])
        result = run(['expect','-c',expect_script], env=env, cwd=work, timeout=45)
        transcript = result.stdout+result.stderr
        (output/'native-seed.log').write_bytes(transcript)
        for token in [b'PL/M-80 COMPILER V3.1', b'0 PROGRAM ERROR(S)',
                      b'OBJECT LINKER V3.0', b'OBJECT LOCATER V3.0',
                      b'PIP-SEED-BUILD-DONE']:
            assert token in transcript, token
        for error in [b'UNRESOLVED', b'NO FILE', b'WRITE ERROR', b'FATAL']:
            assert error not in transcript, error
        run(['cpmcp','-f','ibm-3740',disks/'drivec.dsk','0:*.*',output])
    seed = (output/'pip.com').read_bytes()
    # Prove the retained PIP bytes are compiler-emitted CODE, not PIP DS residue.
    obj = (output/'pip.obj').read_bytes()
    initialized_code = set()
    cursor = 0
    while cursor + 3 <= len(obj):
        kind = obj[cursor]
        size = int.from_bytes(obj[cursor+1:cursor+3], 'little')
        record = obj[cursor:cursor+3+size]
        assert len(record) == size+3 and sum(record) % 256 == 0
        if kind == 6 and record[3] == 1:
            address = int.from_bytes(record[4:6], 'little')
            initialized_code.update(range(address, address+len(record[6:-1])))
        cursor += 3+size
        if kind == 0x0E:
            break
    (output/'initialized-code-offsets.json').write_text(json.dumps(sorted(initialized_code))+'\n')
    report = {'source_sha256':sha(source), 'tool_archive_sha256':sha(archive),
              'cpmsim_sha256':sha(cpmsim), 'stack_bytes':stack_size,
              'seed_sha256':hashlib.sha256(seed).hexdigest(), 'seed_size':len(seed),
              'commands':commands, 'ddt_reference_used':False,
              'initialized_code_bytes':len(initialized_code)}
    (output/'seed-qualification.json').write_text(json.dumps(report,indent=2)+'\n')
    return seed


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs',type=Path,default=ROOT/'third_party/dri-ddt/reproduction')
    p.add_argument('--output',type=Path,default=ROOT/'build/ddt-reproduction/seed')
    p.add_argument('--cpmsim',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    p.add_argument('--stack-size',type=int,default=64)
    p.add_argument('--source',type=Path)
    args=p.parse_args()
    seed=build_seed(args.inputs.resolve(),args.output.resolve(),args.cpmsim,args.stack_size,args.source)
    print(hashlib.sha256(seed).hexdigest())


if __name__=='__main__':
    main()
