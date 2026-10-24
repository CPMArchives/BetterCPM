#!/usr/bin/env python3
"""Profile selection, process propagation and stale/mixed-input rejection."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from build_profiles import (CONTEXT_ENV, PROFILES, context_environment,
                            profile_inputs, read_context, select_profile,
                            symbols, workspace, write_context)
from build_distribution import prepare_profile, source_identity
from checked_build_contract import load_contract

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'src/system/layout.inc'


class BuildProfiles(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)/'source'
        self.source = self.root/'src/system/layout.inc'
        self.source.parent.mkdir(parents=True)
        shutil.copy2(SOURCE, self.source)

    def test_qualified_boundaries_and_fixed_transient_addresses(self):
        before = SOURCE.read_bytes()
        for name, bdos, bios, top, tpa, reserved in [
                ('cpmsim-fullram', 0xE2BC, 0xF591, 0x10000, 57344, 0),
                ('cpmsim-legacy-checked', 0xD6BC, 0xE991, 0xF400, 54272, 3072)]:
            manifest, layout, _ = profile_inputs(PROFILES[name], SOURCE)
            values = symbols(layout)
            self.assertEqual((values['LY_BDOS'], values['LY_BIOS'], values['LY_LIMIT']),
                             (bdos, bios, top))
            self.assertEqual(manifest['capacities']['maximum_com_bytes'], tpa)
            self.assertEqual(values['LY_TOPRSV'], reserved)
            self.assertEqual((values['LY_LOAD'], values['LY_STKL'], values['LY_STKT'],
                              values['LY_SECTS'], values['LY_RLCAP']),
                             (0x100, 0x4C0, 0x500, 13, 0x3A4))
            self.assertEqual(manifest['format_epochs'], dict(private=2, carrier=2, package=2))
        self.assertEqual(SOURCE.read_bytes(), before)

    def test_generated_context_rejects_modified_or_mixed_inputs(self):
        context = write_context(PROFILES['cpmsim-fullram'], self.source)
        for file in [context, context.parent/'layout.inc', context.parent/'profile.inc']:
            before = file.read_bytes()
            file.write_bytes(before.replace(b'cpmsim-fullram', b'cpmsim-legacy-checked'))
            with self.assertRaises(ValueError):
                read_context(context, self.source)
            file.write_bytes(before)
        self.assertEqual(read_context(context, self.source)[0]['ram_end'], 65536)

    def test_context_rejects_changed_canonical_source(self):
        context = write_context(PROFILES['cpmsim-fullram'], self.source)
        self.source.write_text(self.source.read_text()+'\n; source changed\n')
        with self.assertRaisesRegex(ValueError, 'current source'):
            read_context(context, self.source)

    def test_new_numeric_symbol_requires_an_explicit_layout_decision(self):
        self.source.write_text(self.source.read_text()+'\nLY_NEW EQU 0E000H\n')
        with self.assertRaisesRegex(ValueError, 'classify'):
            profile_inputs(PROFILES['cpmsim-fullram'], self.source)

    def test_context_from_another_workspace_is_rejected(self):
        context = write_context(PROFILES['cpmsim-fullram'], self.source)
        with self.assertRaisesRegex(ValueError, 'different source workspace'):
            read_context(context, SOURCE)

    def test_python_assembly_and_child_process_use_the_same_context(self):
        tools = self.root/'tools'
        tools.mkdir()
        for name in ['build_profiles.py', 'system_layout.py', 'rsx_container.py', 'utility_versions.py']:
            shutil.copy2(ROOT/'tools'/name, tools/name)
        common = self.root/'src/utilities/common'
        common.mkdir(parents=True)
        shutil.copy2(ROOT/'src/utilities/common/version.inc', common/'version.inc')
        context = write_context(PROFILES['cpmsim-fullram'], self.source)
        environment = context_environment(context, self.source)
        environment['PYTHONPATH'] = str(tools)
        child = 'import json; from system_layout import LAYOUT, SYMBOLS; print(json.dumps([LAYOUT, SYMBOLS]))'
        parent = ('import json,subprocess,sys; from system_layout import LAYOUT, expand_layout; '
                  'print(json.dumps([LAYOUT, expand_layout("INCLUDE layout.inc\\nINCLUDE profile.inc\\n"), '
                  f'json.loads(subprocess.check_output([sys.executable,"-c",{child!r}]))]))')
        data = json.loads(subprocess.check_output([sys.executable, '-c', parent],
                                                 env=environment, cwd=self.root))
        self.assertEqual(data[0]['BDOS'], 0xE2BC)
        self.assertEqual(data[0], data[2][0])
        self.assertEqual(symbols(data[1]), data[2][1])
        self.assertIn('BP_CHECKED EQU 1', data[1])
        self.assertNotIn('INCLUDE', data[1])

    def test_prepared_cache_is_profile_specific_and_detects_drift(self):
        work = Path(self.temporary.name)/'work'
        identities = {name:source_identity(profile) for name, profile in PROFILES.items()}
        roots = {}
        for name, profile in PROFILES.items():
            root = prepare_profile(work, 'z80pack', identities[name], profile)
            roots[name] = root
            self.assertEqual(prepare_profile(work, 'z80pack', identities[name], profile, True), root)
        self.assertNotEqual(*roots.values())
        self.assertNotEqual(*identities.values())
        self.assertNotIn(workspace(work, 'z80pack'), roots.values())
        name = 'cpmsim-fullram';root = roots[name];profile = PROFILES[name]
        with self.assertRaisesRegex(ValueError, 'does not match'):
            prepare_profile(work, 'z80pack', identities['cpmsim-legacy-checked'], profile, True)
        extra = root/'src/unexpected.inc';extra.write_text('extra')
        with self.assertRaisesRegex(ValueError, 'file set changed'):
            prepare_profile(work, 'z80pack', identities[name], profile, True)
        extra.unlink()
        for rel in ['src/system/layout.inc', 'tools/build_bdos.py', 'build/profile/layout.inc']:
            path = root/rel;before = path.read_bytes();path.write_bytes(before+b'\n; changed\n')
            with self.assertRaisesRegex(ValueError, 'input changed'):
                prepare_profile(work, 'z80pack', identities[name], profile, True)
            path.write_bytes(before)

    def test_unsupported_and_unfinished_builds_fail_before_creating_output(self):
        environment = dict(os.environ);environment.pop(CONTEXT_ENV, None)
        for args in [
                ['--profile', 'cpmsim-fullram', '--target', 'all', '--prepare-profile'],
                ['--profile', 'cpmsim-fullram', '--target', 'trs80gp', '--prepare-profile'],
                ['--profile', 'cpmsim-fullram', '--target', 'z80pack'],
                ['--prepare-profile']]:
            work = Path(self.temporary.name)/'not-created'
            result = subprocess.run([sys.executable, str(ROOT/'tools/build_distribution.py'),
                                     *args, '--work', str(work), '--output', str(work/'output')],
                                    env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(work.exists())
        with self.assertRaisesRegex(ValueError, 'unknown'):
            select_profile('misspelled', 'z80pack')

    def test_prepared_context_cannot_emit_an_unintegrated_or_other_target_disk(self):
        profile = PROFILES['cpmsim-fullram']
        root = prepare_profile(Path(self.temporary.name)/'work', 'z80pack',
                               source_identity(profile), profile)
        environment = context_environment(root/'build/profile/context.json',
                                          root/'src/system/layout.inc')
        for script, message in [
                ('build_complete_system.py', b'full-system integration is pending'),
                ('build_z80pack_image.py', b'checked-profile disk generation is pending'),
                ('build_trs80_boot.py', b'cannot build Model 4 boot products')]:
            result = subprocess.run([sys.executable, str(root/'tools'/script)],
                                    env=environment, cwd=root,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(message, result.stdout)
        self.assertEqual({p.name for p in (root/'build').iterdir()}, {'profile'})

    def test_checked_contract_rejects_source_metadata_and_assembler_drift(self):
        profile = PROFILES['cpmsim-fullram']
        root = prepare_profile(Path(self.temporary.name)/'work', 'z80pack',
                               source_identity(profile), profile)
        assembler = Path.home()/'bin/z80asm'
        original = load_contract(root, assembler)
        for rel in ['src/system/command-stage2.mac', 'tools/checked_build_contract.py',
                    'metadata/utility-versions.tsv']:
            path = root/rel;before = path.read_bytes();path.write_bytes(before+b'\n')
            with self.assertRaisesRegex(ValueError, 'source closure changed'):
                load_contract(root, assembler)
            path.write_bytes(before)
        extra = root/'src/extra.inc';extra.write_text('extra')
        with self.assertRaisesRegex(ValueError, 'source closure changed'):
            load_contract(root, assembler)
        extra.unlink()
        wrong_assembler = Path(self.temporary.name)/'assembler';wrong_assembler.write_bytes(b'different')
        with self.assertRaisesRegex(ValueError, 'assembler differs'):
            load_contract(root, wrong_assembler)
        self.assertEqual(load_contract(root, assembler), original)

    def test_checked_contract_separates_profiles_without_binding_documentation_revisions(self):
        work = Path(self.temporary.name)/'work';assembler = Path.home()/'bin/z80asm'
        contracts = []
        for profile in PROFILES.values():
            root = prepare_profile(work, 'z80pack', source_identity(profile), profile)
            contract = load_contract(root, assembler)
            statefile = root/'profile-state.json';state = json.loads(statefile.read_text())
            state['source']['revision'] = 'documentation-only revision'
            statefile.write_text(json.dumps(state))
            self.assertEqual(load_contract(root, assembler)['compatibility_id'], contract['compatibility_id'])
            contracts.append(contract)
        self.assertNotEqual(contracts[0]['compatibility_id'], contracts[1]['compatibility_id'])
        self.assertEqual(contracts[0]['contract']['private_inputs'], contracts[1]['contract']['private_inputs'])


if __name__ == '__main__':
    unittest.main()
