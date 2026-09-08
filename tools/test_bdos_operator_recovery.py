#!/usr/bin/env python3
"""Qualify the BDOS physical-error operator path in trs80gp."""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

from build_ccp import assemble
from run_trs80_command import DEFAULT_EMULATOR


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT.parent / 'cpm-compatibility'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(image: Path, workspace: Path, name: str,
        responses: list[tuple[int, str]]) -> str:
    snapshot = workspace / f'{name}.bin'
    command = [
        'python3', str(ROOT / 'tools/run_trs80_command.py'), 'FAULTIO',
        '--image', str(image), '--boot-delay', '3500', '--run-delay', '3000',
        '--snapshot', str(snapshot),
    ]
    for delay, response in responses:
        command.extend(('--response', f'{delay}:{response}'))
    result = subprocess.run(command, cwd=ROOT, check=True,
                            text=True, stdout=subprocess.PIPE)
    text = result.stdout
    (workspace / f'{name}.txt').write_text(text)
    return text


def main() -> None:
    workspace = ROOT / 'build/compatibility' / time.strftime(
        'bad-sector-%Y%m%d-%H%M%S')
    workspace.mkdir(parents=True)

    source = ROOT / 'tests/fixtures/conformance/faultmore.mac'
    program = workspace / 'FAULTIO.COM'
    assemble(Path('/Users/nathanael/bin/z80asm'), source.read_text(), program,
             workspace / 'faultmore.lst', 0x100)
    image = workspace / 'BetterCPM-Bad-Sector-Qualification.dmk'
    subprocess.run([
        'python3', str(ROOT / 'tools/build_trs80_boot.py'),
        '--include-as', f'FAULTIO.COM={program}',
        '--include', str(SUITE / 'suite/runtime-payload/BTONE.DAT'),
        '--output', str(image),
    ], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)

    # With no answer supplied, the direct caller must still be suspended at
    # the operator diagnostic when the emulator takes its final snapshot.
    suspended = run(image, workspace, 'suspended', [])
    require('Bad Sector' in suspended, 'physical failure did not present Bad Sector')
    require('READ CALLER RESUMED' not in suspended,
            'physical failure returned without an operator choice')

    ignored = run(image, workspace, 'ignore', [(2400, 'I'), (2400, 'I')])
    require('READ CALLER RESUMED after operator ignore.' in ignored,
            'read caller did not resume after Ignore')
    require('WRITE CALLER RESUMED after operator ignore.' in ignored,
            'write caller did not resume after Ignore')
    require('FAULT PROVIDER COMPLETED BOTH CALLS' in ignored,
            'logical read/write path did not finish after Ignore')

    # Control-C must abandon FAULTIO.  A subsequent resident command proves
    # that warm boot reconstructed a usable CCP rather than returning through
    # the interrupted program.
    aborted = run(image, workspace, 'abort', [(2400, chr(3)), (8000, 'VER\\r')])
    require('READ CALLER RESUMED' not in aborted,
            'Control-C returned to the interrupted read caller')
    require('BetterCP/M 0.3' in aborted,
            'Control-C did not leave a usable command environment')

    print(workspace)
    print('Bad Sector presentation and caller suspension passed')
    print('read/write Ignore continuation passed')
    print('Control-C caller abandonment and CCP recovery passed')


if __name__ == '__main__':
    main()
