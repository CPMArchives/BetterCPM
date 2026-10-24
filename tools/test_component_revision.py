"""Revision continuity, artifact integrity and two-stage acceptance guards."""
import copy
import unittest

from component_inputs import canonical, digest
from component_revision import accept, plan


def receipt(image=b'old executable', *, revision=14, version='1.0', source='old',
            target='z80pack', component='utility:DDT'):
    inputs = {'schema': 1, 'component': component,
              'variant': {'target': target, 'profile': 'default', 'build_mode': 'cross'},
              'identity_fields': {'version': version, 'api_version': None},
              'files': {'selected.mac': digest(source.encode())},
              'configuration': {}, 'toolchain': {'assembler_sha256': digest(b'tool')}}
    identity = {'version': version, 'revision': revision}
    return {'schema': 1, 'component': component, 'identity': identity,
            'artifact': {'name': 'DDT.COM', 'bytes': len(image), 'sha256': digest(image)},
            'input_record': {'schema': 1, 'assigned_identity': identity,
                             'inputs': inputs, 'fingerprint': digest(canonical(inputs))},
            'provenance': {'repository_commit': None}}


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.old_bytes = b'old executable'
        self.new_bytes = b'new executable'
        self.old = receipt()
        self.new = receipt(self.new_bytes, source='new')
        self.proposal = plan(self.old, self.old_bytes, self.new, self.new_bytes)

    def accept(self, final, image):
        return accept(self.proposal, self.old, self.old_bytes,
                      self.new, self.new_bytes, final, image)

    def test_changed_artifact_advances_once(self):
        self.assertEqual(self.proposal['proposed_identity']['revision'], 15)
        final_bytes = b'new executable with revision 015'
        final = receipt(final_bytes, revision=15, source='new')
        result = self.accept(final, final_bytes)
        self.assertEqual(result['identity']['revision'], 15)
        self.assertEqual(result['artifact']['sha256'], digest(final_bytes))

    def test_identical_rebuild_retains_revision(self):
        proposal = plan(self.old, self.old_bytes, self.old, self.old_bytes)
        self.assertEqual(proposal['proposed_identity']['revision'], 14)
        result = accept(proposal, self.old, self.old_bytes, self.old,
                        self.old_bytes, self.old, self.old_bytes)
        self.assertEqual(result['identity']['revision'], 14)

    def test_input_change_without_byte_change_records_equivalence(self):
        new = receipt(source='changed comment or byte-equivalent helper')
        proposal = plan(self.old, self.old_bytes, new, self.old_bytes)
        self.assertTrue(proposal['selected_inputs_changed'])
        self.assertFalse(proposal['executable_changed'])
        self.assertEqual(proposal['proposed_identity']['revision'], 14)

    def test_version_change_continues_sequence(self):
        new = receipt(self.new_bytes, source='new', version='2.0')
        proposal = plan(self.old, self.old_bytes, new, self.new_bytes)
        self.assertEqual(proposal['proposed_identity'], {'version':'2.0', 'revision':15})

    def test_no_rollover(self):
        old = receipt(revision=999)
        new = receipt(self.new_bytes, revision=999)
        self.assertEqual(plan(old,self.old_bytes,new,self.new_bytes)['proposed_identity']['revision'],1000)

    def test_candidate_must_use_old_revision(self):
        new = receipt(self.new_bytes, revision=15)
        with self.assertRaisesRegex(ValueError, 'reference revision'):
            plan(self.old, self.old_bytes, new, self.new_bytes)

    def test_tampered_artifact_and_missing_inputs(self):
        with self.assertRaisesRegex(ValueError, 'checksum'):
            plan(self.old, b'tampered', self.new, self.new_bytes)
        bad = copy.deepcopy(self.new)
        bad['input_record'] = None
        with self.assertRaisesRegex(ValueError, 'input record'):
            plan(self.old,self.old_bytes,bad,self.new_bytes)

    def test_cross_variant_refused(self):
        new = receipt(self.new_bytes, target='trs80gp')
        with self.assertRaisesRegex(ValueError, 'variant'):
            plan(self.old,self.old_bytes,new,self.new_bytes)

    def test_modified_proposal_refused(self):
        self.proposal['proposed_identity']['revision'] = 400
        with self.assertRaisesRegex(ValueError, 'proposal differs'):
            self.accept(receipt(self.new_bytes,revision=400,source='new'),self.new_bytes)

    def test_final_source_change_refused(self):
        with self.assertRaisesRegex(ValueError, 'final inputs'):
            self.accept(receipt(self.new_bytes,revision=15,source='later unreviewed edits'),self.new_bytes)

    def test_final_wrong_identity_refused(self):
        with self.assertRaisesRegex(ValueError, 'final identity'):
            self.accept(self.new,self.new_bytes)

    def test_retained_revision_cannot_change_final_bytes(self):
        proposal = plan(self.old,self.old_bytes,self.old,self.old_bytes)
        final = receipt(self.new_bytes)
        with self.assertRaisesRegex(ValueError, 'identical final'):
            accept(proposal,self.old,self.old_bytes,self.old,self.old_bytes,final,self.new_bytes)


if __name__ == '__main__':
    unittest.main()
