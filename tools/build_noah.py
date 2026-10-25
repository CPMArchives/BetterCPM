#!/usr/bin/env python3
"""Build NOAH's LBR reader, extraction and staged-write increment (not yet a release-disk utility)."""
import argparse
import hashlib
import re
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


def build_flat(assembler, destination, source_only=False):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    texts = {
        'NH_VERSION': version_text(),
        'NH_USAGE': 'NOAH: Invalid or unsupported usage.\r\nUsage: NOAH [/LIST|/TEST] archives [member]\r\n       NOAH /EXTRACT archives [destination:pattern]\r\nUse NOAH /HELP for current scope.\r\n',
        'NH_HELP': 'NOAH LBR development build\r\nUsage: NOAH [/LIST|/TEST] archives [member]\r\n       NOAH /EXTRACT archives [destination:pattern]\r\nAliases: /T /X. /VER and /HELP ignore other arguments; /HELP takes precedence.\r\nShared archive filespecs: wildcards, DU sets and attribute predicates.\r\nArchive order: drive, user, filename; frozen limit 512 archives.\r\nMember names are 8.3 patterns; README means exact extensionless README.\r\nExtraction destination is one DU, default caller DU.\r\nOverwrite: Y/N/All/Cancel, default No; ESC or Ctrl-C cancels.\r\n/Y approves ordinary replacement; /R and /SYS enable separate protection prompts.\r\n/Y always skips protected outputs; extraction never replaces input archives.\r\nLBR writes: /ADD archive sources; /REMOVE archives member; /COMPACT archives.\r\n/CAPACITY=n on ADD/COMPACT; /FORMAT=LBR creates an unknown extension.\r\nNormal updates retain deleted data; rebuild/COMPACT discards recovery data.\r\nCodecs: /SQ sources [destination:] and /CR sources [destination:].\r\n/EXPAND sources [destination:] decodes one recognized layer or copies ordinary files.\r\n/ADD /SQ or /CR stores compressed members; /X /EXPAND expands one inner layer.\r\nMatching NOAH.OVL required except VER/HELP; invocation DU then A0.\r\nARK, /LZ, /Q and recovery UI are pending.\r\nLIST does not test contents. TEST/EXTRACT audit structure and CRCs.\r\n',
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
        for name in ('archive.inc', 'lbr.mac', 'lbraudit.inc', 'lbraudit.mac', 'cpmfile.inc', 'cpmfile.mac', 'lbrwrite.inc', 'lbrwrite.mac', 'lbrwrite-render.inc'):
            shutil.copy2(ROOT / 'src/archive' / name, work / name)
        for name in ('noahextract.inc', 'noahselect.inc', 'noahinput.inc', 'noahpublish.inc', 'noahwrite.inc', 'noahwrite-parse.inc', 'noahcodec.inc', 'noahcodec-add.inc'):
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
        if not source_only:
            try:
                subprocess.run([str(assembler), '-e32', '-sn', '-fb', '-onoah.bin', '-lnoah.lst', 'command.mac'], cwd=work, check=True)
            except subprocess.CalledProcessError:
                shutil.copy2(work / 'noah.lst', destination / 'noah.lst')
                raise
        # Export a self-contained native source; external tools stay unmodified.
        def expand(text):
            return re.sub(r'(?mi)^\s*INCLUDE\s+(\S+)\s*$',
                          lambda m: expand((work / m[1]).read_text()).rstrip(), text)
        from qualify_codec_native import native_text
        flat = expand((work / 'command.mac').read_text())
        # Expand our bounded straight-line macros before native assembly. Keeping
        # all four library bodies as ZSM4 macros exhausts its symbol workspace.
        macros = {}
        def take_macro(m):
            macros[m[1]] = (m[2].strip().split(','), m[3])
            return ''
        flat = re.sub(r'(?ms)^([A-Z_][A-Z_0-9]*) MACRO([^\n]*)\n(.*?)^\s*ENDM[^\n]*$', take_macro, flat)
        def invoke(m):
            params, body = macros[m[1]]
            args = m[2].strip().split(',')
            for param, value in zip(params,args):
                if param:
                    body = re.sub(r'\b'+re.escape(param.strip())+r'\b',value.strip(),body)
            return body.rstrip()
        pattern = r'(?m)^[ \t]*('+ '|'.join(macros) + r')\b([^;\n]*)(?:;[^\n]*)?$'
        for _ in range(4):
            flat, count = re.subn(pattern,invoke,flat)
            if not count: break
        else: raise ValueError('unexpanded NOAH macro')
        if source_only:
            (destination / 'noah-flat.mac').write_text(flat)
            return flat
        from build_dasm import validate_native_identifiers
        validate_native_identifiers(flat)
        (destination / 'noah-flat.mac').write_text(flat)
        native = native_text(flat)
        (destination / 'NOAHNAT.MAC').write_bytes(native)
        image = (work / 'noah.bin').read_bytes()
        if image[:0x100] == bytes(0x100):
            image = image[0x100:]
        if not image or image[0] != 0xC3 or len(image) > 0xCF00:
            raise ValueError('invalid/oversized NOAH.COM')
        (destination / 'NOAH.COM').write_bytes(image)
        shutil.copy2(work / 'noah.lst', destination / 'noah.lst')
    return image


def build(assembler, destination):
    from noah_overlays import production_build
    return production_build(assembler, Path(destination), build_flat)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    p.add_argument('--output-dir', type=Path, default=ROOT / 'build/utilities')
    a = p.parse_args()
    image = build(a.assembler, a.output_dir)
    print(f'NOAH.COM production phases: {len(image)} bytes; SHA-256 {hashlib.sha256(image).hexdigest()}')


if __name__ == '__main__':
    main()
