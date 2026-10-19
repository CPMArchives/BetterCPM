#!/usr/bin/env python3
"""Restore bounded ERA/DUP/SYSGEN recovery evidence against matched artifacts."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from run_validation_returning import sha
ROOT = Path(__file__).resolve().parents[1]
TESTS = ('test_era_destructive_failures', 'test_dup_command_line', 'test_sysgen_command_line', 'test_sysgen_export', 'test_sysgen_package_validation')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('build-root', 'baseline', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); w = a.output.resolve(); w.mkdir(parents=True, exist_ok=False)
    report = json.loads((a.baseline / 'report.json').read_text())
    original = a.baseline / report['image']; assert sha(original) == report['sha256']
    matched = {}
    for name in ('ERA.COM', 'DUP.COM', 'SYSGEN.COM'):
        value = sha(a.build_root / 'build/utilities' / name)
        assert value == next(x['sha256'] for x in report['included'] if x['name'] == name)
        matched[name] = value
    shutil.copy2(__file__, w / 'executed-runner.py'); results = {}
    for name in TESTS:
        shutil.copy2(ROOT / 'tools' / (name + '.py'), w / (name + '.py'))
        code = ('import sys;sys.path.insert(0,' + repr(str(ROOT / 'tools')) + ');from pathlib import Path;'
                'import build_system_package as b;b.ROOT=Path(' + repr(str(a.build_root.resolve())) + ');'
                'import ' + name + ' as t;t.ROOT=Path(' + repr(str(a.build_root.resolve())) + ');t.main()')
        r = subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True, text=True, timeout=300)
        (w / (name + '.txt')).write_text(r.stdout + r.stderr)
        results[name] = {'exit_code': r.returncode, 'test_sha256': sha(w / (name + '.py'))}
        print(name, r.returncode, r.stdout.strip(), flush=True)
    helpers = {}
    for name in ('test_bios.py', 'test_utility_versions.py', 'build_system_package.py', 'test_disk_utilities.py'):
        shutil.copy2(ROOT / 'tools' / name, w / name); helpers[name] = sha(w / name)
    assert sha(original) == report['sha256']
    passed = all(r['exit_code'] == 0 for r in results.values())
    (w / 'result.json').write_text(json.dumps({'status': 'PASS' if passed else 'FAIL', 'matched_binaries': matched,
        'tests': results, 'helpers': helpers, 'baseline_sha256': report['sha256'], 'runner_sha256': sha(w / 'executed-runner.py'),
        'scope': 'controlled instruction/BDOS/BIOS fault fixtures, no physical-media or power-loss claim'}, indent=2) + '\n')
    assert passed, 'see retained logs'


if __name__ == '__main__': main()
