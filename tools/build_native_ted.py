#!/usr/bin/env python3
"""Bounded TED native-build/startup gate; not full TED acceptance.

Build actual maintained instructions using the external ZSM4/LINK binaries.
Use disposable working media; require byte parity with the cross executable.
The runtime smoke test enters EX at the legacy TED prompt and verifies CCP
resumption. It makes no WordStar, ANSI-renderer, preservation or safe-save claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from build_ted import build
from dasm_native import campaign, compact_source, cpm_text


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system', type=Path, required=True)
    p.add_argument('--utilities', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--platforms', nargs='+', choices=['z80pack', 'trs80gp'], default=['z80pack', 'trs80gp'])
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    image = build(Path.home()/'bin/z80asm', a.output/'cross')
    native = compact_source((a.output/'cross/TEDNAT.MAC').read_text().rstrip('\x1a'))
    post = bytes.fromhex('1109010e09cd0500c9')+b'TED FOUNDATION POSTEXIT PASS\r\n$'
    report = {'status': 'IN_PROGRESS', 'scope': 'native build and legacy prompt startup/exit only',
              'editor_qualified': False, 'cross_sha256': hashlib.sha256(image).hexdigest(), 'platforms': {}}
    for platform in a.platforms:
        interactive = [(b'EX\r', b'TED FOUNDATION POSTEXIT PASS', 120)] if platform == 'trs80gp' else [
            (b'TEDDEV\r', b'TED>', 30), (b'EX\r', b'C0>_ ', 30),
            (b'QPOST\r', b'TED FOUNDATION POSTEXIT PASS', 30)]
        log, outputs = campaign(platform, {'TEDNAT.MAC': cpm_text(native), 'QPOST.COM': post},
                                ['B:ZSM4 TEDDEV=TEDNAT', 'B:LINK TEDDEV[A]'], a.output/platform,
                                system=a.system, utilities=a.utilities, extract=['TEDDEV.COM'],
                                interactive=interactive,
                                interactive_launch='TEDDEV' if platform == 'trs80gp' else None,
                                interactive_prompt='TED>', interactive_followup='QPOST',
                                interactive_ready=['TED FOUNDATION POSTEXIT PASS'] if platform == 'trs80gp' else None)
        errors = re.findall(rb'Errors: +([0-9]+)', log)
        assert errors and set(errors) == {b'0'}, errors
        assert b'UNDEFINED SYMBOLS' not in log.upper()
        actual = outputs['TEDDEV.COM']
        assert actual[:len(image)] == image, (platform, 'native/cross payload mismatch')
        assert len(actual) == (len(image)+127)//128*128
        assert set(actual[len(image):]) <= {26}
        assert b'TED FOUNDATION POSTEXIT PASS' in log
        report['platforms'][platform] = {'status': 'PASS', 'native_cross_parity': True,
                                       'legacy_prompt_exit': True, 'editor_qualified': False,
                                       'execution_report': platform+'/execution.json'}
        (a.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        print('PASS', platform, 'native build/parity and legacy prompt exit', flush=True)
    report['status'] = 'PASS'
    (a.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
