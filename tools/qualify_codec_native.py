#!/usr/bin/env python3
"""Build codec commands with CP/M ZSM4/LINK; compare pinned qualified bytes."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from codec_version import prepare_version

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = ('SQ', 'USQ', 'CR', 'UNCR', 'LZH', 'UNLZH')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, **kw):
    return subprocess.run(list(map(str, args)), check=True, capture_output=True, **kw)


def native_text(text):
    text = re.sub(r'(?m)^[ \t]*;[^\n]*\n', '', text)
    if re.search(r'(?m)^\s*ORG\s+100H', text):
        text = re.sub(r'(?m)^\s*ORG\s+100H', '        CSEG\n        .PHASE 100H', text, count=1)
        text = re.sub(r'(?m)^        END$', '        .DEPHASE\n        END', text)
    # z80asm emits FF for DS; make that storage explicit to preserve every byte.
    text = re.sub(r'(?m)^(\s*(?:\w+:)?)[ \t]+DS[ \t]+([^;\n]+)(?:;[^\n]*)?$',
                  r'\1\n        REPT \2\n        DB 0FFH\n        ENDM', text)
    text = text.replace("DB '',13,10", 'DB 13,10')
    # Keep strings intact; remove comments and redundant whitespace to fit
    # native macro storage in the CP/M transient program area.
    lines = []
    for line in text.splitlines():
        parts = re.findall(r"'[^']*'|\"[^\"]*\"|;.*$|[^'\";]+", line)
        compact = ''.join(part if part.startswith(("'", '\"')) else
                          re.sub(r'[ \t]+', ' ', part)
                          for part in parts if not part.startswith(';'))
        if compact.strip():
            lines.append(compact.rstrip())
    return ('\r\n'.join(lines).replace('codecfile.mac', 'cfio.mac') + '\r\n').encode('ascii') + b'\x1a'


def verify_native(raw, expected, log):
    """Reject code-size differences; exclude only the CP/M final record padding."""
    sizes = re.findall(rb'CODE SIZE +([0-9A-F]+)', log)
    if sizes != [f'{len(expected):04X}'.encode()]:
        raise ValueError('LINK code size differs from qualified executable')
    if len(raw) != (len(expected)+127)//128*128:
        raise ValueError('native file does not have the expected CP/M record length')
    if raw[:len(expected)] != expected:
        raise ValueError('native executable bytes differ from qualified executable')
    if any(x != 0x1A for x in raw[len(expected):]):
        raise ValueError('unexpected native final-record padding')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    base = Path.home() / 'projects/git'
    p.add_argument('--cpmsim', type=Path, default=base/'z80pack/cpmsim/cpmsim')
    p.add_argument('--tools', type=Path, default=base/'cpm-compatibility/suite/build-tools')
    p.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--commands', nargs='+', choices=COMMANDS, default=COMMANDS)
    a = p.parse_args()
    out = a.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    library = a.cpmsim.parent/'disks/library'
    env = dict(os.environ); env['PATH'] = str(a.cpmsim.parent/'srctools')+os.pathsep+env['PATH']
    qualification = ROOT/'docs/engineering/Compression-1.0-Qualification.json'
    qualified = json.loads(qualification.read_text())['our_commands']
    inputs = [a.cpmsim, a.tools/'ZSM4.COM', a.tools/'LINK.COM', a.assembler,
              library/'cpm22-62khd.dsk', library/'cpm22-1.dsk', qualification]
    report = {'status': 'IN_PROGRESS', 'date': '2026-10-24',
              'scope': 'Native ZSM4 4.7 / LINK 1.3 on stock 62K CP/M 2.2 under the recorded local cpmsim; prepared macro sources',
              'baseline': run(['git','rev-parse','HEAD'],cwd=ROOT).stdout.decode().strip(),
              'runner_sha256': digest(Path(__file__)), 'environment_sha256': {str(x): digest(x) for x in inputs}, 'commands': {}}
    def save():
        (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    save()
    shutil.copy2(qualification, out/'qualified-input.json')
    for command in a.commands:
        work = out/command; work.mkdir(); disks = work/'disks'; disks.mkdir()
        cross = importlib.import_module('build_'+command.lower()).build(a.assembler, work/'cross')
        assert hashlib.sha256(cross).hexdigest() == qualified[command]['sha256'], 'qualified artifact changed'
        assert len(cross) == qualified[command]['bytes']
        sources = work/'sources'; sources.mkdir(); prepare_version(command, sources)
        source_map = {n: ROOT/'src/codec'/n for n in ('codec.inc','codec.mac',command.lower()+'.inc',command.lower()+'.mac')}
        source_map['cfio.mac'] = ROOT/'src/utilities/common/codecfile.mac'
        source_map['command.mac'] = ROOT/'src/utilities'/ (command.lower()+'.mac')
        for name, path in source_map.items():
            (sources/name).write_text(path.read_text())
        source_hashes = {str(path.relative_to(ROOT)): digest(path) for path in source_map.values()}
        for name in ('tools/build_'+command.lower()+'.py','tools/codec_version.py','metadata/utility-versions.tsv','src/utilities/common/version.inc','src/utilities/common/codecver.inc'):
            source_hashes[name] = digest(ROOT/name)
        for path in list(sources.iterdir()):
            path.write_bytes(native_text(path.read_text()))
        shutil.copy2(library/'cpm22-62khd.dsk', disks/'drivea.dsk')
        for drive in 'bcd':
            shutil.copy2(library/'cpm22-1.dsk', disks/f'drive{drive}.dsk')
            run(['mkfs.cpm','-f','ibm-3740',disks/f'drive{drive}.dsk'])
        for path in sources.iterdir():
            drive = 'c' if path.name == 'command.mac' else 'b'
            run(['cpmcp','-f','ibm-3740',disks/f'drive{drive}.dsk',path,'0:'+path.name])
        for name in ('ZSM4.COM','LINK.COM'):
            run(['cpmcp','-f','ibm-3740',disks/'drived.dsk',a.tools/name,'0:'+name])
        script = '\n'.join(['set timeout 180',
            f'spawn {{{a.cpmsim}}} -z -d {{{disks}}}', 'expect_before {timeout {exit 124} eof {exit 125}}', 'expect "A>"', 'send -- "B:\\r"', 'expect "B>"',
            'send -- "D:ZSM4 B:COMMAND=C:COMMAND\\r"', 'expect "B>"',
            'send -- [format "%s\\r" {D:LINK COMMAND[A]}]', 'expect "B>"', 'expect_before', 'send "\\034"', 'expect eof'])
        (work/'build.exp').write_text(script+'\n')
        with (work/'build.log').open('wb') as stream:
            result = subprocess.run(['expect',str(work/'build.exp')],cwd=work,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=400)
        log = (work/'build.log').read_bytes()
        if result.returncode or not re.search(rb'Errors: +0\b',log) or b'CODE SIZE' not in log:
            raise RuntimeError(f'{command}: native build failed; see {work}/build.log')
        native = work/'COMMAND.COM'
        run(['cpmcp','-f','ibm-3740',disks/'driveb.dsk','0:COMMAND.COM',native])
        raw = native.read_bytes()
        verify_native(raw, cross, log)
        (work/(command+'.COM')).write_bytes(raw[:len(cross)])
        report['commands'][command] = {'status':'PASS','bytes':len(cross),'sha256':hashlib.sha256(cross).hexdigest(),
            'record_bytes':len(raw),'record_sha256':digest(native),'padding_hex':raw[len(cross):].hex(),
            'source_sha256':source_hashes,'prepared_sha256':{x.name:digest(x) for x in sources.iterdir()},'log_sha256':digest(work/'build.log')}
        save(); print(f'PASS {command}: {len(cross)} byte-identical bytes',flush=True)
    report['status'] = 'PASS'; save()


if __name__ == '__main__':
    main()
