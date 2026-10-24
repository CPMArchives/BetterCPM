"""Prepare compression-command identification and help from the common contracts."""
from pathlib import Path

from utility_versions import identities

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTIONS = {
    'SQ': 'Squeeze File Compression',
    'USQ': 'Squeezed File Expansion',
    'CR': 'CRUNCH File Compression',
    'UNCR': 'CRUNCH File Expansion',
    'LZH': 'CrLZH File Compression',
    'UNLZH': 'CrLZH File Expansion',
}


def version_text(command):
    version, build = identities()[command]
    return (f'{command} {version} (Build {build:03d})\r\n  - - -\r\n'
            f' | BetterCP/M Utilities\r\n | {DESCRIPTIONS[command]}\r\n')


HELP_PURPOSES = {
    'SQ': 'Squeeze compression',
    'USQ': 'Squeeze expansion',
    'CR': 'CRUNCH compression',
    'UNCR': 'CRUNCH expansion',
    'LZH': 'CrLZH compression',
    'UNLZH': 'CrLZH expansion',
}


def usage_text(command):
    return (f'Usage: {command} [drive:]file [destination-drive:]\r\n'
            f'Use {command} /HELP for help.\r\n')


def help_text(command):
    version, build = identities()[command]
    return (f'{command} {version} (Build {build:03d})\r\n  - - -\r\n'
            f' | {HELP_PURPOSES[command]}\r\n |\r\n'
            f' |   Usage: {command} [drive:]file [destination-drive:]\r\n\r\n'
            '   Options:\r\n'
            '     /HELP       Display this help.\r\n'
            '     /VER        Display utility identification.\r\n')


def prepare_version(command, work):
    common = ROOT / 'src/utilities/common'
    query = (common / 'version.inc').read_text()
    query = query[query.index('\nUV_QUERY:') + 1:]
    # Short lines avoid assembler macro-line truncation. No environment values
    # or timestamps are embedded; each build has at least three display digits.
    lines = []
    for label, text in [('UC_VERSION_TEXT', version_text(command)),
                        ('UC_HELP_TEXT', help_text(command))]:
        lines.append(label + ':')
        for part in text.splitlines():
            lines.append(f"        DB '{part}',13,10")
        lines.append("        DB '$'")
    source = (common / 'codecver.inc').read_text()
    source = source.replace('; @codec-version-text@', '\n'.join(lines))
    # Exact query tokens anywhere in the tail ignore all other arguments.
    # Help is dispatched first when both /HELP and /VER are present.
    help_query = query.replace('UV_', 'UH_').replace('LD C,4', 'LD C,5')
    help_query = help_query.replace("'/ver'", "'/help'")
    source = source.replace('; @codec-version-query@', query + '\n' + help_query)
    (work / 'codecver.inc').write_text(source)
