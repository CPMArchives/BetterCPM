#!/usr/bin/env python3
"""Check the public design tables; does not implement or qualify TCAP."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def check():
    schema = json.loads((ROOT / 'docs/engineering/contracts/tcap-1.0.json').read_text())
    document = (ROOT / 'docs/engineering/TCAP-Public-ABI.md').read_text()
    assert schema['schema'] == 1 and schema['service'] == 'TCAP'
    assert schema['version'] == [1, 0]
    for name, fields in schema['records'].items():
        cursor = 0
        names = set()
        rows = []
        for field in fields:
            assert field['offset'] == cursor, (name, 'gap/overlap', field)
            assert isinstance(field['bytes'], int) and field['bytes'] > 0
            assert field['field'] not in names, (name, 'duplicate field')
            names.add(field['field'])
            cursor += field['bytes']
            rows.append(f"| {field['offset']} | {field['bytes']} | `{field['field']}` |")
        assert cursor == schema['record_sizes'][name], (name, cursor)
        heading = f'### Wire record: {name} ({cursor} bytes)'
        assert document.count(heading) == 1, heading
        section = document.split(heading, 1)[1].split('\n##', 1)[0]
        actual = re.findall(r'^\| \d+ \| \d+ \| `\w+` \|$', section, re.M)
        assert actual == rows, (name, 'Markdown/schema divergence')
    assert schema['record_sizes'] == {
        'request': 32, 'snapshot': 64, 'eligibility': 96, 'token': 16,
        'provider_requirements': 64, 'owner_header': 32,
    }
    assert schema['records']['eligibility'][0]['field'] == 'snapshot'
    assert schema['records']['eligibility'][0]['bytes'] == schema['record_sizes']['snapshot']
    assert [o['value'] for o in schema['operations']] == list(range(8))
    assert len({o['name'] for o in schema['operations']}) == 8
    for op in schema['operations']:
        assert op['input_bytes'] in (0, 96) and op['output_bytes'] in (0, 64, 96)
        row = (f"| {op['value']:02X}h | {op['name']} | {op['input_bytes']} | "
               f"{op['output_bytes']} | {'16 bytes' if op['token'] else 'none'} |")
        assert row in document, op['name']
    assert list(map(int, schema['statuses'])) == list(range(21))
    assert list(map(int, schema['states'])) == list(range(6)) + [255]
    assert list(map(int, schema['modes'])) == list(range(7))
    for enum in ('statuses', 'states', 'modes'):
        assert len(set(schema[enum].values())) == len(schema[enum])
    for enum in ('statuses', 'states', 'modes'):
        for code, name in schema[enum].items():
            assert f'| {int(code):02X}h | {name} |' in document, (enum, code)
    for name, value in schema['masks'].items():
        assert isinstance(value, int) and 0 < value <= 65535, name
    for name, requirements in schema['implicit_requirements'].items():
        assert requirements['operations'] & ~schema['masks']['operations'] == 0
        assert requirements['cleanup'] & ~schema['masks']['cleanup'] == 0
        row = f"{requirements['operations']:04X}h | {requirements['cleanup']:04X}h"
        assert row in document, (name, 'implicit mask divergence')
    metadata = schema['metadata']
    assert metadata == {'major': 3, 'minor': 0, 'binding_type': 4,
                        'binding_bytes': 18, 'requirements_type': 5,
                        'requirements_bytes': 64, 'mcon': [1, 4]}
    assert metadata['requirements_bytes'] == schema['record_sizes']['provider_requirements']
    minimum_metadata = 12 + 2 + metadata['binding_bytes'] + 2 + metadata['requirements_bytes'] + 2 * 12
    assert minimum_metadata == 122 and minimum_metadata < 512
    assert schema['implicit_requirements']['takeover']['operations'] == 0x06BF
    assert schema['implicit_requirements']['emphasis']['operations'] == 0x0640
    return {'status': 'PASS', 'scope': 'structural documentation consistency only; no runtime conformance',
            'records': len(schema['records']), 'operations': len(schema['operations']),
            'statuses': len(schema['statuses']), 'states': len(schema['states']),
            'minimum_metadata_bytes': minimum_metadata}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
