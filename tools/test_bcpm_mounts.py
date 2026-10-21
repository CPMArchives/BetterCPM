#!/usr/bin/env python3
"""Exercise daily launcher mount policy against a private fake HOME/toolchain."""
import os
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='bcpm-mount-test-') as temp:
        home=Path(temp);repo=home/'projects/git/BetterCPM';daily=repo/'build/z80pack-daily';disks=daily/'disks';disks.mkdir(parents=True)
        system=repo/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk';system.parent.mkdir(parents=True);system.write_bytes(b'A')
        trs=repo/'build/trs80/BetterCPM-Distribution-trs80gp-80T-DS-System.dmk';trs.parent.mkdir(parents=True);trs.write_bytes(b'A')
        utils=repo/'build/utilities-disks';utils.mkdir();raw=utils/'BetterCPM-Utilities-z80pack-332K.dsk';raw.write_bytes(b'B');(utils/'BetterCPM-Utilities-trs80gp-80T-DS-800K.dmk').write_bytes(b'B')
        (daily/'launch-z80pack.command').write_text('#!/bin/sh\nexit 0\n');(daily/'launch-z80pack.command').chmod(0o755)
        exe=home/'trs80/trs80gp-2/mac/trs80gp.app/Contents/MacOS/trs80gp';exe.parent.mkdir(parents=True);exe.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$HOME/launch-args"\n');exe.chmod(0o755)
        env=dict(os.environ,HOME=str(home));script=ROOT/'tools/bcpm'
        def run(cmd):return subprocess.run(['/opt/homebrew/bin/bash',str(script),cmd],env=env,capture_output=True)
        old=home/'conformance.dsk';old.write_bytes(b'unchanged');(disks/'driveb.dsk').symlink_to(old)
        assert run('z').returncode==0
        assert (disks/'driveb.dsk').resolve()==raw.resolve() and old.read_bytes()==b'unchanged'
        assert run('t').returncode==0
        import time
        for _ in range(100):
            if (home/'launch-args').exists():break
            time.sleep(.01)
        args=(home/'launch-args').read_text().splitlines();assert args[args.index('-d1')+1].endswith('BetterCPM-Utilities-trs80gp-80T-DS-800K.dmk')
        assert not any('Conformance' in x for x in args)
        (disks/'driveb.dsk').unlink();(disks/'driveb.dsk').write_bytes(b'personal disk')
        assert run('z').returncode!=0 and (disks/'driveb.dsk').read_bytes()==b'personal disk'
        (disks/'driveb.dsk').unlink();raw.unlink();assert run('z').returncode!=0
        tools=repo/'tools';tools.mkdir();(tools/'build_distribution.py').touch();(tools/'build_utilities_disk.py').touch()
        fake=home/'fakebin';fake.mkdir()
        for name,body in [('git','echo git "$@" >> "$HOME/build-order"'),('python3','echo python3 "$@" >> "$HOME/build-order"; touch "$HOME/projects/git/BetterCPM/build/utilities-disks/BetterCPM-Utilities-z80pack-332K.dsk"')]:
            path=fake/name;path.write_text('#!/bin/sh\n'+body+'\n');path.chmod(0o755)
        env['PATH']=str(fake)+os.pathsep+env['PATH']
        assert run('build').returncode==0
        order=(home/'build-order').read_text().splitlines()
        assert order[0]=='git pull --ff-only' and 'build_distribution.py' in order[1] and 'build_utilities_disk.py --build' in order[2]
        assert (disks/'driveb.dsk').resolve()==raw.resolve()
        print('PASS: both B mounts, old media preserved, no automatic conformance mount, regular-file and missing-image safeguards')


if __name__=='__main__':main()
