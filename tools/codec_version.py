"""Prepare compression-command identification and help from the common contracts."""
from pathlib import Path

from utility_versions import identities
from component_identity import identification, title
from component_development import select as select_display
from contextvars import ContextVar
from functools import wraps
import json
import subprocess
from component_inputs import capture, digest

DISPLAY = ContextVar('codec_display', default=None)


def development(command):
    selected = DISPLAY.get()
    if selected is not None and selected[0] == command:
        return selected[1]['development']
    return select_display('utility:'+command, Path.home()/'bin/z80asm', root=ROOT)['development']


def recorded_build(command):
    """Share input/artifact binding without duplicating six assembler drivers."""
    def decorate(build):
        @wraps(build)
        def wrapped(assembler, destination, *, identity_state='auto', target='z80pack'):
            assembler = Path(assembler).resolve()
            destination = Path(destination)
            destination.mkdir(parents=True, exist_ok=True)
            report_path = destination/(command+'-build-report.json')
            report_path.unlink(missing_ok=True)
            before = capture('utility:'+command, assembler, root=ROOT, target=target)
            display = select_display('utility:'+command, assembler, root=ROOT, target=target, mode=identity_state)
            token = DISPLAY.set((command, display))
            try:
                image = build(assembler, destination)
                after = capture('utility:'+command, assembler, root=ROOT, target=target)
                if before != after or display != select_display('utility:'+command, assembler, root=ROOT, target=target, mode=identity_state):
                    raise RuntimeError(command+' inputs/display changed during assembly')
                if (destination/(command+'.COM')).read_bytes() != image:
                    raise RuntimeError(command+' output changed before report generation')
                result = subprocess.run(['git','-C',str(ROOT),'rev-parse','HEAD'], capture_output=True, text=True)
                report = {'schema':1, 'component':'utility:'+command,
                    'identity':before['assigned_identity'], 'input_record':before,
                    'artifact':{'name':command+'.COM','bytes':len(image),'sha256':digest(image)},
                    'display_selection':display,
                    'status':'build record; execution qualification not asserted',
                    'provenance':{'repository_commit':result.stdout.strip() if result.returncode==0 else None}}
                report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
                return image
            finally:
                DISPLAY.reset(token)
        return wrapped
    return decorate

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
    return identification(command, version, build, DESCRIPTIONS[command], development=development(command))


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
    return (title(command, version, build, development=development(command)) + '\r\n  - - -\r\n'
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
