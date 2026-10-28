#!/usr/bin/env python3
"""Assemble PATCH with ZSM4/LINK under CP/M and require cross/native parity."""
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
from build_patch import ROOT


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cpmsim', type=Path, default=DEFAULT_CPMSIM)
    p.add_argument('--system-disk', type=Path, default=DEFAULT_SYSTEM)
    p.add_argument('--disk-template', type=Path, default=DEFAULT_TEMPLATE)
    p.add_argument('--tools', type=Path, default=DEFAULT_TOOLS)
    a = p.parse_args()
    os.environ['PATH'] = str(a.cpmsim.parent/'srctools')+os.pathsep+os.environ.get('PATH', '')
    report = ROOT/'build/patch-development'
    report.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='bettercpm-native-patch-') as temporary:
        work = Path(temporary)
        disks = work/'disks'
        disks.mkdir()
        shutil.copy2(a.system_disk, disks/'drivea.dsk')
        for drive in 'bcd':
            blank(a.disk_template, disks/f'drive{drive}.dsk')
        run('cpmcp', '-f', 'ibm-3740', str(disks/'drivec.dsk'),
            str(ROOT/'build/utilities/PATCH-NATIVE.MAC'), '0:PATCH.MAC')
        for tool in ('ZSM4.COM', 'LINK.COM'):
            run('cpmcp', '-f', 'ibm-3740', str(disks/'drived.dsk'), str(a.tools/tool), '0:'+tool)
        fixture=work/'IN.DAT';fixture.write_bytes(bytes(range(128)))
        patch=work/'FIX.PAT';patch.write_bytes(b'INPUT IN.DAT\r\nOUTPUT OUT.DAT\r\n00: 00 01 02 -> FF FE\r\n02: 02 -> FD\r\n\x1a')
        for name in ('IN.DAT','FIX.PAT'):
            run('cpmcp','-f','ibm-3740',str(disks/'driveb.dsk'),str(work/name),'0:'+name)
        commands = f'''set timeout 15
spawn {a.cpmsim} -z -d {disks}
expect_before timeout {{exit 2}}
expect "A>"
send -- "B:\r"
expect "B>"
send -- "D:ZSM4 B:PATCH=C:PATCH\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK PATCH\\[A\\]\r"
expect "CODE SIZE"
expect "B>"
send -- "PATCH /HELP /VER\r"
expect "Usage: PATCH"
expect "B>"
send -- "PATCH FIX.PAT\r"
expect "full verification passed."
expect "B>"
send -- "\\034"
expect eof
'''
        result = run('expect', '-c', commands, check=False)
        transcript = result.stdout+result.stderr
        (report/'NATIVE-PATCH-BUILD.LOG').write_text(transcript)
        if result.returncode:
            run('cpmcp','-f','ibm-3740',str(disks/'driveb.dsk'),'0:PATCH.COM',str(report/'PATCH-failed-native.COM'))
            raise SystemExit('Native PATCH build/runtime failed:\n'+transcript)
        native = work/'PATCH.COM'
        run('cpmcp', '-f', 'ibm-3740', str(disks/'driveb.dsk'), '0:PATCH.COM', str(native))
        patched=work/'OUT.DAT'
        run('cpmcp','-f','ibm-3740',str(disks/'driveb.dsk'),'0:OUT.DAT',str(patched))
        assert patched.read_bytes()==bytes([255,254,253])+bytes(range(3,128))
        cross = (ROOT/'build/utilities/PATCH.COM').read_bytes()
        (report/'PATCH-native.COM').write_bytes(native.read_bytes()[:len(cross)])
        if native.read_bytes()[:len(cross)] != cross:
            mismatch = next(i for i,(x,y) in enumerate(zip(native.read_bytes(),cross)) if x!=y)
            raise SystemExit(f'PATCH native/cross byte mismatch at {mismatch:04X}')
        print(f'PATCH: {len(cross)} byte-identical bytes; CP/M command fixtures pass')


if __name__ == '__main__':
    main()
