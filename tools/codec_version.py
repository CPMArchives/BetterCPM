"""Prepare compression-command identities from the shared version contract."""
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


def prepare_version(command, work):
    common = ROOT / 'src/utilities/common'
    query = (common / 'version.inc').read_text()
    query = query[query.index('\nUV_QUERY:') + 1:]
    # Short lines avoid assembler macro-line truncation. No environment values
    # or timestamps are embedded; each build has at least three display digits.
    text = version_text(command)
    lines = ["UC_VERSION_TEXT:"]
    for part in text.splitlines():
        lines.append(f"        DB '{part}',13,10")
    lines.append("        DB '$'")
    source = (common / 'codecver.inc').read_text()
    source = source.replace('; @codec-version-text@', '\n'.join(lines))
    source = source.replace('; @codec-version-query@', query)
    (work / 'codecver.inc').write_text(source)
