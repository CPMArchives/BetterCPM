"""Shared numeric identities and exact transitional display compatibility."""
import unittest
from component_identity import title, identification, revision_text


class IdentityTests(unittest.TestCase):
    def test_numeric(self):
        self.assertEqual(title('DDT','1.9',4),'DDT 1.9 (004)')
        self.assertEqual(title('DDT','2.0',5),'DDT 2.0 (005)')
        self.assertEqual(title('DDT','2.0',1000),'DDT 2.0 (1000)')

    def test_development(self):
        self.assertEqual(title('DDT','1.0',2,development=True),'DDT 1.0 (002-dev)')
        with self.assertRaises(ValueError):
            revision_text(2,development='unknown')

    def test_checked_does_not_replace_numeric_revision(self):
        self.assertEqual(title('DIR','1.0',8,checked_id='a'*32),'DIR 1.0 (008)')

    def test_resident_numeric_uses_supplied_owner_revision(self):
        self.assertEqual(title('DIR','1.0',15,resident=True),'DIR 1.0 (015)')

    def test_identification_block(self):
        self.assertEqual(identification('DDT','1.0',2,'Dynamic Debugging Tool'),
                         'DDT 1.0 (002)\r\n  - - -\r\n | BetterCP/M Utilities\r\n | Dynamic Debugging Tool\r\n')

    def test_legacy_forms(self):
        self.assertEqual(title('BYE','1.0',1,style='legacy'),'BYE 1.0 (Build 001)')
        self.assertEqual(title('DIR','1.0',8,style='legacy-common'),'BetterCP/M DIR 1.0 (Build 008)')
        self.assertEqual(title('DIR','1.0',15,style='legacy-common',resident=True),
                         'BetterCP/M DIR 1.0 (Resident, RCP Build 015)')
        self.assertEqual(title('DIR','1.0',8,style='legacy-common',checked_id='abcdef01'+'0'*24),
                         'BetterCP/M DIR 1.0 (Checked abcdef01)')

    def test_invalid_identity(self):
        for revision in (0,-1,True,'004',4.5):
            with self.assertRaises(ValueError):title('DDT','1.0',revision)
        for name,version in [('ddt','1.0'),('DDT','1.0\n'),('DDT$','1.0')]:
            with self.assertRaises(ValueError):title(name,version,2)

    def test_unsafe_or_ambiguous_display_refused(self):
        for description in ('bad\nline','unsafe$','\x00'):
            with self.assertRaises(ValueError):identification('DDT','1.0',2,description)
        with self.assertRaises(ValueError):title('DDT','1.0',2,style='legacy',development=True)
        with self.assertRaises(ValueError):title('DDT','1.0',2,style='unknown')


if __name__ == '__main__':
    unittest.main()
