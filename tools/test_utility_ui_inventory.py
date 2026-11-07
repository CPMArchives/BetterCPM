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
    noargs=('ADMTST','ANSITST','VT52TST')
    if any(rows[name][3]=='C' for name in noargs):
        proof=json.loads((ROOT/'docs/engineering/evidence/2026-11-03-ui-argument-validation/results.json').read_text())
        assert proof['host']=='PASS' and proof['cpmsim']=='PASS'
        for name in noargs:
            path='src/utilities/'+name.lower()+'.mac'
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==proof['source_sha256'][path],('stale argument evidence',name)
            artifact=ROOT/'build/utilities'/(name+'.COM')
            if artifact.exists():
                assert hashlib.sha256(artifact.read_bytes()).hexdigest()==proof['current'][name]['sha256'],('stale argument binary',name)
        native=json.loads((ROOT/'docs/engineering/evidence/2026-11-03-ui-noargs-model4-pass/results.json').read_text())
        assert native['status']=='PASS' and native['captures']==22
        for name in noargs:
            assert native['receipt']['binaries'][name]==proof['current'][name],('native argument payload differs',name)
    if rows['XSUB'][3]=='C':
        # Revision 008 accepts an optional DU. Its two-platform run and parser
        # checks were recorded together after the old no-operand contract changed.
        evidence=ROOT/'docs/engineering/evidence/2026-11-06-rsx-offline'
        proof=json.loads((evidence/'results.json').read_text())
        assert proof['status']=='PASS' and proof['host_checks']['test_rsx_source_cli']=='PASS'
        baselines=json.loads((ROOT/'metadata/component-baselines.json').read_text())['records']
        source='src/utilities/xsub.mac'
        for target,receipt in (('z80pack','cpmsim.json'),('trs80gp','model4.json')):
            baseline=baselines[f'utility:XSUB|{target}|default|cross']
            assert baseline['assigned_identity']['revision']==8
            assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==baseline['inputs']['files'][source]
            guest=json.loads((evidence/receipt).read_text())
            assert guest['status']=='PASS' and guest['target']==target
        if (ROOT/'build/utilities/XSUB.COM').is_file():
            from test_utility_finalization import execute
            output, requests = execute('XSUB', ' B0: EXTRA', queries=False)
            assert 'Invalid usage.' in output and not requests
            _, requests = execute('XSUB', ' B0:', queries=False)
            assert [request[1] for request in requests] == [3, 1]
    print(f'PASS: {len(rows)} unique utility rows cover distribution, companion, host helpers and registry')

if __name__=='__main__':main()
