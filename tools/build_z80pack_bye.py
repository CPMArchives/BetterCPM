#!/usr/bin/env python3
"""Build the cpmsim-only BYE command with common utility query conventions."""
import argparse
from pathlib import Path
from build_ccp import assemble
from utility_versions import identities

ROOT = Path(__file__).resolve().parents[1]


def title():
    version, build = identities()['BYE']
    return f'BYE {version} (Build {build:03d})'


def version_text():
    return (title() + '\r\n  - - -\r\n | BetterCP/M Utilities\r\n'
            ' | cpmsim Emulator Exit\r\n')


def help_text():
    return (title() + '\r\n  - - -\r\n | Exit the cpmsim emulator\r\n |\r\n'
            ' |   Usage: BYE [options]\r\n\r\n'
            '   Options:\r\n'
            '     /Y          Exit without confirmation.\r\n\r\n'
            '     /HELP       Display this help.\r\n'
            '     /VER        Display utility identification.\r\n')


def build(assembler=Path.home() / 'bin/z80asm', output=None):
    output = Path(output or ROOT / 'build/z80pack-tools')
    output.mkdir(parents=True, exist_ok=True)
    source = (ROOT / 'src/platform/z80pack/bye.mac').read_text()
    text = []
    for label, screen in [('VERTEXT', version_text()), ('HELPTEXT', help_text())]:
        text.append(label + ':')
        text.extend(f"        DB '{line}',13,10" for line in screen.splitlines())
        text.append("        DB '$'")
    query = (ROOT / 'src/utilities/common/version.inc').read_text()
    query = query[query.index('\nUV_QUERY:') + 1:]
    help_query = query.replace('UV_', 'UH_').replace('LD C,4', 'LD C,5')
    help_query = help_query.replace("'/ver'", "'/help'")
    source = source.replace('; @bye-text@', '\n'.join(text))
    source = source.replace('; @bye-queries@', help_query + '\n' + query)
    return assemble(assembler, source, output / 'BYE.COM', output / 'bye.lst', 0x100)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    p.add_argument('--output', type=Path, default=ROOT / 'build/z80pack-tools')
    args = p.parse_args()
    data = build(args.assembler, args.output)
    print(f'{args.output / "BYE.COM"}: {len(data)} bytes')
