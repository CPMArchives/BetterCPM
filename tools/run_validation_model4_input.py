#!/usr/bin/env python3
"""Observe native Model 4 input on private media, without confirming suite cards."""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw, add_file
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR, key_args
from trs80gp_launch import run
from test_sysgen_install import screen


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recovery_checks(text):
    """Require executed VER output and a final CCP prompt, not input echo."""
    return {
        'ccp_version_command': 'BetterCP/M VER 1.0 (Resident, RCP Build ' in text,
        'final_ccp_prompt': text.rstrip().endswith('A0>'),
        'caller_abandoned': 'OBSERVED: Function 10 returned to CONSTEST.' not in text,
        'no_confirmation': 'Do OBSERVED and EXPECTED match?' not in text,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'suite', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--group', choices=('basic', 'controls'), default='basic')
    args = parser.parse_args()
    report = json.loads((args.baseline/'report.json').read_text())
    original = args.baseline/report['image']
    assert report['target'] == 'trs80gp' and sha(original) == report['sha256']
    program = args.suite/'suite/build/CONSTEST.COM'
    hashes = {line.split()[1]: line.split()[0] for line in (args.suite/'suite/build/SHA256SUMS.txt').read_text().splitlines() if line.strip()}
    assert sha(program) == hashes['CONSTEST.COM']
    args.output.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='model4-input-', dir=args.output.resolve()))
    raw = extract_raw(original.read_bytes())
    add_file(raw, 'CONSTEST.COM', program.read_bytes())
    specimen = build(bytes(raw))
    cases = [
        (106, 'Expect count 02 and data [AB]: ', 'AB\r', 'OBSERVED: count=02; data=[AB]', 'Expect count 02 and data [AB]: AB'),
        (115, 'Expect count 02/data [AC]: ', 'AB\x08C\r', 'OBSERVED: count=02; data=[AC]', 'Expect count 02/data [AC]: AC'),
        (121, 'Expect erased line and data [CD]: ', 'AB\x18CD\r', 'OBSERVED: count=02; data=[CD]', 'Expect erased line and data [CD]: CD'),
    ]
    if args.group == 'controls':
        cases = [
            (118, 'Expect new line and data [ABCD]: ', 'AB\x05CD\r', 'OBSERVED: count=04; data=[ABCD]', 'Expect new line and data [ABCD]: AB\nCD'),
            (119, 'Expect redisplay and data [ABCD]: ', 'AB\x12CD\r', 'OBSERVED: count=04; data=[ABCD]', 'Expect redisplay and data [ABCD]: AB#\nABCD'),
            (120, 'Expect new line and data [CD]: ', 'AB\x15CD\r', 'OBSERVED: count=02; data=[CD]', 'Expect new line and data [CD]: AB#\nCD'),
        ]
    results = []
    manifest = {'baseline_sha256': report['sha256'], 'program_sha256': sha(program), 'emulator_sha256': sha(DEFAULT_EMULATOR), 'cases': results, 'scope': 'native keyboard matrix input, returned buffers and final visible edit; no suite Y confirmation or suite PASS-row claim'}
    for number, prompt, keys, returned, visible in cases:
        case = work/f'{number:04d}'
        case.mkdir()
        image = case/'a.dmk'
        image.write_bytes(specimen)
        command = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx', '-d0', str(image), '-itime', '15000', '-iw', 'Type TYPE README.TXT for more', '-id', '6000']
        command += key_args(f'CONSTEST /{number:04d}\r') + ['-iw', prompt]
        command += key_args(keys) + ['-iw', 'Do OBSERVED and EXPECTED match?', '-id', '120', '-it', '-ix']
        run(command, cwd=case, timeout=180)
        text = screen(case/'trs80-text-0.bin')
        (case/'screen.txt').write_text(text+'\n')
        # Wrapped prompt lines are normalized only for this contiguous phrase;
        # exact returned-buffer text remains a separate check.
        flattened = ''.join(line.rstrip() for line in text.splitlines())
        checks = {'returned_buffer': returned in text, 'visible_edit': visible in (text if '\n' in visible else flattened), 'awaiting_confirmation': 'Do OBSERVED and EXPECTED match?' in text}
        results.append({'case': number, 'keys_hex': keys.encode().hex(), 'checks': checks, 'status': 'PASS' if all(checks.values()) else 'FAIL', 'screen': f'{number:04d}/screen.txt'})
        assert sha(original) == report['sha256']
        (work/'result.json').write_text(json.dumps(manifest, indent=2)+'\n')
        print(json.dumps(results[-1]), flush=True)
    if args.group == 'controls':
        case = work/'0117'
        case.mkdir()
        image = case/'a.dmk'
        image.write_bytes(specimen)
        command = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx', '-d0', str(image), '-itime', '15000', '-iw', 'Type TYPE README.TXT for more', '-id', '6000']
        command += key_args('CONSTEST /0117\r') + ['-iw', 'Press any key to start the test: ']
        command += key_args('K\x03') + ['-id', '6000']
        command += key_args('VER /VER\r') + ['-iw', 'BetterCP/M VER 1.0', '-id', '120', '-it', '-ix']
        run(command, cwd=case, timeout=300)
        text = screen(case/'trs80-text-0.bin')
        (case/'screen.txt').write_text(text+'\n')
        checks = recovery_checks(text)
        results.append({'case': 117, 'keys_hex': '4b03', 'checks': checks, 'status': 'PASS' if all(checks.values()) else 'FAIL', 'screen': '0117/screen.txt'})
        assert sha(original) == report['sha256']
        (work/'result.json').write_text(json.dumps(manifest, indent=2)+'\n')
        print(json.dumps(results[-1]), flush=True)
    print(json.dumps({'evidence': str(work), 'pass': sum(c['status']=='PASS' for c in results)}), flush=True)
    assert all(c['status']=='PASS' for c in results), 'native input check failed; see retained screens'


if __name__ == '__main__':
    main()
