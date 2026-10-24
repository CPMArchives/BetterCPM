#!/usr/bin/env python3
"""Independently observe CONSTEST input results before confirming each case."""
import argparse
import hashlib
import json
from importlib.metadata import version
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
        (116, b'Type AB, DEL, C, Enter. Expect count 02/data [AC]: ', b'AB\x7fC\r', b'AC'),
        (122, b'Expect count 02/data [AC]: ', b'AB\x08C\r', b'AC'),
    ]
    confirmation = b'Do OBSERVED and EXPECTED match? (Y/N; no Enter) '
    trace = work/'transcript.bin'
    observed = []
    def commands():
        yield (b'CONSTEST /0085\r', b'Press any key to start with an empty input queue: ', 30)
        yield (b'K', confirmation, 30)
        assert b'OBSERVED: return A=00\r\n' in trace.read_bytes().split(b'Probe 0085:', 1)[1]
        observed.append({'case': 85, 'keys_hex': '4b', 'return_a_hex': '00'})
        yield (b'Y', b'0085  P  R', 30)
        yield (b'', b'A0>_ ', 30)

        yield (b'CONSTEST /0092\r', b'Wait briefly, then press B: ', 30)
        yield (b'', None, 0.5)
        before = trace.read_bytes()
        yield (b'B', confirmation, 30)
        assert trace.read_bytes()[len(before):].startswith(b'B\r\nOBSERVED: return A=42\r\n')
        observed.append({'case': 92, 'keys_hex': '42', 'return_a_hex': '42', 'silence_seconds': 0.5})
        yield (b'Y', b'0092  P  R', 30)
        yield (b'', b'A0>_ ', 30)

        yield (b'CONSTEST /0104\r', b'Press K once. Function 11 must detect it; Function 1 must consume it: ', 30)
        before = trace.read_bytes()
        yield (b'K', confirmation, 30)
        assert trace.read_bytes()[len(before):].startswith(b'K\r\nOBSERVED: Function 1 returned A=4B\r\n')
        observed.append({'case': 104, 'classification': 'profile', 'keys_hex': '4b', 'return_a_hex': '4b', 'oracle': 'one supplied key survives Function 11 and is echoed once by Function 1'})
        yield (b'Y', b'0104  P  X', 30)
        yield (b'', b'A0>_ ', 30)
        yield (b'CONSTEST /0107\r', b'Maximum is 1. Type Z only; call must return without Enter: ', 30)
        before = trace.read_bytes()
        yield (b'Z', b'Expect count 01 and data [Q]: ', 30)
        delta = trace.read_bytes()[len(before):]
        echo, result = delta.split(b'\r\nOBSERVED: count=', 1)
        assert result.startswith(b'01; data=[Z]\r\n')
        assert display(before+echo) == display(before+b'Z')
        before = trace.read_bytes()
        yield (b'Q\r', confirmation, 30)
        delta = trace.read_bytes()[len(before):]
        echo, result = delta.split(b'\r\nOBSERVED: count=', 1)
        assert result.startswith(b'01; data=[Q]\r\n')
        assert display(before+echo) == display(before+b'Q')
        observed.append({'case': 107, 'keys_hex': '5a510d', 'buffers': ['5a', '51'], 'oracle': 'maximum 1 returns without Enter; maximum byte FF accepts Q and returns on Enter'})
        yield (b'Y', b'0107  P  R', 30)
        yield (b'', b'A0>_ ', 30)

        yield (b'CONSTEST /0101\r', b'The input call must pause until resumed and finally return X: ', 30)
        yield (b'\x13', None, 0.25)
        yield (b'\x11', None, 0.25)
        before = trace.read_bytes()
        yield (b'X', confirmation, 30)
        assert trace.read_bytes()[len(before):].startswith(b'X\r\nOBSERVED: final return A=58\r\n')
        observed.append({'case': 101, 'keys_hex': '131158', 'return_a_hex': '58', 'silence_seconds': [0.25, 0.25]})
        yield (b'Y', b'0101  P  R', 30)
        yield (b'', b'A0>_ ', 30)
        echo_cases = [
            (95, b'Press Enter; cursor should return to column zero: ', b'\r', b'\r\r\nOBSERVED: return A=0D\r\n'),
            (96, b'Press Ctrl-J; cursor should advance one line: ', b'\n', b'\n\r\nOBSERVED: return A=0A\r\n'),
            (97, b'After ABC, press Backspace; X should overwrite C:\r\nABC', b'\x08', b'\x08X\r\nEXPECTED: display ends as ABX.\r\n'),
            (98, b'After A, press TAB; B should land at next tab stop:\r\nA', b'\t', b'       B\r\nEXPECTED: TAB was expanded to the next eight-column stop.\r\n'),
            (99, b'Press Ctrl-A; nothing should appear between brackets: [', b'\x01', b']\r\nOBSERVED: return A=01\r\n'),
            (100, b'After A, press TAB; B should use the shared next tab stop:\r\nA', b'\t', b'       B\r\nEXPECTED: Function 1 TAB used the column established by Function 9.\r\n'),
        ]
        for number, prompt, key, expected in echo_cases:
            yield (f'CONSTEST /{number:04d}\r'.encode(), prompt, 30)
            before = trace.read_bytes()
            yield (key, confirmation, 30)
            delta = trace.read_bytes()[len(before):]
            assert delta.startswith(expected), (number, delta)
            observed.append({'case': number, 'keys_hex': key.hex(), 'expected_prefix_hex': expected.hex(), 'oracle': 'literal control echo and cursor movement bytes'})
            yield (b'Y', f'{number:04d}  P  R'.encode(), 30)
            yield (b'', b'A0>_ ', 30)
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
        controls = [
            (118, b'Type AB, Ctrl-E, CD, Enter. Expect new line and data [ABCD]: ', b'AB\x05CD\r', b'ABCD', b'AB\r\nCD'),
            (119, b'Type AB, Ctrl-R, CD, Enter. Expect redisplay and data [ABCD]: ', b'AB\x12CD\r', b'ABCD', b'AB#\r\nABCD'),
            (120, b'Type AB, Ctrl-U, CD, Enter. Expect new line and data [CD]: ', b'AB\x15CD\r', b'CD', b'AB#\r\nCD'),
            (121, b'Type AB, Ctrl-X, CD, Enter. Expect erased line and data [CD]: ', b'AB\x18CD\r', b'CD', b'CD'),
        ]
        for number, prompt, keys, data, visible in [(*case, case[3]) for case in cases] + controls:
            if number == 116:
                yield (b'CONSTEST /0116\r', b'Can this keyboard send ASCII DEL (7Fh)? (Y/U; U=untested) ', 30)
                yield (b'Y', prompt, 30)
            else:
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
            assert display(before + echo) == display(before + visible), (number, 'visible edit differs', echo)
            observed.append({'case': number, 'keys_hex': keys.hex(), 'returned_hex': data.hex(), 'visible_edit_verified': True})
            yield (b'Y', f'{number:04d}  P  R'.encode(), 30)
            yield (b'', b'A0>_ ', 30)
        yield (b'CONSTEST /0117\r', b'Press any key to start the test: ', 30)
        # WAITRDY consumes one readiness key before calling Function 10. Send
        # both bytes in order; the second must abandon the caller, not return.
        before = trace.read_bytes()
        yield (b'K\x03', b'A0>_ ', 30)
        delta = trace.read_bytes()[len(before):]
        assert b'OBSERVED: Function 10 returned to CONSTEST.' not in delta
        assert b'Do OBSERVED and EXPECTED match?' not in delta
        yield (b'VER\r', b'A0>_ ', 30)
        assert b'BetterCP/M' in trace.read_bytes()[len(before):]
        observed.append({'case': 117, 'keys_hex': '4b03', 'oracle': 'CCP return without Function 10 return diagnostic, then VER recovery'})
        yield (b'BYE /Y\r', b'System halted', 10)
    session(args.simulator.resolve(), disks, commands(), trace)
    assert sha(original) == report['sha256']
    result = {'baseline_sha256': report['sha256'], 'program_sha256': sha(program), 'simulator_sha256': sha(args.simulator), 'pyte_module': pyte.__file__, 'pyte_version': version('pyte'), 'cases': observed, 'pass': len(observed), 'required_pass': len(observed)-1, 'profile_pass': 1, 'oracle': 'literal returned buffers and independently rendered final input echo before confirmation', 'scope': 'cpmsim Functions 1, 6 and 10 selected input recipes; blocking observation limited to the recorded silence interval; no native Model 4 claim'}
    (work/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'pass': len(observed), 'evidence': str(work)}, indent=2))


if __name__ == '__main__':
    main()
