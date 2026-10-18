#!/usr/bin/env python3
"""Native malformed-CPX recovery and removal, with immutable shipped-file audit."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from add_cpm_file_to_dmk import (extract_raw, add_file, FILESYSTEM_FIRST_SECTOR,
                                 SECTOR_SIZE, DIRECTORY_ENTRIES)
from build_montezuma_extended_790k import build
from run_validation_model4 import audit_files
from run_validation_returning import sha
from run_trs80_command import DEFAULT_EMULATOR, key_args
from trs80gp_launch import run
from test_sysgen_install import screen


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    w = a.output.resolve()
    w.mkdir(parents=True, exist_ok=False)
    report = json.loads((a.baseline / 'report.json').read_text())
    original = a.baseline / report['image']
    assert report['target'] == 'trs80gp' and sha(original) == report['sha256']
    raw = extract_raw(original.read_bytes())
    for i in range(DIRECTORY_ENTRIES):
        off = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE + i * 32
        if raw[off] == 0 and raw[off + 1:off + 12] == b'STARTUP SUB':
            raw[off] = 0xE5
    fixtures = {
        'BAD.CPX': b'INVALID HEADER'.ljust(128, b'\0'),
        'STARTUP.SUB': b'CPX LOAD BAD\r\nCPX LIST\r\nTYPE CHECK.TXT\r\n\x1a',
        'CLEAN.SUB': b'CPX UNLOAD BAD\r\nCPX LIST\r\nRSX LIST\r\nTYPE DONE.TXT\r\n\x1a',
        'CHECK.TXT': b'BAD CPX RECOVERY REACHED\r\n\x1a',
        'DONE.TXT': b'BAD CPX REMOVED SAFELY\r\n\x1a',
    }
    import hashlib
    for name, data in fixtures.items():
        (w / name).write_bytes(data)
        add_file(raw, name, data)
    image = w / 'a.dmk'
    image.write_bytes(build(bytes(raw)))
    shutil.copy2(__file__, w / 'executed-runner.py')
    cmd = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx',
           '-d0', str(image), '-itime', '15000',
           '-iw', 'BAD CPX RECOVERY REACHED', '-id', '6000', '-it']
    cmd += key_args('SUBMIT CLEAN\r')
    cmd += ['-iw', 'BAD CPX REMOVED SAFELY', '-id', '6000', '-it', '-ix']
    (w / 'invocation.json').write_text(json.dumps(cmd, indent=2) + '\n')
    run(cmd, cwd=w, timeout=480, check=True)
    captures = sorted(w.glob('trs80-text-*.bin'))
    assert len(captures) == 2
    texts = [screen(f) for f in captures]
    for i, text in enumerate(texts):
        (w / f'screen-{i}.txt').write_text(text + '\n')
    first, last = texts
    assert 'CPX?' in first and 'BAD.CPX' in first and 'RCP.CPX' in first
    assert 'BAD CPX RECOVERY REACHED' in first
    assert 'BAD CPX REMOVED SAFELY' in last and 'RCP.CPX' in last
    assert 'No RSXs loaded' in last and 'TPA available: 53K' in last
    # Only examine output after the removal command; earlier warnings may
    # legitimately remain in the screen history.
    removed = last[last.index('CPX UNLOAD BAD'):]
    assert 'BAD.CPX' not in removed and 'CPX?' not in removed
    audit = audit_files(original, image,
                        dict(report, included=[f for f in report['included']
                                               if f['name'] != 'STARTUP.SUB']), w)
    r = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'bettercpm-default',
                        '-n', str(w / 'file-audit/after.raw')],
                       cwd=w / 'file-audit', capture_output=True, check=True)
    (w / 'filesystem.txt').write_bytes(r.stdout + r.stderr)
    assert sha(original) == report['sha256']
    (w / 'result.json').write_text(json.dumps({
        'status': 'PASS', 'baseline_sha256': report['sha256'],
        'fixtures': {n: hashlib.sha256(d).hexdigest() for n, d in fixtures.items()},
        'runner_sha256': sha(Path(__file__)), 'emulator_sha256': sha(DEFAULT_EMULATOR),
        'file_audit': audit,
        'scope': 'native invalid optional CPX rejection, retained RCP and profile, explicit removal, repeated batch continuation and 53K; STARTUP.SUB is a declared fixture'
    }, indent=2) + '\n')
    print('PASS native malformed CPX recovery', w)


if __name__ == '__main__':
    main()
