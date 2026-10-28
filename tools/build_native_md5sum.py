#!/usr/bin/env python3
"""Assemble MD5SUM with ZSM4/LINK under CP/M and require cross/native parity."""
from pathlib import Path
import argparse
import os
import shutil
import tempfile
from build_native_trs80 import blank, run
Z80PACK = Path.home()/'projects/git/z80pack'
DEFAULT_CPMSIM = Z80PACK/'cpmsim/cpmsim'
DEFAULT_SYSTEM = Z80PACK/'cpmsim/disks/library/cpm22-62khd.dsk'
DEFAULT_TEMPLATE = Z80PACK/'cpmsim/disks/library/cpm22-1.dsk'
DEFAULT_TOOLS = Path.home()/'projects/git/cpm-compatibility/suite/build-tools'
from build_md5sum import ROOT


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cpmsim', type=Path, default=DEFAULT_CPMSIM)
    p.add_argument('--system-disk', type=Path, default=DEFAULT_SYSTEM)
    p.add_argument('--disk-template', type=Path, default=DEFAULT_TEMPLATE)
    p.add_argument('--tools', type=Path, default=DEFAULT_TOOLS)
    a = p.parse_args()
    os.environ['PATH'] = str(a.cpmsim.parent/'srctools')+os.pathsep+os.environ.get('PATH', '')
    report = ROOT/'build/md5sum-development'
    report.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='bettercpm-native-md5sum-') as temporary:
        work = Path(temporary)
        disks = work/'disks'
        disks.mkdir()
        shutil.copy2(a.system_disk, disks/'drivea.dsk')
        for drive in 'bcd':
            blank(a.disk_template, disks/f'drive{drive}.dsk')
        run('cpmcp', '-f', 'ibm-3740', str(disks/'drivec.dsk'),
            str(ROOT/'build/utilities/MD5SUM-NATIVE.MAC'), '0:MD5SUM.MAC')
        for tool in ('ZSM4.COM', 'LINK.COM'):
            run('cpmcp', '-f', 'ibm-3740', str(disks/'drived.dsk'), str(a.tools/tool), '0:'+tool)
        fixture = work/'FIX.DAT'
        fixture.write_bytes(b'123456789'+b'\x1a'*119)
        run('cpmcp', '-f', 'ibm-3740', str(disks/'driveb.dsk'), str(fixture), '0:FIX.DAT')
        commands = f'''set timeout 60
spawn {a.cpmsim} -z -d {disks}
expect_before timeout {{exit 2}}
expect "A>"
send -- "B:\r"
expect "B>"
send -- "D:ZSM4 B:MD5SUM=C:MD5SUM\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK MD5SUM\\[A\\]\r"
expect "CODE SIZE"
expect "B>"
send -- "MD5SUM /HELP /VER\r"
expect "Usage: MD5SUM"
expect "B>"
send -- "MD5SUM FIX.DAT /FILE=MD5SUM.LST\r"
expect "b42a83d49df3489b2324811d5ed28d76"
expect "1 file calculated; 1 list written."
expect "B>"
send -- "MD5SUM /CHECK FIX.DAT\r"
expect "1 verified."
expect "B>"
send -- "\\034"
expect eof
'''
        result = run('expect', '-c', commands, check=False)
        transcript = result.stdout+result.stderr
        (report/'NATIVE-MD5SUM-BUILD.LOG').write_text(transcript)
        if result.returncode:
            raise SystemExit('Native MD5SUM build/runtime failed:\n'+transcript)
        native = work/'MD5SUM.COM'
        run('cpmcp', '-f', 'ibm-3740', str(disks/'driveb.dsk'), '0:MD5SUM.COM', str(native))
        cross = (ROOT/'build/utilities/MD5SUM.COM').read_bytes()
        (report/'MD5SUM-native.COM').write_bytes(native.read_bytes()[:len(cross)])
        if native.read_bytes()[:len(cross)] != cross:
            mismatch = next(i for i,(x,y) in enumerate(zip(native.read_bytes(),cross)) if x!=y)
            raise SystemExit(f'MD5SUM native/cross byte mismatch at {mismatch:04X}')
        print(f'MD5SUM: {len(cross)} byte-identical bytes; CP/M command fixtures pass')


if __name__ == '__main__':
    main()
