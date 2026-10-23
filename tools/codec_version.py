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


HELP_DETAILS = {
    'SQ': ('Compress one file into historical squeezed format.', 'REPORT.TXT',
           'REPORT.TXT becomes REPORT.TQT. Input is read twice; keep it unchanged.'),
    'USQ': ('Expand one historical squeezed file.', 'REPORT.TQT',
            'The original output name is restored from the squeezed header.'),
    'CR': ('Compress one file into CRUNCH 2.x format.', 'REPORT.TXT',
           'REPORT.TXT becomes REPORT.TZT. Use UNCR to restore it.'),
    'UNCR': ('Expand one CRUNCH 2.x file.', 'REPORT.TZT',
             'CRUNCH 1.x is unsupported. The header supplies the output name.'),
    'LZH': ('Compress one file into CrLZH 2.x format.', 'REPORT.TXT',
            'REPORT.TXT becomes REPORT.TYT. Use UNLZH to restore it.'),
    'UNLZH': ('Expand one CrLZH 1.x or 2.x file.', 'REPORT.TYT',
              'The header supplies the output name. LHA archives are unsupported.'),
}


def usage_text(command):
    return (f'Usage: {command} [drive:]file [destination-drive:]\r\n'
            f'Use {command} /HELP for help.\r\n')


def help_text(command):
    purpose, example, detail = HELP_DETAILS[command]
    return (version_text(command) + '\r\n' + purpose + '\r\n\r\n'
            + f'Usage: {command} [drive:]file [destination-drive:]\r\n'
            + f'       {command} /HELP\r\n       {command} /VER\r\n\r\n'
            + '  /HELP   Display this help.\r\n'
            + '  /VER    Display utility identification.\r\n\r\n'
            + f'Example: {command} A:{example} B:\r\n\r\n'
            + 'Output defaults to the logged drive and current user area.\r\n'
            + 'Existing output files are refused; the source is retained.\r\n'
            + 'Wildcards are not supported.\r\n' + detail + '\r\n')


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
    # The help recognizer has the same exact-token/standalone contract, with
    # a five-byte keyword. Keep the version recognizer first for mixed queries.
    # Fail visibly if the shared query changes shape: the fifth keyword byte
    # needs a fifth advance after matching, as well as a longer comparison.
    for fragment in ('LD C,4', 'SUB 4', '        JR Z,UV_PRINT', "'/ver'"):
        if query.count(fragment) != 1:
            raise ValueError('shared version query changed: ' + fragment)
    help_query = query.replace('UV_', 'UH_').replace('LD C,4', 'LD C,5')
    help_query = help_query.replace('SUB 4', 'SUB 5')
    help_query = help_query.replace('        JR Z,UH_PRINT', '        INC HL\n        JR Z,UH_PRINT')
    help_query = help_query.replace("'/ver'", "'/help'").replace('/VER', '/HELP')
    source = source.replace('; @codec-version-query@', query + '\n' + help_query)
    (work / 'codecver.inc').write_text(source)
