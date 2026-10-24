#!/usr/bin/env python3
"""Guard the native recovery oracle against startup banners and failed returns."""
import unittest
from run_validation_model4_input import recovery_checks


class RecoveryObserver(unittest.TestCase):
    healthy = 'Press any key to start the test:\nBetterCP/M VER 1.0 (Resident, RCP Build 012)\n\nA0>\n'

    def test_command_echo_not_required(self):
        self.assertTrue(all(recovery_checks(self.healthy).values()))

    def test_startup_banner_is_not_recovery(self):
        self.assertFalse(all(recovery_checks('BetterCP/M 1.0\nA0>\n').values()))

    def test_caller_return_is_not_recovery(self):
        self.assertFalse(all(recovery_checks('OBSERVED: Function 10 returned to CONSTEST.\n'+self.healthy).values()))

    def test_final_prompt_required(self):
        self.assertFalse(all(recovery_checks(self.healthy.replace('A0>', '')).values()))


if __name__ == '__main__':
    unittest.main()
