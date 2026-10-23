#!/usr/bin/env python3
"""Execute all six /VER and /HELP entries on the full Z80 core; forbid non-console BDOS.

Checks exact metadata-owned identification, mixed requests, token boundaries,
TAB/space handling, maximum tails, unchanged FCB/context/tail, stack/registers,
code immutability, deterministic builds and four-digit build display.
"""
import argparse
import ctypes as C
import importlib
from pathlib import Path
import shutil
import subprocess
import tempfile
from unittest.mock import patch

from codec_version import DESCRIPTIONS, version_text, help_text, usage_text
from utility_versions import identities
from test_usq import SHIM
from test_usq_com import Command, diskkey

ROOT = Path(__file__).resolve().parents[1]


class VersionCommand(Command):
    console_only = True

    def bdos(self, fn, de):
        if self.console_only:
            assert fn == 9, ('version request invoked normal initialization/I/O', fn)
            # Console BDOS is as hostile to index registers as file BDOS.
            self.reg['IX'].value = 0xDEAD
            self.reg['IY'].value = 0xCAFE
        return super().bdos(fn, de)


def check(m, tail, expected, console_only=True):
    m.console_only = console_only
    m.reg['IX'].value = 0xABCD
    files = {diskkey(2,'KEEP.BIN',7):b'KEEP ALL BYTES'}
    assert m.run(tail, files, drive=2, user=7) == expected, (tail,m.console,expected)
    assert m.reg['IX'].value == 0xABCD
    assert not m.created and not m.deleted and not m.renamed and not m.opened
    assert m.drive == 2 and m.user == 7
    assert bytes(m.mem[0x81:0x81+len(tail)]) == tail.encode()
    if console_only:
        assert [fn for fn,_ in m.events] == [9]
        first = m.symbols['UC_INPUT']
        last = m.symbols['UC_STACK']
        assert bytes(m.mem[first:last]) == m.image[first-0x100:last-0x100], 'FCBs/context initialized on /VER'
    else:
        assert not any(fn in (15,16,17,19,20,21,22,23) for fn,_ in m.events)
    m.intact()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    parser.add_argument('--z80pack',type=Path,default=Path.home()/'projects/git/z80pack')
    parser.add_argument('--cc',default='cc')
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='bettercpm-codec-versions-') as temp:
        work=Path(temp)
        (work/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h','simport.h'):
            shutil.copy2(args.z80pack/'z80sim/srcsim'/name,work/name)
        (work/'shim.c').write_text(SHIM)
        core=args.z80pack/'z80core'
        subprocess.run([args.cc,'-shared','-fPIC','-O2',f'-I{work}',f'-I{core}',
                        str(work/'shim.c'),str(core/'simglb.c'),
                        *map(str,sorted(core.glob('simz80*.c'))),'-o',str(work/'core.so')],check=True)
        lib=C.CDLL(str(work/'core.so'))
        total=0
        for command in DESCRIPTIONS:
            builder=importlib.import_module('build_'+command.lower())
            image=builder.build(args.assembler,work)
            assert builder.build(args.assembler,work/'repeat') == image
            m=VersionCommand(lib,image,(work/(command.lower()+'.lst')).read_text(errors='replace'))
            for tail in ('/VER',' /ver  ','/VeR','\t/VeR\t',' '*123+'/VER','/VER'+' '*123,
                         '\t'*123+'/ver'):
                check(m,tail,version_text(command))
            for tail in ('/VER FILE.BIN','FILE.BIN /VER','/VER /VER','/VER /HELP',
                         '/HELP /VER','/VER \x0f','/VER B:','/VER\tX','X\t/ver',
                         '/VER'+' '*122+'X','X'+' '*122+'/VER'):
                check(m,tail,'Invalid /VER usage.\r\n')
            for tail in ('/VERIFY','/VERBOSE','/VERX','/VER=X','X/VER','/VER/','/VE',
                         '/VER.X','\x0fVER'):
                check(m,tail,usage_text(command),False)
            screen = help_text(command)
            lines = screen.splitlines()
            assert len(lines) <= 23 and max(map(len, lines)) <= 79
            assert all(32 <= ord(c) <= 126 or c in '\r\n' for c in screen)
            for tail in ('/HELP',' /help  ','/HeLp','\t/HeLp\t',
                         ' '*122+'/HELP','/HELP'+' '*122,'\t'*122+'/help'):
                check(m,tail,screen)
            for tail in ('/HELP FILE.BIN','FILE.BIN /HELP','/HELP /HELP',
                         '/HELP B:','B: /HELP','/HELP /UNKNOWN','/HELP \x0f',
                         '/HELP\tX','X\t/help','/HELP'+' '*121+'X',
                         'X'+' '*121+'/HELP'):
                check(m,tail,'Invalid /HELP usage.\r\n')
            for tail in ('/HELPER','/HELP.X','/HELP=X','X/HELP','/HEL','/HELP/',
                         '\x0fHELP','/HELP\x01','/VERX /HELPX','', '   ', '\t'):
                check(m,tail,usage_text(command),False)
            total+=m.cases
        # Build identity is metadata-owned, not a hard-coded width.
        modified=dict(identities());modified['SQ']=('2.3',1001)
        with patch('codec_version.identities',return_value=modified):
            builder=importlib.import_module('build_sq')
            image=builder.build(args.assembler,work/'large')
            m=VersionCommand(lib,image,(work/'large/sq.lst').read_text(errors='replace'))
            check(m,'/VER',version_text('SQ'))
            assert 'SQ 2.3 (Build 1001)' in m.console
            check(m,'/HELP',help_text('SQ'))
            assert 'SQ 2.3 (Build 1001)' in m.console
            total+=m.cases
        print(f'PASS: {total} full-Z80 version/help/parser cases across six commands;')
        print('console-only query paths, bounded tails, unchanged files/FCBs/context, ABI and deterministic metadata expansion checked.')


if __name__=='__main__':
    main()
