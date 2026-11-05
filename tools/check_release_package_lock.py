#!/usr/bin/env python3
"""Read-only five-lock plus separately versioned documentation verification.

GPL-2.0-or-later. No archive writes, extraction, software builds, tags or uploads.
"""
import argparse
import json
import zipfile
import subprocess
from pathlib import Path
from release_documentation import FINAL_NAME, load_lock, locked_files, verify_documentation


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('packages', type=Path)
    p.add_argument('--repository', type=Path, required=True)
    p.add_argument('--documentation', type=Path)
    p.add_argument('--allow-preview', action='store_true')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    lock, raw = load_lock(a.repository.resolve())
    document = a.documentation or a.packages / FINAL_NAME
    protected = {(a.packages / row['filename']).resolve() for row in lock['packages']}
    protected.add(document.resolve())
    if a.output.resolve() in protected or a.output.exists():
        p.error('Report output must be new and cannot replace an input')
    try:
        five = locked_files(a.packages.resolve(), lock)
        docs = verify_documentation(document, lock, raw, allow_preview=a.allow_preview, repo=a.repository.resolve())
        result = {'status': 'REVIEW_STATIC_CHECKS_PASS' if docs['documentation_revision'] is None else 'SPLIT_IDENTITIES_STATIC_CHECKS_PASS',
                  'locked_packages': five, 'documentation': docs,
                  'runtime_qualification': 'NOT_REPEATED; retained evidence applies only to identical locked bytes',
                  'remaining': ['Final content/example/license/format review', 'Actual release index/checksum update after accepted Documentation build'],
                  'publication': 'HOLD', 'tagging': 'HOLD', 'failures': []}
    except (ValueError, OSError, KeyError, json.JSONDecodeError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        result = {'status': 'FAIL', 'publication': 'HOLD', 'tagging': 'HOLD', 'failures': [str(error)]}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + chr(10))
    print(result['status'])
    return int(result['status'] == 'FAIL')


if __name__ == '__main__':
    raise SystemExit(main())
