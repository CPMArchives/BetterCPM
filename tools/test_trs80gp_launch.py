#!/usr/bin/env python3
"""A cancelled batch capture must terminate its own emulator process."""
import os
import signal
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import trs80gp_launch as launch


def check(mode):
    calls=[]
    terminated=False
    def open_app(command,**kwargs):
        prefix='BETTERCPM_TRS80_PIDFILE='
        pidfile=next(arg[len(prefix):] for arg in command if arg.startswith(prefix))
        Path(pidfile).write_text('12345')
    def kill(pid,sig):
        nonlocal terminated
        assert pid==12345
        calls.append(sig)
        if sig==signal.SIGTERM:
            if terminated:raise ProcessLookupError()
            terminated=True
            return
        assert sig==0
        if terminated or mode=='normal':raise ProcessLookupError()
        if mode=='cancel':raise KeyboardInterrupt()
    with tempfile.TemporaryDirectory() as temp:
        command=[str(Path(temp)/'Emulator.app/Contents/MacOS/trs80gp'),'-batch']
        with patch.object(launch.sys,'platform','darwin'), \
             patch.object(launch,'launch_services_lookup',return_value=0), \
             patch.dict(os.environ,{'BETTERCPM_TRS80GP_DIRECT':'0'}), \
             patch.object(launch.subprocess,'run',side_effect=open_app), \
             patch.object(launch.os,'kill',side_effect=kill), \
             patch.object(launch.time,'monotonic',side_effect=[0,20]), \
             patch.object(launch.time,'sleep'):
            try:
                result=launch.run(command,cwd=Path(temp),timeout=10)
            except KeyboardInterrupt:
                assert mode=='cancel'
            except subprocess.TimeoutExpired:
                assert mode=='timeout'
            else:
                assert mode=='normal' and result.returncode==0
    assert (signal.SIGTERM in calls)==(mode!='normal'),(mode,calls)


class LaunchTests(unittest.TestCase):
    def test_denied_service_does_not_spawn_gui(self):
        with patch.object(launch.sys,'platform','darwin'), \
             patch.object(launch,'launch_services_lookup',return_value=1100), \
             patch.object(launch.subprocess,'run') as run:
            with self.assertRaisesRegex(launch.LaunchServicesUnavailable,
                                        'permission denied.*1100'):
                launch.run(['/Applications/trs80gp.app/Contents/MacOS/trs80gp'],
                           cwd=Path('/tmp'),timeout=1)
            run.assert_not_called()

    def test_missing_service_is_not_reported_as_permission_denial(self):
        with patch.object(launch,'launch_services_lookup',return_value=1102):
            with self.assertRaisesRegex(launch.LaunchServicesUnavailable,
                                        'service lookup failed.*1102'):
                launch.require_launch_services()

    def test_allowed_direct_execution_preserves_arguments(self):
        command=['/Applications/trs80gp.app/Contents/MacOS/trs80gp','-m4','-batch']
        result=subprocess.CompletedProcess(command,0)
        with patch.object(launch.sys,'platform','darwin'), \
             patch.object(launch,'launch_services_lookup',return_value=0), \
             patch.dict(launch.os.environ,{'BETTERCPM_TRS80GP_DIRECT':'1'}), \
             patch.object(launch.subprocess,'run',return_value=result) as run:
            self.assertIs(launch.run(command,cwd=Path('/tmp'),timeout=3),result)
            run.assert_called_once_with(command,cwd=Path('/tmp'),check=True,timeout=3)

    def test_non_mac_execution_does_not_probe_macos(self):
        with patch.object(launch.sys,'platform','linux'), \
             patch.object(launch,'launch_services_lookup') as probe, \
             patch.object(launch.subprocess,'run') as run:
            launch.run(['/tmp/trs80gp','-batch'],cwd=Path('/tmp'),timeout=2,check=False)
            probe.assert_not_called()
            run.assert_called_once_with(['/tmp/trs80gp','-batch'],cwd=Path('/tmp'),check=False,timeout=2)



def main():
    for mode in ('normal','cancel','timeout'):check(mode)
    print('PASS: normal completion, cancellation cleanup, timeout cleanup; only the launched PID is signalled')


if __name__=='__main__':
    main()
    unittest.main()
