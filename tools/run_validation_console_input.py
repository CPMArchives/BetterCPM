#!/usr/bin/env python3
"""Independently observe CONSTEST input results before confirming each case."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
import pyte
from test_z80pack_sysgen_install import session


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display(data):
    screen = pyte.Screen(80, 200)
    pyte.Stream(screen).feed(data.decode('ascii'))
    return screen.display


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'diskdefs', 'suite', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--simulator', type=Path, default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    args = parser.parse_args()
    report = json.loads((args.baseline/'report.json').read_text())
    original = args.baseline/report['image']
    assert report['target'] == 'z80pack' and sha(original) == report['sha256']
    program = args.suite/'suite/build/CONSTEST.COM'
    hashes = {line.split()[1]: line.split()[0] for line in (args.suite/'suite/build/SHA256SUMS.txt').read_text().splitlines() if line.strip()}
    assert sha(program) == hashes['CONSTEST.COM']
    args.output.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='constest-input-', dir=args.output.resolve()))
    disks = work/'disks'
    disks.mkdir()
    shutil.copy2(original, disks/'drivea.dsk')
    shutil.copy2(args.diskdefs, work/'diskdefs')
    subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(disks/'drivea.dsk'), str(program), '0:CONSTEST.COM'], cwd=work, check=True)
    # Reviewed recipes and expected buffers are literal external oracles. Never
    # derive an expected result from the program's own EXPECTED description.
    cases = [
        (106, b'Type AB then Enter. Expect count 02 and data [AB]: ', b'AB\r', b'AB'),
        (108, b'Type ABC then Enter. Expect count 03: ', b'ABC\r', b'ABC'),
        (109, b'Type XYZ then Enter. Expect data [XYZ] at buffer+2: ', b'XYZ\r', b'XYZ'),
        (111, b'Type AB then Enter. Expect count 02/data [AB], no CR stored: ', b'AB\r', b'AB'),
        (112, b'Type AB then Ctrl-J. Expect count 02/data [AB], no LF stored: ', b'AB\n', b'AB'),
        (113, b'Maximum is 1. Type Z only; no additional character is required: ', b'Z', b'Z'),
        (114, b'Type M then Enter. Expect M echoed, count 01, data [M]: ', b'M\r', b'M'),
        (115, b'Type AB, Backspace, C, Enter. Expect count 02/data [AC]: ', b'AB\x08C\r', b'AC'),
        (122, b'Expect count 02/data [AC]: ', b'AB\x08C\r', b'AC'),
    ]
    confirmation = b'Do OBSERVED and EXPECTED match? (Y/N; no Enter) '
    trace = work/'transcript.bin'
    observed = []
    def commands():
        direct = [
            (83, b'Press K now: ', b'K', b'\r\nOBSERVED: return A=4B', b''),
            (84, b'Press U; nothing should appear between these brackets: [', b'U', b']\r\nOBSERVED: return A=55', b']'),
            (93, b'Press R now: ', b'R', b'R\r\nOBSERVED: return A=52', b'R'),
            (94, b'Press G; it should appear between brackets: [', b'G', b'G]\r\nOBSERVED: return A=47', b'G]'),
        ]
        for number, prompt, key, expected, visible in direct:
            yield (f'CONSTEST /{number:04d}\r'.encode(), prompt, 30)
            before = trace.read_bytes()
            yield (key, confirmation, 30)
            after = trace.read_bytes()
            assert after.startswith(before)
            delta = after[len(before):]
            assert delta.startswith(expected), (number, delta)
            echo = delta.split(b'\r\nOBSERVED:', 1)[0]
            assert display(before + echo) == display(before + visible), (number, 'input echo differs')
            observed.append({'case': number, 'keys_hex': key.hex(), 'return_a_hex': key.hex(), 'visible_edit_verified': True})
            yield (b'Y', f'{number:04d}  P  R'.encode(), 30)
            yield (b'', b'A0>_ ', 30)
        for number, prompt, keys, data in cases:
            yield (f'CONSTEST /{number:04d}\r'.encode(), prompt, 30)
            before = trace.read_bytes()
            yield (keys, confirmation, 30)
            after = trace.read_bytes()
            assert after.startswith(before)
            delta = after[len(before):]
            marker = b'\r\nOBSERVED: count='
            echo, result = delta.split(marker, 1)
            expected = f'{len(data):02X}'.encode() + b'; data=[' + data + b']\r\n'
            assert result.startswith(expected), (number, result)
            assert display(before + echo) == display(before + data), (number, 'visible edit differs', echo)
            observed.append({'case': number, 'keys_hex': keys.hex(), 'returned_hex': data.hex(), 'visible_edit_verified': True})
            yield (b'Y', f'{number:04d}  P  R'.encode(), 30)
            yield (b'', b'A0>_ ', 30)
        yield (b'BYE\r', b'System halted', 10)
    session(args.simulator.resolve(), disks, commands(), trace)
    assert sha(original) == report['sha256']
    result = {'baseline_sha256': report['sha256'], 'program_sha256': sha(program), 'simulator_sha256': sha(args.simulator), 'pyte_module': pyte.__file__, 'cases': observed, 'pass': len(observed), 'oracle': 'literal returned buffers and independently rendered final input echo before confirmation', 'scope': 'cpmsim Functions 1, 6 and 10 selected input recipes; no timing or native Model 4 claim'}
    (work/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'pass': len(observed), 'evidence': str(work)}, indent=2))


if __name__ == '__main__':
    main()
