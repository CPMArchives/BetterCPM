#!/usr/bin/env python3
"""A cancelled batch capture must terminate its own emulator process."""
import os
import signal
import subprocess
import tempfile
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


def main():
    for mode in ('normal','cancel','timeout'):check(mode)
    print('PASS: normal completion, cancellation cleanup, timeout cleanup; only the launched PID is signalled')


if __name__=='__main__':main()
