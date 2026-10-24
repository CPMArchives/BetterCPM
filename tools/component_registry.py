"""Authoritative component identities; compilation never assigns revisions.

Legacy TSV files are deterministic projections retained for existing consumers.
Source roots are ownership hints, not qualified fingerprint dependencies.
"""
from pathlib import Path
import argparse
import csv
import io
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'metadata/component-registry.json'
VERSION = re.compile(r'[0-9]+\.[0-9]+')


def load(path=None):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate registry key: ' + key)
            result[key] = value
        return result
    data = json.loads(Path(path or REGISTRY).read_text(encoding='utf-8'),
                      object_pairs_hook=unique)
    if data['schema'] != 1:
        raise ValueError('unsupported registry schema')
    for key, row in data['components'].items():
        if not re.fullmatch(r'(utility|subsystem|module):[A-Z][A-Z0-9]*', key):
            raise ValueError('invalid component key: ' + key)
        if row['tracking'] not in ('existing', 'initial', 'pending'):
            raise ValueError('invalid tracking state: ' + key)
        for field in ('version', 'api_version'):
            value = row[field]
            if value is not None and (not isinstance(value, str) or not VERSION.fullmatch(value)):
                raise ValueError('invalid ' + field + ': ' + key)
        revision = row['revision']
        if revision is not None and (type(revision) is not int or revision < 1):
            raise ValueError('invalid revision: ' + key)
        if row['tracking'] != 'pending' and (row['version'] is None or revision is None):
            raise ValueError('assigned identity is incomplete: ' + key)
        for field in ('roots', 'builders'):
            if not row[field] or len(row[field]) != len(set(row[field])):
                raise ValueError('empty or duplicate paths: ' + key)
            for relative in row[field]:
                p = Path(relative)
                if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0] not in ('src', 'tools'):
                    raise ValueError('invalid dependency root: ' + relative)
    order = data['legacy_utility_order']
    assigned = {key.split(':')[1] for key, row in data['components'].items()
                if key.startswith('utility:') and row['tracking'] in ('existing', 'initial')}
    if len(order) != len(set(order)) or set(order) != assigned:
        raise ValueError('legacy utility projection membership mismatch')
    for row in data['legacy_subsystem_rows']:
        if 'component_ref' in row:
            if row['component_ref'] != 'subsystem:' + row['component']:
                raise ValueError('invalid subsystem projection reference')
            if row['component_ref'] not in data['components']:
                raise ValueError('missing subsystem projection reference')
            if 'implementation_version' in row or 'interface_version' in row:
                raise ValueError('duplicated subsystem identity')
    return data


def identity(key, data=None):
    row = (data or load())['components'][key]
    if row['tracking'] == 'pending':
        raise ValueError('identity assignment pending: ' + key)
    return row['version'], row['revision']


def utility_identities(data=None):
    data = data or load()
    return {name: identity('utility:' + name, data)
            for name in data['legacy_utility_order']}


def subsystem_rows(data=None):
    data = data or load()
    result = []
    for original in data['legacy_subsystem_rows']:
        row = dict(original)
        ref = row.pop('component_ref', None)
        if ref:
            component = data['components'][ref]
            row['interface_version'] = component['api_version'] or '-'
            row['implementation_version'] = component['version'] or '-'
        result.append(row)
    return result


def tsv(fields, rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, delimiter='\t', lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def projections(data=None):
    data = data or load()
    return {
        'metadata/utility-versions.tsv': tsv(['utility', 'version', 'build'],
            [{'utility': name, 'version': version, 'build': revision}
             for name, (version, revision) in utility_identities(data).items()]),
        'metadata/subsystem-versions.tsv': tsv(
            ['component', 'identity', 'interface_version', 'implementation_version', 'status', 'notes'],
            subsystem_rows(data)),
    }


def module_version(name):
    data = load()['components']
    key = 'utility:RCP' if name.upper() == 'RCP' else 'module:' + name.upper()
    row = data.get(key)
    return tuple(map(int,row['version'].split('.'))) if row and row['version'] else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--write', action='store_true')
    args = parser.parse_args()
    from version_metadata import render, render_manager
    views = projections()
    views.update({'src/bdos/versions.inc': render(),
                  'src/utilities/cpxvers.inc': render_manager('CPX', 'CX_VERSION'),
                  'src/utilities/rsxvers.inc': render_manager('RSX', 'RS_VERSION')})
    for relative, text in views.items():
        path = ROOT / relative
        if args.write:
            path.write_text(text, encoding='utf-8')
        elif path.read_bytes() != text.encode('utf-8'):
            raise SystemExit(relative + ' is stale; run tools/component_registry.py --write')
    print('Component registry projections: PASS')


if __name__ == '__main__':
    main()
