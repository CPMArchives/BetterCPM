#!/usr/bin/env python3
"""Check shipped extension-manager refusals preserve live profiles and media."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from run_validation_cpmsim_ren import audit
from run_validation_returning import sha
from test_z80pack_sysgen_install import session
from utility_versions import banner


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    modes = p.add_mutually_exclusive_group()
    modes.add_argument('--recover-malformed-cpx', action='store_true',
                       help='Require safe recovery and explicit profile removal')
    modes.add_argument('--malformed-cpx', action='store_true',
                   help='Historical oracle: reproduce the hard-stop on an unfixed baseline')
    a = p.parse_args()
    base = a.baseline.resolve()
    w = a.output.resolve()
    w.mkdir(parents=True, exist_ok=False)
    report = json.loads((base / 'report.json').read_text())
    assert sha(base / report['image']) == report['sha256']
    (w / 'disks').mkdir()
    disk = w / 'disks/drivea.dsk'
    shutil.copy2(base / report['image'], disk)
    shutil.copy2(base / 'diskdefs', w / 'diskdefs')
    shutil.copy2(__file__, w / 'executed-runner.py')
    # Intentionally invalid headers; never substitute a shipped module.
    for name in ('BAD.CPX', 'BAD.RSX'):
        fixture = w / name
        fixture.write_bytes(b'INVALID HEADER'.ljust(128, b'\0'))
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default',
                        str(disk), str(fixture), '0:' + name], cwd=w,
                       capture_output=True, check=True)
    cases = []
    steps = []
    prompt = b'A0>_ '
    def command(text, diagnostic):
        steps.append((text.encode() + b'\r', prompt, 30))
        cases.append((text, diagnostic))
    for command_name, suffix, error in (
        ('CPX', 'CPX', b'CPX profile error'),
        ('RSX', 'RSX', b'RSX module or profile error')):
        for text in ('BOGUS', 'LOAD', 'LOAD BAD.TXT'):
            command(command_name + ' ' + text,
                    (command_name + ' LIST | LOAD/UNLOAD').encode())
        for text in ('LOAD MISSING', 'LOAD BAD', 'UNLOAD MISSING'):
            if command_name == 'CPX':
                # Missing carriers are permitted profile entries; malformed ones
                # checked by the separate recovery/historical-finding modes.
                if text == 'LOAD BAD':
                    continue
                command(command_name + ' ' + text, None)
                if text == 'LOAD MISSING':
                    command('CPX LIST', b'MISSING.CPX')
            else:
                command(command_name + ' ' + text, None if text == 'UNLOAD MISSING' else error)
        command(command_name + ' LIST', b'RCP.CPX' if suffix == 'CPX' else b'No RSXs loaded')
    command('DIR /VER', banner('DIR', resident=True).encode())
    command('RSX LOAD ANSISCRN', None)
    command('RSX LOAD ANSI', None)
    command('RSX LOAD BAD', b'RSX module or profile error')
    command('RSX UNLOAD MISSING', None)
    command('RSX LIST', b'ANSI : BDOS 255')
    command('RSX UNLOAD ANSI', None)
    command('RSX UNLOAD ANSISCRN', None)
    command('RSX LIST', b'No RSXs loaded')
    steps.append((b'BYE\r', b'System halted', 30))
    sim = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    if a.recover_malformed_cpx:
        cases = []
        steps = []
        command('CPX LOAD BAD', b'CPX?')
        command('CPX LIST', b'BAD.CPX')
        command(':VER /VER', banner('VER').encode())
        command('RSX LOAD ANSISCRN', b'CPX?')
        command('RSX LOAD ANSI', b'CPX?')
        command('CPX LIST', b'BAD.CPX')
        command('CPX UNLOAD BAD', None)
        command('CPX LIST', b'RCP.CPX')
        command('DIR /VER', banner('DIR', resident=True).encode())
        command('RSX UNLOAD ANSI', None)
        command('RSX UNLOAD ANSISCRN', None)
        command('RSX LIST', b'TPA available: 53K')
        steps.append((b'BYE\r', b'System halted', 30))
    if a.malformed_cpx:
        steps = [(b'CPX LOAD BAD\r', prompt, 30)]
    try:
        trace = session(sim, w / 'disks', steps, w / 'transcript.bin')
    except AssertionError as error:
        (w / 'result.json').write_text(json.dumps({
            'status': 'OPEN_FINDING' if a.malformed_cpx else 'FAIL',
            'error': str(error), 'baseline_sha256': report['sha256'],
            'runner_sha256': sha(Path(__file__))}, indent=2) + '\n')
        raise
    assert not a.malformed_cpx, 'malformed CPX returned; review finding oracle'
    pos = 0
    observations = []
    for text, diagnostic in cases:
        start = trace.index(text.encode(), pos)
        end = trace.index(prompt, start)
        output = trace[start:end]
        if diagnostic is not None:
            assert diagnostic in output, (text, output)
        if a.recover_malformed_cpx and text == 'CPX LIST':
            assert b'RCP.CPX' in output
            if b'BAD.CPX' in diagnostic:
                assert b'CPX?' in output
            else:
                assert b'BAD.CPX' not in output and b'CPX?' not in output
        if text == 'RSX LIST':
            assert b'TPA available: 53K' in output if b'No RSXs' in output else b'ANSISCRN : BDOS 255' in output
        observations.append({'command': text, 'status': 'PASS'})
        pos = end + len(prompt)
    matched = audit(base, report, w, disk)
    assert sha(base / report['image']) == report['sha256']
    (w / 'result.json').write_text(json.dumps({
        'status': 'PASS', 'cases': observations, 'unchanged_shipped_files': matched,
        'runner_sha256': sha(Path(__file__)), 'simulator_sha256': sha(sim),
        'baseline_sha256': report['sha256'],
        'recovered_malformed_cpx': a.recover_malformed_cpx,
        'scope': 'shipped cpmsim managers; syntax and malformed RSX rejection, optional missing CPX profile entry/removal, missing RSX rejection, idempotent absent unload, live profile preservation and 53K recovery; malformed CPX recovery is checked only in the explicit recovery mode; not exhaustive transaction fault injection'
    }, indent=2) + '\n')
    print('PASS extension-manager refusal and recovery checks', w)


if __name__ == '__main__':
    main()
