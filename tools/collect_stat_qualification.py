#!/usr/bin/env python3
"""Preserve passing STAT reports, binaries and source hashes in one local bundle."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', action='append', default=[], metavar='LABEL=REPORT')
    parser.add_argument('--log', action='append', default=[], type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    cases = []
    for item in args.case:
        label, name = item.split('=', 1)
        assert label and Path(label).name == label and label not in ('.', '..')
        report = Path(name).resolve()
        evidence = json.loads((report / 'evidence.json').read_text())
        assert evidence['result'] == 'PASS', (label, evidence)
        shutil.copytree(report, output / 'reports' / label)
        cases.append({'label': label, 'source_report': str(report),
                      'tested_stat_sha256': evidence.get('stat_sha256'),
                      'evidence': 'reports/' + label + '/evidence.json'})
    logs = output / 'logs'; logs.mkdir()
    for path in args.log:
        assert 'passed' in path.read_text(errors='replace').lower(), path
        shutil.copy2(path, logs / path.name)
    shutil.copy2(ROOT / 'build/utilities/STAT.COM', output / 'STAT.COM')
    sources = [ROOT / 'src/utilities/stat.mac', ROOT / 'src/system/layout.inc',
               ROOT / 'docs/engineering/128 STAT Utility.md']
    sources += sorted((ROOT / 'tools').glob('test_stat*.py'))
    sources += sorted((ROOT / 'tools').glob('test_model4_stat*.py'))
    sources += sorted((ROOT / 'tools').glob('test_z80pack_stat*.py'))
    for path in sources:
        destination = output / 'sources' / path.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    files = {str(path.relative_to(output)): {'bytes': path.stat().st_size, 'sha256': digest(path)}
             for path in sorted(output.rglob('*')) if path.is_file()}
    (output / 'manifest.json').write_text(json.dumps({
        'scope': 'STAT utility qualification; BIOS IOBYTE routing remains separate',
        'final_stat_bytes': (output / 'STAT.COM').stat().st_size,
        'final_stat_sha256': digest(output / 'STAT.COM'), 'cases': cases,
        'provenance_note': 'Earlier reports retain their tested binary hashes. The final change only corrects the loaded-RSX MEM range endpoint; final MEM and summary-guard checks use the final binary. Retained diagnostic traces are not additional passing cases.',
        'files': files}, indent=2) + '\n')
    print(f'Preserved {len(cases)} passing reports and {len(files)} files in {output}')


if __name__ == '__main__':
    main()
