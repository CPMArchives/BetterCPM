#!/usr/bin/env python3
"""Prepare/resume isolated Model 4 runtime checks for audit blockers 001/002.

Preparation uses current common/Model 4 build products. Resume verifies frozen
packet inputs and needs no rebuild. A LaunchServices failure is never a pass.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from add_cpm_file_to_dmk import extract_raw, add_file, FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE, DIRECTORY_ENTRIES
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_montezuma_extended_790k import build
from build_rsx_module import make_module
from build_source_disk import install_files, extract_files
from build_system_package import compose
from run_trs80_command import DEFAULT_EMULATOR, key_args
from startup_record import build as startup
from system_layout import LAYOUT
from trs80gp_launch import run, require_launch_services, LaunchServicesUnavailable

ROOT = Path(__file__).resolve().parents[1]
PR_COMMIT = 'b69664b8dae31b64b5dae86f58a80660f4037b5f'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def screen(path):
    data = path.read_bytes()[:1920]
    return '\n'.join(bytes(v & 127 for v in data[i:i + 80]).decode('ascii').rstrip()
                     for i in range(0, 1920, 80))


def prepare(out, emulator, assembler):
    out.mkdir(parents=True, exist_ok=False)
    baseline = ROOT / 'build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk'
    source = extract_raw(baseline.read_bytes())
    bdos = (ROOT / 'build/bdos/bdos.bin').read_bytes()
    at = 1024 + LAYOUT['BDOS'] - LAYOUT['SYSTEM']
    assert source[at:at + len(bdos)] == bdos, 'boot image contains stale BDOS'
    # Bind the production artifacts to the reviewed correction receipts.
    receipts = ROOT / 'docs/engineering/audit-blockers-20261103'
    artifacts = [('BDOS', ROOT / 'build/bdos/bdos.bin'),
                 ('SYSBUILD', ROOT / 'build/utilities/SYSBUILD.COM'),
                 ('RLMBUILD', ROOT / 'build/utilities/RLMBUILD.COM')]
    for name, path in artifacts:
        receipt = json.loads((receipts / (name + '-acceptance.json')).read_text())
        assert sha(path) == receipt['artifact']['sha256'], 'artifact differs from PR: ' + name
    source[128:384] = startup('', system_base=LAYOUT['SYSTEM'])

    def put(name, data):
        directory = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
        stem, _, ext = name.partition('.')
        fcbname = (stem.ljust(8) + ext.ljust(3)).encode('ascii')
        for index in range(DIRECTORY_ENTRIES):
            pos = directory + index * 32
            if source[pos] == 0 and bytes(v & 127 for v in source[pos + 1:pos + 12]) == fcbname:
                source[pos] = 0xE5
        add_file(source, name, data)

    # One valid Open establishes a real context before each invalid request.
    code = [' ORG 100H']
    for function in (15, 16, 17, 19, 20, 21, 22, 23, 30, 33, 34, 35, 40):
        code += [' LD HL,INITIAL', ' LD DE,FCB', ' LD BC,36', ' LDIR',
                 ' XOR A', ' LD (FCB),A', ' LD DE,FCB', ' LD C,15',
                 ' CALL 5', ' CP 255', ' JP Z,FAIL',
                 ' LD HL,INITIAL', ' LD DE,FCB', ' LD BC,36', ' LDIR',
                 f' LD C,{function}', ' LD DE,FCB', ' CALL 5',
                 ' CP 255', ' JP NZ,FAIL']
    code += [' LD DE,OK', ' JR PRINT', 'FAIL: LD DE,BAD', 'PRINT: LD C,9',
             ' CALL 5', ' JP 0', "OK: DB 'AUD001 PASS: 13 invalid-drive calls rejected',13,10,'$'",
             "BAD: DB 'AUD001 FAIL: invalid-drive call or fixture failed',13,10,'$'",
             # Explicit zero metadata: this assembler fills DS with FF, which
             # would accidentally request clean Close and huge random records.
             "INITIAL: DB 5,'TARGET  DAT'", " DB 0,0,0,0,0,'RENAMED DAT'",
             ' DB 0,0,0,0,0,0,0,0',
             'FCB: DS 36', ' END']
    text = '\n'.join(code) + '\n'
    (out / 'drive5.mac').write_text(text)
    probe = assemble(assembler, text, out / 'DRIVE5.COM', out / 'drive5.lst', 0x100)
    gate = """ ORG 100H
 LD HL,(6)
 LD DE,8001H
 OR A
 SBC HL,DE
 LD DE,BAD
 JR NZ,PRINT
 LD DE,OK
