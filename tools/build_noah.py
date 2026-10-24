#!/usr/bin/env python3
"""Build NOAH's LBR reader/test/extraction increment (not yet a release-disk utility)."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
from utility_versions import identities
from component_identity import identification

ROOT = Path(__file__).resolve().parents[1]


def version_text():
    version, counter = identities()['NOAH']
    return identification('NOAH',version,counter,'Archive Utility - Development')


def build(assembler, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    texts = {
        'NH_VERSION': version_text(),
        'NH_USAGE': 'NOAH: Invalid or unsupported usage.\r\nUsage: NOAH [/LIST|/TEST] archives [member]\r\n       NOAH /EXTRACT archives [destination:pattern]\r\nUse NOAH /HELP for current scope.\r\n',
        'NH_HELP': 'NOAH LBR reader development build\r\nUsage: NOAH [/LIST|/TEST] archives [member]\r\n       NOAH /EXTRACT archives [destination:pattern]\r\nAliases: /T /X. /VER and /HELP ignore other arguments; /HELP takes precedence.\r\nShared archive filespecs: wildcards, DU sets and attribute predicates.\r\nArchive order: drive, user, filename; frozen limit 512 archives.\r\nMember names are 8.3 patterns; README means exact extensionless README.\r\nExtraction destination is one DU, default caller DU.\r\nOverwrite: Y/N/All/Cancel, default No; ESC or Ctrl-C cancels.\r\n/Y approves ordinary replacement; /R and /SYS enable separate protection prompts.\r\n/Y always skips protected outputs; input archives are never replaced.\r\nARK, codecs, archive updates, /Q and recovery UI are pending.\r\nLIST does not test contents. TEST/EXTRACT audit structure and CRCs.\r\n',
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
        for name in ('noahextract.inc', 'noahselect.inc', 'noahinput.inc', 'noahpublish.inc'):
            shutil.copy2(ROOT / 'src/utilities/common' / name, work / name)
        from shared_ui import controller_source, UI
        binding = (work / 'noahinput.inc').read_text()
        binding = binding.replace('; @choice-modules@', (UI / 'events.inc').read_text() + '\n' + controller_source(text=False, choice=True))
        (work / 'noahinput.inc').write_text(binding)
        common = ROOT / 'src/utilities/common'
        grammar = 'DU_MAP: DS 64\nDU_WORK: DS 12\n'
        grammar += ''.join((common / n).read_text() + '\n' for n in ('duselect.inc', 'filespec.inc', 'operandqual.inc'))
        attrs = (common / 'attrselect.inc').read_text()
        grammar += attrs[:attrs.index('; Destination modification list:')]
        grammar += (common / 'rcpselect.inc').read_text()
        rcp = (ROOT / 'src/cpx/rcp.mac').read_text()
        start = rcp.index('BC_PFCB:')
        grammar += rcp[start:rcp.index('; ================================================================================', start)]
        grammar += 'BC_ALL: DB \'*.*\'\nBC_INPTR: DW 0\nBC_INLEN: DB 0\nBC_FCBPTR: DW 0\n'
        (work / 'noahgrammar.inc').write_text(grammar)
        source = (ROOT / 'src/utilities/noah.mac').read_text()
        query = (ROOT / 'src/utilities/common/version.inc').read_text()
        query = query[query.index('\nUV_QUERY:') + 1:]
        help_query = query.replace('UV_', 'UH_').replace('LD C,4', 'LD C,5')
        help_query = help_query.replace("'/ver'", "'/help'")
        source = source.replace('; @noah-version-query@', query + '\n' + help_query)
        (work / 'command.mac').write_text(source.replace('; @noah-text@', '\n'.join(emitted)))
        try:
            subprocess.run([str(assembler), '-e32', '-sn', '-fb', '-onoah.bin', '-lnoah.lst', 'command.mac'], cwd=work, check=True)
        except subprocess.CalledProcessError:
            shutil.copy2(work / 'noah.lst', destination / 'noah.lst')
            raise
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
