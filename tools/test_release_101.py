"""Check the 1.0 lock, explicit new-release selection and supplemental/docs inputs."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import package_release_candidates as packaging
from release_documentation import selection_mapping
from fdf_v1 import parse, serialize, read_fdb
from build_fdf_catalog import catalogue_payload

ROOT=Path(__file__).resolve().parents[1]


class Release101Tests(unittest.TestCase):
    def test_default_does_not_reopen_10_lock(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);lock=root/'docs/releases/non-documentation-lock-1.0/LOCK.json'
            lock.parent.mkdir(parents=True);lock.write_text('{}')
            with patch.object(packaging,'ROOT',root),self.assertRaisesRegex(ValueError,'locked'):
                packaging.assemble(SimpleNamespace())

    def test_unsupported_version_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'unsupported'):
            packaging.assemble(SimpleNamespace(version='1.1'))

    def test_cannot_label_10_assets_as_101(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'metadata').mkdir()
            (root/'metadata/release-assets-1.0.1.json').write_text('{"version":"1.0"}')
            with patch.object(packaging,'ROOT',root),patch.object(packaging,'git',return_value=b''),self.assertRaisesRegex(ValueError,'version metadata mismatch'):
                packaging.assemble(SimpleNamespace(version='1.0.1'))

    def test_preserve_old_asset_manifest(self):
        old=json.loads((ROOT/'metadata/release-assets.json').read_text())
        new=json.loads((ROOT/'metadata/release-assets-1.0.1.json').read_text())
        self.assertEqual(old['version'],'1.0');self.assertEqual(new['version'],'1.0.1')
        self.assertEqual(len(new['assets']),6)
        self.assertTrue(all('1.0.1' in a['filename'] for a in new['assets']))
        self.assertFalse(set(a['filename'] for a in old['assets']) & set(a['filename'] for a in new['assets']))

    def test_supplement_is_separate_and_compiles_identically(self):
        standard=read_fdb(catalogue_payload()).descriptors
        supplement=parse((ROOT/'metadata/supplemental/1.0.1/SUPPDISK.FDF').read_text())
        self.assertEqual(len(standard),108);self.assertEqual(len(supplement),4)
        self.assertEqual({f.ident for f in supplement},{'CPCSYS','CPCDATA','PCW','BW14'})
        self.assertTrue(all(f.cks <= 32 for f in supplement))
        self.assertFalse({f.ident for f in standard} & {f.ident for f in supplement})
        self.assertEqual(serialize(supplement),(ROOT/'metadata/supplemental/1.0.1/SUPPDISK.FDB').read_bytes())

    def test_distribution_retains_existing_checksum_profile(self):
        import inspect
        import build_distribution
        self.assertNotIn('--ram-only',inspect.getsource(build_distribution.current_build))

    def test_bios_identity_covers_configuration_and_tables(self):
        from bios_implementation import bundle,PIECES
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name,path in PIECES['z80pack'].items():
                p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(name.encode())
            layout=root/'build/z80pack/checksum-layout.json'
            layout.write_text('{"cks_limit":32}')
            extra=root/'build/z80pack/checksum-extra.bin';extra.write_bytes(bytes(96))
            original=bundle(root,'z80pack');value=json.loads(original)
            self.assertNotIn('checksum-extra',value['pieces'])
            (root/PIECES['z80pack']['config']).write_bytes(b'changed configuration')
            self.assertNotEqual(bundle(root,'z80pack'),original)
            layout.write_text('{"cks_limit":48}')
            self.assertEqual(json.loads(bundle(root,'z80pack'))['pieces']['checksum-extra']['bytes'],96)
            layout.write_text('{"cks_limit":33}')
            with self.assertRaises(ValueError):bundle(root,'z80pack')

    def test_reader_documentation_has_four_manuals_and_valid_local_links(self):
        path='packaging/1.0.1/documentation-selection.json'
        selection=json.loads((ROOT/path).read_text());mapping=selection_mapping(selection)
        mapping['README.md']='packaging/1.0.1/README-Documentation.md'
        mapping['Provenance/selection.json']=path;mapping.pop('Provenance/SOFTWARE-PACKAGES.json')
        tracked={source:(ROOT/source).read_bytes() for source in mapping.values()}
        files,evidence=packaging.documentation_members(tracked,'a'*40,'1.0.1')
        self.assertEqual(len(evidence['manuals']),4);self.assertGreater(evidence['local_links_checked'],100)
        self.assertFalse(any(n.endswith(('.pdf','.docx','.zip','.dsk','.dmk')) for n in files))
        self.assertNotIn(b'30b24a021cc3a90e',files['README.md'])


if __name__=='__main__':unittest.main()
