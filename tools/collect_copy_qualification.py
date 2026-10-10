#!/usr/bin/env python3
"""Archive COPY qualification with strict agreement on tested binaries."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--case', action='append', required=True, metavar='LABEL=REPORT')
    parser.add_argument('--transient-only', action='store_true', help='Require COPY identity; RCP is a reference snapshot, not a claimed test target')
    parser.add_argument('--run-record', type=Path, help='Preserve orchestration commands and exit codes')
    parser.add_argument('--seed', type=Path, help='Preserve the exact input simulator disk/configuration directory')
    parser.add_argument('--scope', default='Agreed common COPY functionality; handoff and full release conformance remain separate')
    args = parser.parse_args()
    expected = {'copy_sha256': digest(ROOT / 'build/utilities/COPY.COM'),
                'rcp_sha256': digest(ROOT / 'build/cpx/RCP.CPX')}
    cases = []
    for item in args.case:
        label, path = item.split('=', 1)
        assert Path(label).name == label and label not in ('.', '..')
        assert label not in [case[0] for case in cases], label
        report = Path(path).resolve()
        evidence = json.loads((report / 'evidence.json').read_text())
        assert evidence['result'] == 'PASS', label
        assert evidence['copy_sha256'] == expected['copy_sha256'], (label, 'tested COPY binary differs')
        for key, value in expected.items():
            if key not in evidence and args.transient_only and key == 'rcp_sha256':
                continue
            assert evidence[key] == value, (label, key, 'tested binary differs')
        if 'bdos_sha256' in evidence:
            assert evidence['bdos_sha256'] == digest(ROOT / 'build/bdos/bdos.bin'), (label, 'BDOS differs')
        cases.append((label, report))
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    if args.run_record:
        record = json.loads(args.run_record.read_text())
        assert record and all(case['exit_code'] == 0 for case in record), 'incomplete qualification run'
        shutil.copy2(args.run_record, output / 'run-record.json')
    if args.seed:
        shutil.copytree(args.seed.resolve(), output / 'input-seed')
    for label, report in cases:
        shutil.copytree(report, output / 'reports' / label)
    paths = [ROOT / 'build/utilities/COPY.COM', ROOT / 'build/cpx/RCP.CPX',
             ROOT / 'build/bdos/bdos.bin', ROOT / 'src/cpx/rcp.mac',
             ROOT / 'src/bdos/unified.mac', ROOT / 'src/system/layout.inc',
             ROOT / 'docs/engineering/COPY Utility.md', Path(__file__).resolve()]
    paths += sorted((ROOT / 'tools').glob('test*copy*.py'))
    paths += sorted((ROOT / 'src/cpx').glob('copy-*.inc'))
    paths += [ROOT / 'src/utilities/common' / name for name in ('duselect.inc', 'operandqual.inc', 'attrselect.inc')]
    paths += [ROOT / 'tools/build_rcp_transients.py', ROOT / 'docs/engineering/COPY Specification.md']
    for path in paths:
        target = output / 'snapshot' / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    files = {str(path.relative_to(output)): {'bytes': path.stat().st_size, 'sha256': digest(path)}
             for path in sorted(output.rglob('*')) if path.is_file()}
    (output / 'manifest.json').write_text(json.dumps({
        'scope': args.scope,
        'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'working_tree_snapshot': True,
        'tested_binaries': {'copy_sha256': expected['copy_sha256']} if args.transient_only else expected,
        'reference_binaries': expected,
        'cases': [{'label': label, 'source': str(report), 'evidence': f'reports/{label}/evidence.json'}
                  for label, report in cases], 'files': files}, indent=2) + '\n')
    print(f'Preserved {len(cases)} matching COPY reports and {len(files)} files in {output}')


if __name__ == '__main__':
    main()
