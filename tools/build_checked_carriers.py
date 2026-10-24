#!/usr/bin/env python3
"""Build reviewed checked carriers through ordinary module builders; no media."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
from checked_carriers import selected_contract

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ('ccp', 'rcp_cpx', 'hello_cpx', 'hello_rsx', 'echo_rsx',
              'batch', 'fdf_rsx', 'p2dos_rsx', 'zprtc_rsx', 'test_service_rsx',
              'stateful_test_rsx', 'adm3a', 'screen_backends', 'vt52', 'ansi')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    a = p.parse_args();contract = selected_contract(a.assembler)
    if not contract:
        p.error('select a prepared checked profile with BETTERCPM_BUILD_CONTEXT')
    # Refuse stale hardware or unreviewed carriers in a reused output directory.
    from checked_carriers import PUBLIC_RSX, PRIVATE_RSX
    for existing in (ROOT/'build/rsx').glob('*.RSX'):
        if existing.stem not in PUBLIC_RSX | PRIVATE_RSX:
            p.error(f'unsupported or unreviewed existing carrier: {existing.name}')
    for component in COMPONENTS:
        subprocess.run([sys.executable, str(ROOT/'tools'/f'build_{component}.py'),
                        '--assembler', str(a.assembler)], cwd=ROOT, check=True)
    files = [ROOT/'build/ccp/ccp.rlm', *sorted((ROOT/'build/cpx').glob('*.CPX')),
             *sorted((ROOT/'build/rsx').glob('*.RSX'))]
    if selected_contract(a.assembler) != contract:
        raise ValueError('checked build source changed while compiling')
    result = {'profile':contract['contract']['profile'],
              'compatibility_id':contract['compatibility_id'],
              'artifacts':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()
                           for f in files},
              'development_only':['HELLO.RSX', 'HELLO.CPX', 'STATEFUL.RSX'],
              'unsupported_hardware_omitted':['M4SCRN.RSX', 'FREHDCLK.RSX'],
              'status':'checked carriers only; distribution integration pending'}
    (ROOT/'build/carriers-results.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':main()
