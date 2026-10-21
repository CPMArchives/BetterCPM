#!/usr/bin/env python3
"""Inventory pinned suite cards without treating exclusions as passes.

External numeric witnesses remain separate from the independent suite's rows.
Group summaries and controlled unit checks are retained for review, rather than
being expanded into invented per-card native results.
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('suite', 'baseline', 'returning', 'external', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--reviewed', type=Path, help='Explicit card-to-evidence review; never inferred from group counts')
    a = p.parse_args()
    report = json.loads((a.baseline / 'report.json').read_text())
    assert sha(a.baseline / report['image']) == report['sha256']
    revision = subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=a.suite, text=True).strip()
    assert revision == 'a9a878fcd2e36698c7e856654a85847a004fdd20'
    catalog_path = a.suite / 'suite/design/case-to-executable-catalog.tsv'
    oracle_path = a.suite / 'docs/conformance/tables/oracle-definitions.tsv'
    catalog = list(csv.DictReader(catalog_path.open(), delimiter='\t'))
    oracles = {r['ledger_entry']: r for r in csv.DictReader(
        oracle_path.open(), delimiter='\t')}
    assert len(catalog) == len({r['ledger_entry'] for r in catalog}) == 627
    observed, evidence, external = {}, {}, {}
    canonical = {r["ledger_entry"]: r["executable"] for r in catalog}
    raw_rows = 0
    for path in sorted(a.returning.glob('*/result.json')):
        data = json.loads(path.read_text())
        assert data['baseline_sha256'] == report['sha256']
        assert data['suite_revision'] == revision
        assert not data['failed_or_error_rows'], str(path)
        evidence[str(path)] = sha(path)
        raw_rows += len(data['rows'])
        program = data['command'].split()[0] + '.COM'
        for number, value in data['rows'].items():
            # Common prerequisite rows may appear in several executables.
            # Use the pinned catalog's owner rather than overwrite by scan order.
            if canonical[number] != program:
                continue
            assert number not in observed, 'duplicate canonical execution'
            observed[number] = value, str(path)
    runs = json.loads((a.external / 'runner-results.json').read_text())
    for folder in ('console-output', 'console-input', 'readonly', 'ecology'):
        assert runs[folder]['exit_code'] == 0, folder
        parents = list((a.external / folder).glob('*/result.json'))
        assert len(parents) == 1, folder
        path = parents[0]
        data = json.loads(path.read_text())
        assert data['baseline_sha256'] == report['sha256']
        evidence[str(path)] = sha(path)
        for entry in data.get('cases', data.get('observations', [])):
            number = entry if isinstance(entry, int) else entry.get('case', entry.get('item'))
            if number is None:
                continue
            if isinstance(entry, dict) and entry.get('status', 'PASS') != 'PASS':
                continue
            external.setdefault(f'{int(number):04d}', []).append(str(path))
    reviewed = {}
    if a.reviewed:
        review = json.loads(a.reviewed.read_text())
        assert review['baseline_sha256'] == report['sha256']
        for group in review['groups']:
            assert group['status'] in ('PASS_CONTROLLED','PASS_EXTERNAL','PASS_NATIVE','PASS_PROFILE','PROFILE_DIFFERENCE','NOT_APPLICABLE','FAIL','BLOCKED') and group['scope']
            for source in group['evidence']:
                assert sha(Path(source['path'])) == source['sha256'], source
                evidence[source['path']] = source['sha256']
            for number in group['cards']:
                assert number not in reviewed and number in canonical
                classification = next(r['classification'] for r in catalog if r['ledger_entry'] == number)
                assert group['status'] != 'NOT_APPLICABLE' or classification == 'OPTIONAL', number
                reviewed[number] = group
    rows = []
    for case in catalog:
        number = case['ledger_entry']
        row, source = observed.get(number, ({}, ''))
        classification = case['classification']
        if number in reviewed and reviewed[number]['status'] in ('FAIL','BLOCKED','PROFILE_DIFFERENCE'):
            status = reviewed[number]['status']
        elif row.get('status') == 'P':
            status = 'PASS_SUITE'
        elif number in reviewed and classification in ('REQUIRED','OPTIONAL'):
            status = reviewed[number]['status']
        elif number in external and classification == 'REQUIRED':
            status = 'PASS_EXTERNAL'
        elif number in external:
            status = 'OBSERVED_EXTERNAL_PROFILE'
        elif classification == 'OUTSIDE SCOPE':
            status = 'OUTSIDE_BASELINE'
        elif classification == 'OPTIONAL':
            status = 'OPTIONAL_PROFILE_REVIEW'
        elif classification != 'REQUIRED':
            status = 'OBSERVED' if row.get('status') == 'O' else 'NOT_RUN_NONGUARANTEED'
        else:
            status = 'OPEN_RECONCILIATION'
        rows.append({'card': number, 'case_id': case['case_id'],
                     'executable': case['executable'], 'classification': classification,
                     'requirement': case['requirement'], 'oracle': oracles[number]['oracle'],
                     'cpmsim_suite_status': row.get('status', 'NOT_CAPTURED'),
                     'accounting': status, 'suite_evidence': source,
                     'external_evidence': ';'.join(external.get(number, []) + [e['path'] for e in reviewed.get(number, {}).get('evidence', [])]),
                     'reviewed_scope': reviewed.get(number, {}).get('scope', ''),
                     'cpmsim_scope': reviewed.get(number, {}).get('platforms', {}).get('cpmsim', 'Actual suite/external row or shared-code oracle; see platform acceptance record'),
                     'native_card_status': reviewed.get(number, {}).get('platforms', {}).get('model4', 'Native group/compiled-common-code evidence; no invented per-card transcript')})
    a.output.mkdir(parents=True, exist_ok=True)
    with (a.output / 'cards.tsv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    incomplete = any(r['accounting'] in ('OPEN_RECONCILIATION','OPTIONAL_PROFILE_REVIEW') for r in rows)
    blocked = any(r['accounting'] in ('FAIL','BLOCKED') for r in rows)
    summary = {'schema': 2, 'status': 'ACCEPTANCE_BLOCKED' if blocked else ('ACCOUNTING_OPEN' if incomplete else 'ACCOUNTING_RECONCILED'), 'source_revision': report['source']['revision'],
               'baseline_sha256': report['sha256'], 'suite_revision': revision,
               'catalog_sha256': sha(catalog_path), 'oracles_sha256': sha(oracle_path),
               'cards': len(rows), 'raw_printed_rows': raw_rows, 'captured_suite_rows': len(observed),
               'suite_counts': dict(collections.Counter(r[0]['status'] for r in observed.values())),
               'accounting_counts': dict(collections.Counter(r['accounting'] for r in rows)),
               'open_required_by_program': dict(collections.Counter(
                   r['executable'] for r in rows if r['accounting'] == 'OPEN_RECONCILIATION')),
               'open_required_cards': [r['card'] for r in rows if r['accounting'] == 'OPEN_RECONCILIATION'],
               'evidence_sha256': evidence, 'cards_sha256': sha(a.output / 'cards.tsv'),
               'limits': 'Card accounting only, not final release acceptance. Suite rows remain actual observations. Controlled/private-provider and platform scopes are explicit; PROFILE_DIFFERENCE is not generic CP/M PASS. Native aggregate/common-code evidence is not expanded into invented per-card transcripts. Independent release/device gates still apply.'}
    (a.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: summary[k] for k in ('cards', 'captured_suite_rows', 'suite_counts', 'accounting_counts', 'open_required_by_program')}, indent=2))


if __name__ == '__main__':
    main()
