#!/usr/bin/env python3
"""GPL-2.0-or-later. Check controlled repository documentation file targets and anchors."""
import argparse
import json
import re
import subprocess
from pathlib import Path
from release_documentation import links, resolve_link, heading_ids


def check_repository(repo, revision):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args]).decode()
    tracked = set(git('ls-tree', '-r', '--name-only', revision).splitlines())
    cache = {}
    def read(name):
        if name not in cache:
            cache[name] = git('show', revision + ':' + name)
        return cache[name]
    errors, count = [], 0
    for name in sorted(tracked):
        if not (name.startswith('docs/') or '/' not in name) or Path(name).suffix not in ('.md', '.txt', '.rst', '.html'):
            continue
        for link in links(read(name)):
            if re.match(r'\w+://|mailto:', link):
                continue
            target, fragment = resolve_link(name, link)
            if target not in tracked:
                if not any(n.startswith(target.rstrip('/') + '/') for n in tracked):
                    errors.append({'source': name, 'link': link, 'error': 'missing target'})
            elif fragment and Path(target).suffix in ('.md', '.txt') and fragment not in heading_ids(read(target)):
                errors.append({'source': name, 'link': link, 'error': 'missing anchor'})
            count += 1
    return {'status': 'FAIL' if errors else 'PASS', 'revision': revision, 'links_checked': count, 'errors': errors}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repository', type=Path, required=True)
    p.add_argument('--revision', required=True)
    a = p.parse_args()
    result = check_repository(a.repository, a.revision)
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result['errors']))
