#!/usr/bin/env python3
"""Check the merged MOVE assignment change on private release-image copies."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from run_validation_cpmsim_monitors import audit
from run_validation_returning import sha
from test_z80pack_sysgen_install import session
from test_z80pack_attributes import directory


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    w = a.output.resolve()
    w.mkdir(parents=True, exist_ok=False)
    b = a.baseline.resolve()
    report = json.loads((b / 'report.json').read_text())
    assert report['target'] == 'z80pack' and sha(b / report['image']) == report['sha256']
    (w / 'disks').mkdir()
    shutil.copy2(b / 'diskdefs', w / 'diskdefs')
    shutil.copy2(__file__, w / 'executed-runner.py')
    disks = {d: w / f'disks/drive{d}.dsk' for d in 'abc'}
    for d, image in disks.items():
        shutil.copy2(b / report['image'], image)
        if d != 'a':
            subprocess.run(['cpmrm', '-T', 'raw', '-f', 'bettercpm-default',
                            str(image), '0:*.*'], cwd=w, check=True, capture_output=True)
    payload = b'MOVE ASSIGNMENT CONTENT\r\n\x1a'.ljust(128, b'\x1a')
    f = w / 'source.txt'
    f.write_bytes(payload)
    for name in ('ONE.TXT', 'TWO.TXT'):
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default',
                        str(disks['b']), str(f), '0:' + name], cwd=w, check=True)
    reference = w / 'source-records.bin'
    subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default',
                    str(disks['b']), '0:ONE.TXT', str(reference)], cwd=w, check=True)
    expected_records = reference.read_bytes()
    assert len(expected_records) == 128 and expected_records.startswith(payload)
    commands = ['MOVE C3:=B0:ONE.TXT', 'MOVE C4:RENAMED.TXT=B0:TWO.TXT',
                'MOVE B0:RESTORED.TXT=C3:ONE.TXT', 'MOVE B5:=C4:RENAMED.TXT']
    sim = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    steps = [(c.encode() + b'\r', b'A0>_ ', 30) for c in commands]
    steps += [(b'BYE\r', b'System halted', 30)]
    trace = session(sim, w / 'disks', steps, w / 'transcript.bin')
    assert b'INVALID' not in trace and b'NOT FOUND' not in trace and b'\r\n?\r\n' not in trace
    expected = {('b', 0, 'RESTORED.TXT'), ('b', 5, 'RENAMED.TXT')}
    inventories = {}
    for d in 'bc':
        listing = subprocess.check_output(['cpmls', '-T', 'raw', '-f',
                  'bettercpm-default', '-u', str(disks[d])], cwd=w, text=True)
        inventories[d] = listing
    for d, user, name in expected:
        out = w / f'{d}-{user}-{name}'
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(disks[d]),
                        f'{user}:{name}', str(out)], cwd=w, check=True)
        assert out.is_file() and out.read_bytes() == expected_records
    for d in 'bc':
        raw = directory(disks[d], w / 'diskdefs')
        actual = {(raw[i], bytes(x & 127 for x in raw[i+1:i+12]))
                  for i in range(0, len(raw), 32) if raw[i] < 32}
        wanted = {(0,b'RESTOREDTXT'),(5,b'RENAMED TXT')} if d == 'b' else set()
        assert actual == wanted, (d, actual, wanted)
    shipped = audit(b, report, w, disks['a'])
    for d in 'bc':
        r = subprocess.run(['fsck.cpm', '-T', 'raw', '-f', 'bettercpm-default',
                            '-n', str(disks[d])], cwd=w, capture_output=True)
        (w / f'filesystem-{d}.txt').write_bytes(r.stdout + r.stderr)
        assert r.returncode == 0
    (w / 'result.json').write_text(json.dumps({'status': 'PASS',
        'baseline_sha256': report['sha256'], 'commands': commands,
        'simulator_sha256': sha(sim), 'runner_sha256': sha(w / 'executed-runner.py'),
        'inventories': inventories, 'unchanged_shipped_files': shipped,
        'scope': 'Resident exact/DU-only plain-equals MOVE; destination text, source deletion, caller A0 and independent filesystem checks.'}, indent=2) + '\n')
    print('PASS release MOVE assignment forms', w)


if __name__ == '__main__':
    main()
