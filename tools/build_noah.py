#!/usr/bin/env python3
"""Build NOAH's LBR reader/test/extraction increment (not yet a release-disk utility)."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
from utility_versions import identities

ROOT = Path(__file__).resolve().parents[1]


def version_text():
    version, counter = identities()['NOAH']
    return (f"NOAH {version} (Build {counter:03d})\r\n  - - -\r\n"
            " | BetterCP/M Utilities\r\n | Noah's ARK - development build\r\n")


def build(assembler, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    texts = {
        'NH_VERSION': version_text(),
        'NH_USAGE': 'NOAH: Invalid or unsupported usage.\r\nUsage: NOAH [/LIST|/TEST] [drive:]file\r\n       NOAH /EXTRACT [drive:]file [destination-drive:]\r\nUse NOAH /HELP for current scope.\r\n',
        'NH_HELP': 'NOAH LBR reader development build\r\nUsage: NOAH [/LIST|/TEST] [drive:]file\r\n       NOAH /EXTRACT [drive:]file [destination-drive:]\r\nAliases: /T /X. /VER and /HELP ignore other arguments; /HELP takes precedence.\r\nOne exact archive, current user only; all active members.\r\nExisting outputs are reported and skipped; no overwrites yet.\r\nARK, full selectors, overwrite UI, updates and overlays are pending.\r\nLIST does not test contents. TEST/EXTRACT audit structure and CRCs.\r\n',
    }
    emitted = []
    for label, text in texts.items():
        emitted.append(label + ':')
        for line in text.splitlines():
            # Byte lists also handle apostrophes and dollar-sign filenames.
            raw = line.encode('ascii')
            for offset in range(0, len(raw), 16):
                emitted.append('        DB ' + ','.join(str(b) for b in raw[offset:offset + 16]))
            emitted.append('        DB 13,10')
        emitted.append('        DB 36')
    with tempfile.TemporaryDirectory(prefix='bettercpm-noah-') as temp:
        work = Path(temp)
        for name in ('archive.inc', 'lbr.mac', 'lbraudit.inc', 'lbraudit.mac', 'cpmfile.inc', 'cpmfile.mac'):
            shutil.copy2(ROOT / 'src/archive' / name, work / name)
        shutil.copy2(ROOT / 'src/utilities/common/noahextract.inc', work / 'noahextract.inc')
        source = (ROOT / 'src/utilities/noah.mac').read_text()
        query = (ROOT / 'src/utilities/common/version.inc').read_text()
        query = query[query.index('\nUV_QUERY:') + 1:]
        help_query = query.replace('UV_', 'UH_').replace('LD C,4', 'LD C,5')
        help_query = help_query.replace("'/ver'", "'/help'")
        source = source.replace('; @noah-version-query@', query + '\n' + help_query)
        (work / 'command.mac').write_text(source.replace('; @noah-text@', '\n'.join(emitted)))
        subprocess.run([str(assembler), '-e32', '-sn', '-fb', '-onoah.bin', '-lnoah.lst', 'command.mac'], cwd=work, check=True)
        image = (work / 'noah.bin').read_bytes()
        if image[:0x100] == bytes(0x100):
            image = image[0x100:]
        if not image or image[0] != 0xC3 or len(image) > 0xCF00:
            raise ValueError('invalid/oversized NOAH.COM')
        (destination / 'NOAH.COM').write_bytes(image)
        shutil.copy2(work / 'noah.lst', destination / 'noah.lst')
    return image


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    p.add_argument('--output-dir', type=Path, default=ROOT / 'build/utilities')
    a = p.parse_args()
    image = build(a.assembler, a.output_dir)
    print(f'NOAH.COM foundation: {len(image)} bytes; SHA-256 {hashlib.sha256(image).hexdigest()}')


if __name__ == '__main__':
    main()
