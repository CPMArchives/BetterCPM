#!/usr/bin/env python3
"""GPL-2.0-or-later. Verify reader Documentation plus unchanged published software/evidence."""
import argparse
import json
from pathlib import Path
from release_documentation import FINAL_NAME, SOFTWARE_PATH, verify_documentation, verify_software


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('packages', type=Path)
    p.add_argument('--repository', type=Path, required=True)
    p.add_argument('--documentation', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists() or a.output.resolve() == (a.documentation or a.packages / FINAL_NAME).resolve():
        p.error('Output must be new and cannot replace an input')
    doc = verify_documentation(a.documentation or a.packages / FINAL_NAME, repo=a.repository)
    # The independently versioned Documentation records the current software packaging baseline.
    import zipfile
    from release_documentation import ROOT_NAME
    with zipfile.ZipFile(a.documentation or a.packages / FINAL_NAME) as z:
        baseline = json.loads(z.read(ROOT_NAME + '/Provenance/SOFTWARE-PACKAGES.json'))
    rows = verify_software(a.packages, baseline)
    result = {'status': 'PASS', 'documentation': doc, 'unchanged_software_and_evidence': rows,
              'software_runtime_tests': 'not repeated; matching bounded prior evidence retained'}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('x') as f:
        f.write(json.dumps(result, indent=2) + '\n')
    print('PASS')


if __name__ == '__main__':
    main()
