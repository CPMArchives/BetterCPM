#!/usr/bin/env python3
"""Keep UI review coverage aligned with distribution and registry membership."""
import hashlib,json,re
from pathlib import Path
from build_utilities_disk import COMPONENTS
from noah_distribution import COMPONENTS as COMPANION
from component_registry import utility_identities
ROOT=Path(__file__).resolve().parents[1]


def main():
    manifest=json.loads((ROOT/'metadata/distribution.json').read_text())
    expected={x['name'][:-4] for x in manifest['system_disk'] if x['name'].endswith('.COM')}
    expected|={x[:-4] for x in COMPONENTS|COMPANION if x.endswith('.COM')}
    expected|=set(utility_identities())
    source=(ROOT/'docs/engineering/UI-Conformance-Matrix.md').read_text()
    rows={}
    for line in source.splitlines():
        if not re.match(r'^\| [A-Z][A-Z0-9]* \|',line):continue
        cells=[x.strip() for x in line.strip('|').split('|')]
        name=cells[0];assert name not in rows,('duplicate row',name)
        assert len(cells)==12,(name,len(cells))
        assert set(cells[1:11])<={'C','E','N','O'},(name,'invalid status')
        assert cells[-1],(name,'missing basis')
        rows[name]=cells
    assert set(rows)==expected,{'missing':sorted(expected-set(rows)),'extra':sorted(set(rows)-expected)}
    if rows['TED'][8]=='C':
        proof=json.loads((ROOT/'docs/engineering/evidence/2026-11-03-ted-choice/results.json').read_text())
        assert proof['host']=='PASS' and proof['cpmsim']=='PASS'
        for path,digest in proof['source_sha256'].items():
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,('stale TED confirmation evidence',path)
    print(f'PASS: {len(rows)} unique utility rows cover distribution, companion, host helpers and registry')

if __name__=='__main__':main()
