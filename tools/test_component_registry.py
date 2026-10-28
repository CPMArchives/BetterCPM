"""Registry migration invariants and malformed-input refusal."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import component_registry as registry
from utility_versions import identities
from version_metadata import rows


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.data = registry.load()

    def rejects(self, mutate):
        data = copy.deepcopy(self.data)
        mutate(data)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'registry.json'
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                registry.load(path)

    def test_complete_import_and_paths(self):
        self.assertEqual(len(self.data['components']), 60)
        self.assertEqual(len(identities()), 47)
        self.assertEqual(identities()['DDT'], ('1.0', 3))
        self.assertEqual(identities()['PIP'], ('1.0', 30))
        self.assertEqual(identities()['BYE'], ('1.0', 2))
        for key, component in self.data['components'].items():
            self.assertNotIn(key, ('utility:ZSM4', 'utility:LINK'))
            for path in component['roots'] + component['builders']:
                self.assertTrue((registry.ROOT / path).is_file(), path)
            if component['tracking'] == 'initial':
                self.assertGreaterEqual(component['revision'], 1)

    def test_legacy_projections_exact(self):
        for relative, text in registry.projections().items():
            self.assertEqual((registry.ROOT / relative).read_bytes(), text.encode())
        self.assertEqual(next(x for x in rows() if x['component'] == 'BDOS')['implementation_version'], '1.10')

    def test_new_utility_assignments(self):
        for name in ('MOVE', 'WARM', 'DLINK', 'SEARCH'):
            self.assertEqual(registry.identity('utility:' + name, self.data), ('1.0', 1))

    def test_ted_initial_adaptation_identity(self):
        self.assertEqual(self.data['components']['utility:TED']['tracking'], 'initial')
        self.assertEqual(identities()['TED'], ('1.0', 2))
        self.assertEqual(registry.identity('utility:TED', self.data), ('1.0', 2))

    def test_component_projection_is_independent(self):
        before = registry.identity('utility:DDT', self.data)
        self.data['components']['utility:PIP']['revision'] += 1
        self.assertEqual(registry.identity('utility:DDT', self.data), before)
        self.data['components']['utility:DDT']['version'] = '2.0'
        self.assertEqual(registry.identity('utility:DDT', self.data), ('2.0', 3))
        self.data['components']['utility:DDT']['revision'] = 1000
        self.assertEqual(registry.identity('utility:DDT', self.data), ('2.0', 1000))

    def test_invalid_revisions(self):
        for value in (0, -1, True, 1.5, '002'):
            self.rejects(lambda d: d['components']['utility:DDT'].update(revision=value))

    def test_incomplete_identity_and_path_escape(self):
        self.rejects(lambda d: d['components']['utility:DDT'].update(version=None))
        self.rejects(lambda d: d['components']['utility:DDT'].update(roots=['../outside']))
        self.rejects(lambda d: d['components']['utility:DDT'].update(version='1.0\n'))

    def test_projection_coverage(self):
        self.rejects(lambda d: d['legacy_utility_order'].append('DDT'))
        self.rejects(lambda d: d['legacy_utility_order'].remove('DDT'))
        self.rejects(lambda d: d['legacy_subsystem_rows'][1].update(implementation_version='99.0'))

    def test_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'duplicate.json'
            path.write_text('{"schema":1,"schema":2}')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                registry.load(path)


if __name__ == '__main__':
    unittest.main()
