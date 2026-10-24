#!/usr/bin/env python3
"""Build the cpmsim-only BYE command with common utility query conventions."""
import argparse
import json
import subprocess
from pathlib import Path
from build_ccp import assemble
from utility_versions import identities
from component_inputs import capture, classify, digest

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


def build(assembler=Path.home() / 'bin/z80asm', output=None, *, baseline=None):
    output = Path(output or ROOT / 'build/z80pack-tools')
    output.mkdir(parents=True, exist_ok=True)
    assembler = Path(assembler).resolve()
    report_path = output / 'build-report.json'
    # A failed rebuild must never leave an old success receipt beside its output.
    report_path.unlink(missing_ok=True)
    reference = json.loads(Path(baseline).read_text()) if baseline else None
    def inputs():
        try:
            return capture('utility:BYE', assembler, root=ROOT), None
        except (ValueError, OSError, KeyError) as error:
            return None, str(error)
    before, unsupported = inputs()
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
    image = assemble(assembler, source, output / 'BYE.COM', output / 'bye.lst', 0x100)
    after, after_error = inputs()
    if before != after or unsupported != after_error:
        raise RuntimeError('BYE inputs changed during assembly; no build report emitted')
    if (output / 'BYE.COM').read_bytes() != image:
        raise RuntimeError('BYE output changed before build report')
    provenance = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                                capture_output=True, text=True)
    commit = provenance.stdout.strip() if provenance.returncode == 0 else None
    report = {
        'schema': 1, 'component': 'utility:BYE',
        'status': 'build-record; qualification not asserted',
        'identity': dict(zip(('version', 'revision'), identities()['BYE'])),
        'artifact': {'name': 'BYE.COM', 'bytes': len(image), 'sha256': digest(image)},
        'input_record': before,
        'comparison': classify(before, reference) if before else
            {'state': 'unknown', 'reason': unsupported},
        'provenance': {'repository_commit': commit,
                       'source_state': 'selected input hashes; global cleanliness not asserted',
                       'assembler_sha256': digest(assembler.read_bytes())},
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return image


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    p.add_argument('--output', type=Path, default=ROOT / 'build/z80pack-tools')
    p.add_argument('--baseline', type=Path,
                   help='explicit input-record reference; never assigns a revision')
    args = p.parse_args()
    data = build(args.assembler, args.output, baseline=args.baseline)
    print(f'{args.output / "BYE.COM"}: {len(data)} bytes')