PRINT: LD C,9
 CALL 5
 JP 0
OK: DB 'GATE8001 PASS',13,10,'$'
BAD: DB 'GATE8001 FAIL',13,10,'$'
 END
"""
    (out / 'gate.mac').write_text(gate)
    gateway = assemble(assembler, gate, out / 'GATE.COM', out / 'gate.lst', 0x100)
    hello = (ROOT / 'build/rsx/hello.bin').read_bytes()
    alternate = (ROOT / 'build/rsx/hello-alt.bin').read_bytes()
    bigmem = make_module(name='BIGMEM', version=(0, 1), services=[198], linked_base=0x8000,
                         code=hello, relocations=relocation_offsets(hello, alternate, 0x101),
                         allocation=0x5100)
    for name, data in [('DRIVE5.COM', probe), ('GATE.COM', gateway),
                       ('TARGET.DAT', b'INVALID DRIVE MUST PRESERVE THIS FILE\r\n'.ljust(128, b'\x1A')),
                       ('BIGMEM.RSX', bigmem),
                       ('SYSBUILD.COM', (ROOT / 'build/utilities/SYSBUILD.COM').read_bytes()),
                       ('RLMBUILD.COM', (ROOT / 'build/utilities/RLMBUILD.COM').read_bytes())]:
        put(name, data)
    boot = build(source)
    package, parts = compose()
    parts.update({'CCPBASE.BIN': (ROOT / 'build/ccp/ccp.bin').read_bytes(),
                  'CCPALT.BIN': (ROOT / 'build/ccp/ccp-alt.bin').read_bytes(),
                  'CCPCHK.BIN': (ROOT / 'build/ccp/ccp-check.bin').read_bytes()})
    data_disk = build(install_files([(0, name, data) for name, data in parts.items()]))
    for name, data in [('CCP.RLM', parts['CCP.RLM']), ('SYSTEM.SYS', package)]:
        (out / ('expected-' + name)).write_bytes(data.ljust((len(data) + 127) // 128 * 128, b'\0'))
    cases = {
        'invalid-drive': [('DRIVE5', 'AUD001 PASS: 13 invalid-drive calls rejected', 'A0>')],
        'low-tpa': [('RSX LOAD BIGMEM', 'BIGMEM', 'A0>'),
                    ('GATE', 'GATE8001 PASS', 'A0>'),
                    ('SYSBUILD', 'SYSBUILD: insufficient active TPA.', 'A0>'),
                    ('RLMBUILD', 'RLMBUILD: insufficient active TPA.', 'A0>'),
                    ('SYSBUILD /VER', 'SYSBUILD 1.0', 'A0>'),
                    ('RLMBUILD /HELP', 'Display utility identification.', 'A0>'),
                    ('RSX LIST', 'BIGMEM', 'A0>'), ('GATE', 'GATE8001 PASS', 'A0>')],
        'normal-tpa': [('B:', 'B0>', 'B0>'),
                       ('A:RLMBUILD', 'CCP.RLM created and verified.', 'B0>'),
                       ('A:SYSBUILD', 'SYSTEM.SYS created and verified', 'B0>')],
    }
    for name in cases:
        work = out / name
        work.mkdir()
        (work / 'a-before.dmk').write_bytes(boot)
        (work / 'b-before.dmk').write_bytes(data_disk)
    shutil.copy2(__file__, out / 'prepared-runner.py')
    inputs = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()}
    manifest = {'status': 'PREPARED; Model 4 not executed', 'reviewed_pr_commit': PR_COMMIT,
                'emulator': str(emulator.resolve()), 'emulator_sha256': sha(emulator),
                'source_boot_sha256': sha(baseline), 'artifacts': {n: sha(p) for n, p in artifacts},
                'runner_sha256': sha(Path(__file__)),
                'helpers': {name: sha(ROOT / 'tools' / name) for name in (
                    'trs80gp_launch.py', 'run_trs80_command.py',
                    'add_cpm_file_to_dmk.py', 'build_source_disk.py',
                    'build_montezuma_extended_790k.py')},
                'cases': cases, 'inputs': inputs}
    (out / 'packet.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Prepared private Model 4 packet:', out)


def execute(out, emulator):
    (out / 'result.json').unlink(missing_ok=True)
    (out / 'launch-blocked.json').unlink(missing_ok=True)
    manifest = json.loads((out / 'packet.json').read_text())
    assert sha(Path(__file__)) == manifest['runner_sha256'], 'runner changed; prepare a new packet'
    for name, expected in manifest['helpers'].items():
        assert sha(ROOT / 'tools' / name) == expected, 'helper changed: ' + name
    assert sha(emulator) == manifest['emulator_sha256'], 'emulator changed; prepare a new packet'
    for relative, expected in manifest['inputs'].items():
        assert sha(out / relative) == expected, 'prepared input changed: ' + relative
    require_launch_services()
    results = []
    for name, commands in manifest['cases'].items():
        work = out / name
        (work / 'result.json').unlink(missing_ok=True)
        # Repeated runs always start from the frozen private before-images.
        for drive in ('a', 'b'):
            shutil.copy2(work / (drive + '-before.dmk'), work / (drive + '.dmk'))
        for old in work.glob('trs80-text-*.bin'):
            old.unlink()
        invocation = [str(emulator), '-m4', '-batch', '-turbo', '-ktx',
                      '-d0', str(work / 'a.dmk'), '-d1', str(work / 'b.dmk'),
                      '-itime', '20000', '-id', '6000', '-it']
        for command, expected, prompt in commands:
            invocation += key_args(command + '\r', delay=25)
            invocation += ['-iw', expected, '-id', '6000', '-it']
        invocation += ['-ix']
        (work / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
        print('Running Model 4:', name, flush=True)
        run(invocation, cwd=work, timeout=180, check=True)
        captures = sorted(work.glob('trs80-text-*.bin'), key=lambda p: int(p.stem.rsplit('-', 1)[1]))
        assert len(captures) == len(commands) + 1, (name, 'missing screen captures')
        for index, (command, expected, prompt) in enumerate(commands, 1):
            text = screen(captures[index])
            (work / f'screen-{index}.txt').write_text(text + '\n')
            assert expected in text and text.rstrip().rstrip('_').rstrip().endswith(prompt), (name, command, text)
            assert 'AUD001 FAIL' not in text and 'GATE8001 FAIL' not in text, text
        assert extract_raw((work / 'a.dmk').read_bytes()) == extract_raw((work / 'a-before.dmk').read_bytes()), 'A: changed: ' + name
        after = extract_raw((work / 'b.dmk').read_bytes())
        if name == 'normal-tpa':
            files = extract_files(after)
            before = extract_files(extract_raw((work / 'b-before.dmk').read_bytes()))
            for product in ('CCP.RLM', 'SYSTEM.SYS'):
                assert files[0, product] == (out / ('expected-' + product)).read_bytes(), product
            for key, data in before.items():
                if key != (0, 'CCP.RLM'):
                    assert files[key] == data, 'input changed: ' + str(key)
        else:
            assert after == extract_raw((work / 'b-before.dmk').read_bytes()), 'B: changed: ' + name
        results.append({'case': name, 'status': 'PASS', 'commands': [c[0] for c in commands],
                        'a_after_sha256': sha(work / 'a.dmk'), 'b_after_sha256': sha(work / 'b.dmk')})
        (work / 'result.json').write_text(json.dumps(results[-1], indent=2) + '\n')
    (out / 'result.json').write_text(json.dumps({'status': 'PASS', 'cases': results,
        'reviewed_pr_commit': manifest['reviewed_pr_commit'], 'artifacts': manifest['artifacts'],
        'emulator_sha256': sha(emulator), 'scope': 'targeted Model 4 audit-blocker runtime checks; not full release certification'}, indent=2) + '\n')
    print('PASS: Model 4 invalid-drive rejection, reduced TPA, and both successful builders')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--emulator', type=Path, default=DEFAULT_EMULATOR)
    p.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    p.add_argument('--prepare-only', action='store_true')
    p.add_argument('--resume', action='store_true')
    a = p.parse_args()
    out = a.output.resolve()
    if not a.resume:
        prepare(out, a.emulator, a.assembler)
    if not a.prepare_only:
        try:
            execute(out, a.emulator)
        except LaunchServicesUnavailable as error:
            (out / 'launch-blocked.json').write_text(json.dumps({'status': 'NOT RUN', 'reason': str(error)}, indent=2) + '\n')
            raise SystemExit(str(error))


if __name__ == '__main__':
    main()
