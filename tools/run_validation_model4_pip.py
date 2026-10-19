#!/usr/bin/env python3
"""Native shipped PIP verified disk copy, CRT and unavailable-device admission."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw, add_file, FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE, DIRECTORY_ENTRIES
from build_source_disk import install_files
from build_montezuma_extended_790k import build
from build_ccp import assemble
from run_validation_model4 import audit_files
from run_validation_returning import sha
from run_trs80_command import DEFAULT_EMULATOR, key_args
from test_sysgen_install import screen
from test_model4_copy import files
from trs80gp_launch import run
ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'suite', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--group', choices=('positive', 'lpt', 'ptr'), required=True)
    a = p.parse_args()
    w = a.output.resolve(); w.mkdir(parents=True, exist_ok=False)
    report = json.loads((a.baseline / 'report.json').read_text())
    original = a.baseline / report['image']
    assert report['target'] == 'trs80gp' and sha(original) == report['sha256']
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=a.suite, text=True).strip()
    assert revision == 'a9a878fcd2e36698c7e856654a85847a004fdd20'
    raw = extract_raw(original.read_bytes())
    for i in range(DIRECTORY_ENTRIES):
        at = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE + i * 32
        if raw[at] == 0 and raw[at + 1:at + 12] == b'STARTUP SUB': raw[at] = 0xE5
    commands = ([':VER /BANNER', 'PIP B3:OUT.TXT=A0:SRC.TXT[V]', 'PIP CRT:=SRC.TXT', 'PIP /VER', 'STATE', 'VER', 'FINAL'] if a.group == 'positive'
                else ['CLS', 'PIP LPT:=SRC.TXT' if a.group == 'lpt' else 'PIP B3:BAD.TXT=PTR:'])
    startup = ('\r\n'.join(commands) + '\r\n\x1a').encode()
    add_file(raw, 'STARTUP.SUB', startup)
    (w / 'STARTUP.SUB').write_bytes(startup)
    source = (ROOT / 'tests/fixtures/conformance/returnstate.mac').read_text()
    (w / 'state.asm').write_text(source)
    assembler = Path.home() / 'bin/z80asm'
    state = assemble(assembler, source, w / 'STATE.COM', w / 'state.lst', 0x100)
    add_file(raw, 'STATE.COM', state)
    final_source = " ORG 100H\n LD DE,MSG\n LD C,9\n CALL 5\n RET\nMSG: DB 'NATIVE PIP WORKFLOW COMPLETE',13,10,'$'\n END\n"
    (w / 'FINAL.asm').write_text(final_source)
    final = assemble(assembler, final_source, w / 'FINAL.COM', w / 'FINAL.lst', 0x100)
    add_file(raw, 'FINAL.COM', final)
    payload = b'MODEL FOUR PIP TRANSFER\r\n' + b'V' * 500 + b'\x1a'
    add_file(raw, 'SRC.TXT', payload)
    fixtures = [(0, 'KEEP.TXT', b'NATIVE PIP SENTINEL\r\n\x1a')]
    before_raw = install_files(fixtures)
    before_files = files(before_raw)
    (w / 'b-before.raw').write_bytes(before_raw)
    image = w / 'a.dmk'; image.write_bytes(build(bytes(raw)))
    secondary = w / 'b.dmk'; secondary.write_bytes(build(bytes(before_raw)))
    shutil.copy2(__file__, w / 'executed-runner.py')
    cmd = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx', '-d0', str(image), '-d1', str(secondary), '-itime', '15000']
    if a.group == 'positive':
        cmd += ['-iw', 'MODEL FOUR PIP TRANSFER', '-id', '120', '-it',
                '-iw', 'NATIVE PIP WORKFLOW COMPLETE', '-id', '6000', '-it', '-ix']
    else:
        # PIP intentionally cancels SUBMIT on errors. Wait for the returned
        # blank prompt, not the A0> prefix still present on its command line.
        cmd += ['-iw', 'DEVICE UNAVAILABLE', '-it', '-iw', 'A0> ', '-id', '120']
        cmd += key_args('STATE\r',delay=25) + ['-iw','STATE D=00 U=00 TOP=D501','-it','-iw','A0> ','-id','120']
        cmd += key_args('VER\r',delay=25) + ['-iw','BetterCP/M 0.90','-iw','A0> ','-id','120','-it','-ix']
    (w / 'invocation.json').write_text(json.dumps(cmd, indent=2) + '\n')
    run(cmd, cwd=w, timeout=1800, check=True)
    captures = sorted(w.glob('trs80-text-*.bin'), key=lambda f: int(f.stem.rsplit('-', 1)[1]))
    texts = [screen(f) for f in captures]
    for i, t in enumerate(texts): (w / f'screen-{i}.txt').write_text(t + '\n')
    if a.group == 'positive':
        assert any('MODEL FOUR PIP TRANSFER' in t for t in texts)
        assert 'BetterCP/M PIP 1.0' in texts[-1] and 'NATIVE PIP WORKFLOW COMPLETE' in texts[-1]
    else: assert any('DEVICE UNAVAILABLE' in t for t in texts)
    assert 'STATE D=00 U=00 TOP=D501' in texts[-1]
    assert 'BetterCP/M 0.90' in texts[-1] and texts[-1].rstrip().endswith('A0>')
    after_raw = extract_raw(secondary.read_bytes()); (w / 'b-after.raw').write_bytes(after_raw)
    current = files(after_raw)
    if a.group == 'positive':
        assert set(current) == set(before_files) | {(3, b'OUT     TXT')}
        assert current[3, b'OUT     TXT'][0] == payload.ljust(640, b'\x1a')
    else:
        assert bytes(after_raw) == bytes(before_raw), 'unsupported alias mutated data disk'
    for key, value in before_files.items(): assert current[key] == value
    assert not any(k[1] == b'BAD     TXT' or k[1].endswith(b'$$$') for k in current)
    audit = audit_files(original, image, dict(report, included=[f for f in report['included'] if f['name'] != 'STARTUP.SUB']), w)
    assert extract_raw(image.read_bytes())[:20480] == extract_raw(original.read_bytes())[:20480]
    (w / 'diskdefs').write_text('diskdef native-data\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 0\n os 2.2\nend\n')
    for path in ('b-before.raw', 'b-after.raw'):
        result = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'native-data', '-n', str(w / path)], cwd=w, capture_output=True, check=True)
        (w / (path + '.fsck.txt')).write_bytes(result.stdout + result.stderr)
    result = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'bettercpm-default', '-n', str(w / 'file-audit/after.raw')], cwd=w / 'file-audit', capture_output=True, check=True)
    (w / 'file-audit/filesystem.txt').write_bytes(result.stdout + result.stderr)
    assert sha(original) == report['sha256']
    (w / 'result.json').write_text(json.dumps({'status': 'PASS', 'closure_item': 'S7-04', 'group': a.group, 'baseline_sha256': sha(original), 'suite_revision': revision, 'procedure_sha256': sha(a.suite / 'suite/src/ECOTEST.ASM'), 'runner_sha256': sha(w / 'executed-runner.py'), 'emulator_sha256': sha(DEFAULT_EMULATOR), 'pip_sha256': next(x['sha256'] for x in report['included'] if x['name'] == 'PIP.COM'), 'file_audit': audit, 'scope': 'shipped native PIP through cold-boot SUBMIT queue: verified multi-DU copy, CRT output, unsupported LPT/PTR preflight, version and A0/53K return; no UART/printer hardware claim'}, indent=2) + '\n')
    print('PASS native PIP capability gates', w)


if __name__ == '__main__': main()
