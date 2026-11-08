"""Release heading preserves its fixed field and honest development fallback."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from build_ccp import assemble
from utility_versions import expand_versions


class ReleaseHeadingTests(unittest.TestCase):
    def test_fixed_field_and_automatic_selection(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            images = []
            for development in (False, True):
                with patch('utility_versions.display_development', return_value=development):
                    text = expand_versions('        ORG 100H\nBC_VERSION: ; @release-heading@\nAFTER: RET\n END\n')
                image = assemble(Path.home()/'bin/z80asm', text,
                                 root/f'{development}.bin', root/f'{development}.lst', 0x100)
                self.assertEqual(image[-1:], b'\xc9')
                images.append(image)
            self.assertEqual(len(images[0]), len(images[1]))
            release=json.loads((Path(__file__).resolve().parents[1]/'metadata/release-package.json').read_text())['version']
            self.assertTrue(images[0].startswith(('\r\nBetterCP/M '+release+'\r\n$').encode()))
            expected='BetterCP/M '+release if release=='1.1' else 'BetterCP/M development (after core 1.0)'
            self.assertTrue(images[1].startswith(('\r\n'+expected+'\r\n$').encode()))


if __name__ == '__main__':
    unittest.main()
