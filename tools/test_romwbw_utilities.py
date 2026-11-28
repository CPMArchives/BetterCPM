#!/usr/bin/env python3
"""Focused portable utility acceptance on private RomWBW disk copies."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from romwbw_media import SIZE
from test_romwbw_system import Terminal


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('image-dir', 'simulator', 'rom', 'output'):
        p.add_argument('--'+key, type=Path, required=True)
    a = p.parse_args()
    image, out = a.image_dir.resolve(), a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source, target = out/'source.img', out/'target.img'
    shutil.copy2(image/'system.img', source)
    shutil.copy2(image/'diskdefs', out/'diskdefs')
    target.write_bytes(b'\xe5'*SIZE)
    fixture = bytes(range(256))*9
    (out/'input.bin').write_bytes(fixture)
    (out/'smoke.sub').write_bytes(b'HELLO\r\nHELLO\r\n\x1a')
    def cpm(*args):
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-romwbw', *map(str,args)], cwd=out, check=True)
    cpm(target, out/'input.bin', '0:INPUT.BIN')
    cpm(target, out/'smoke.sub', '0:SMOKE.SUB')
    candidate = json.loads((image/'candidate.json').read_text())
    from component_registry import utility_identities
    registry = utility_identities()
    queried, checks = [], []
    cmd = [str(a.simulator.resolve()), '--romwbw='+str(a.rom.resolve()),
           '--disk0='+str(source), '--disk1='+str(target), '--boot=2',
           '--no-config', '--strict-io', '--max-instructions=8000000000']
    t = Terminal(a.simulator.resolve(), out, command=cmd)
    try:
        t.prompt()
        for filename in sorted(candidate['files']):
            name = filename.removesuffix('.COM')
            if not filename.endswith('.COM') or name not in registry or name in ('CONFIG','SYSGEN'): continue
            before = len(t.data)
            t.send(name+' /VER')
            version, revision = registry['RCP' if b'Resident RCP' in t.data[before:] else name]
            expected = f'{name} {version} ({revision:03d}'.encode()
            if expected not in t.data[before:]: raise AssertionError((name, expected, t.data[before:]))
            queried.append(name)
            print('Version PASS:',name,flush=True)
        checks.append('registry version queries for every shipped portable COM')
        t.send('CONFIG /LOGICAL=B /UNIT=3', 'B: binding updated.')
        t.send('PIP B:COPY.BIN=B:INPUT.BIN')
        t.send('COMPARE B:INPUT.BIN B:COPY.BIN', 'FILES IDENTICAL')
        t.send('MD5SUM B:COPY.BIN', hashlib.md5(fixture).hexdigest())
        t.send('NOAH /ADD B:SMOKE.ARK B:INPUT.BIN')
        t.send('NOAH /TEST B:SMOKE.ARK', 'INPUT.BIN: CRC OK')
        t.send('ERA B:INPUT.BIN')
        t.send('NOAH /X /Y B:SMOKE.ARK B:', 'extracted and verified.')
        checks += ['PIP binary copy and COMPARE equality', 'MD5SUM agrees with host',
                   'NOAH overlay add/test/extract and ERA']
        t.send('TIME', 'No TIME provider is loaded')
        t.send('STAT MEM', 'Maximum loadable COM: 57344 bytes')
        t.type_command('SUBMIT B:SMOKE')
        t.expect('ROMWBW TRANSIENT PASS')
        t.expect('ROMWBW TRANSIENT PASS')
        t.prompt()
        checks += ['TIME reports missing provider', 'STAT reports 56 KiB capacity',
                   'SUBMIT executes two transient commands']
    finally:
        t.close()
    for name in ('INPUT.BIN', 'COPY.BIN'):
        extracted = out/name.lower()
        cpm(target, '0:'+name, extracted)
        if extracted.read_bytes() != fixture: raise AssertionError(name+' differs from fixture')
    checks.append('independent host verification of copied and extracted binary files')
    result = {'status':'PASS', 'system_sha256':hashlib.sha256((image/'system.img').read_bytes()).hexdigest(),
              'utility_versions':queried, 'checks':checks}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS:',out/'result.json')


if __name__ == '__main__': main()
