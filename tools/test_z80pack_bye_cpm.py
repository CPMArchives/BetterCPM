#!/usr/bin/env python3
"""Qualify shipped BYE on disposable copies of the cpmsim System Disk."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

from build_z80pack_bye import ROOT, help_text, version_text
from test_z80pack_sysgen_install import session


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image-dir', type=Path, default=ROOT/'build/z80pack/disks/library')
    p.add_argument('--diskdefs', type=Path)
    p.add_argument('--simulator', type=Path,
                   default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    a = p.parse_args()
    image = a.image_dir.resolve()/'BetterCPM-Distribution-z80pack-332K.dsk'
    definitions = (a.diskdefs or a.image_dir/'diskdefs').resolve()
    original = image.read_bytes()
    with tempfile.TemporaryDirectory(prefix='bettercpm-bye-cpm-') as temp:
        work = Path(temp)
        disks = work/'disks'
        disks.mkdir()
        shutil.copy2(definitions, work/'diskdefs')
        shutil.copy2(image, disks/'drivea.dsk')
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',
                        str(disks/'drivea.dsk'),'0:BYE.COM',str(work/'BYE.COM')],
                       cwd=work,check=True,capture_output=True)
        binary = (ROOT/'build/z80pack-tools/BYE.COM').read_bytes()
        shipped = (work/'BYE.COM').read_bytes()
        assert shipped[:len(binary)] == binary
        assert len(shipped)-len(binary) < 128
        prompt = b'A0>_ '
        ask = b'Exit cpmsim? [y/N] '
        steps = []
        for command, screen in [(b'BYE /ver\r',version_text()),
                                (b'BYE /Y /HELP /VER\r',help_text())]:
            steps.extend([(command,screen.encode('ascii'),10),(b'',prompt,10)])
        steps.extend([(b'BYE /Y /UNKNOWN\r',b'Use BYE /HELP for help.',10),
                      (b'',prompt,10)])
        for key in (b'n',b'\r',b'\x1b',b'\x03'):
            steps.extend([(b'BYE\r',ask,10),(key,prompt,10)])
        steps.extend([(b'BYE\r',ask,10),(b'x',ask,10),(b'y',b'System halted',10)])
        trace = session(a.simulator.resolve(),disks,steps)
        assert trace.count(ask) == 6
        shutil.copy2(image, disks/'drivea.dsk')
        trace = session(a.simulator.resolve(),disks,
                        [(b'BYE /y\r',b'System halted',10)])
        assert ask not in trace
        assert image.read_bytes() == original
        print('PASS: shipped BYE readback; /VER, /HELP precedence, invalid arguments, '
              'N/Enter/Escape/Ctrl-C cancellation, invalid key, Y and /Y exit on cpmsim.')


if __name__ == '__main__':
    main()
