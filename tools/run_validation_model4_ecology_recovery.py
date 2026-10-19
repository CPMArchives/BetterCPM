#!/usr/bin/env python3
"""External native ordinary resident-command failure and disk-full recovery."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw, add_file, FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE, DIRECTORY_ENTRIES
from build_source_disk import install_files, BLOCK_COUNT
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
    p.add_argument('--group', choices=('ordinary', 'full'), required=True)
    p.add_argument('--analyze-only', action='store_true', help='Review retained execution without modifying media or launching an emulator')
    a = p.parse_args()
    w = a.output.resolve()
    report = json.loads((a.baseline / 'report.json').read_text())
    original = a.baseline / report['image']
    assert report['target'] == 'trs80gp' and sha(original) == report['sha256']
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=a.suite, text=True).strip()
    assert revision == 'a9a878fcd2e36698c7e856654a85847a004fdd20'
    if a.analyze_only:
        assert (w / 'executed-runner.py').is_file()
        before_raw = (w / 'b-before.raw').read_bytes()
        analyze(a, w, report, original, before_raw, files(before_raw),
                json.loads((w / 'observations.json').read_text()), w / 'a.dmk', w / 'b.dmk', revision)
        return
    w.mkdir(parents=True, exist_ok=False)
    raw = extract_raw(original.read_bytes())
    for i in range(DIRECTORY_ENTRIES):
        at = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE + i * 32
        if raw[at] == 0 and raw[at + 1:at + 12] == b'STARTUP SUB': raw[at] = 0xE5
    add_file(raw, 'STARTUP.SUB', b':VER /BANNER\r\n\x1a')
    source = (ROOT / 'tests/fixtures/conformance/returnstate.mac').read_text()
    (w / 'state.asm').write_text(source)
    assembler = Path.home() / 'bin/z80asm'
    state = assemble(assembler, source, w / 'STATE.COM', w / 'state.lst', 0x100)
    add_file(raw, 'STATE.COM', state)
    fixtures = [(0, 'KEEP.TXT', b'ECOLOGY KEEP SENTINEL\r\n\x1a'), (0, 'FIRST.TXT', b'FIRST SENTINEL\x1a'), (0, 'SECOND.TXT', b'SECOND SENTINEL\x1a')]
    for name in ('DIR', 'ERA', 'REN', 'SAVE', 'TYPE', 'USER'):
        marker = f" ORG 100H\n LD DE,MSG\n LD C,9\n CALL 5\n RET\nMSG: DB 'TRANSIENT MARKER {name}',13,10,'$'\n END\n"
        (w / (name + '.asm')).write_text(marker)
        binary = assemble(assembler, marker, w / (name + '.COM'), w / (name + '.lst'), 0x100)
        fixtures.append((0, name + '.COM', binary))
    before_raw = install_files(fixtures)
    if a.group == 'full':
        used = {0, 1}
        for at in range(0, 4096, 32):
            if before_raw[at] < 32:
                used.update(int.from_bytes(before_raw[at+i:at+i+2], 'little') for i in range(16, 32, 2))
        fixtures.append((0, 'FILLER.BIN', bytes([0xA5]) * ((BLOCK_COUNT - len(used)) * 2048)))
        before_raw = install_files(fixtures)
        all_used = {0, 1}
        for at in range(0, 4096, 32):
            if before_raw[at] < 32:
                all_used.update(int.from_bytes(before_raw[at+i:at+i+2], 'little') for i in range(16, 32, 2))
        assert all_used == set(range(BLOCK_COUNT)), 'fixture not allocation-full'
    before_files = files(before_raw)
    (w / 'b-before.raw').write_bytes(before_raw)
    image = w / 'a.dmk'; image.write_bytes(build(bytes(raw)))
    secondary = w / 'b.dmk'; secondary.write_bytes(build(bytes(before_raw)))
    shutil.copy2(__file__, w / 'executed-runner.py')
    cmd = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx', '-d0', str(image), '-d1', str(secondary), '-itime', '15000', '-iw', 'Type TYPE README.TXT for more', '-id', '6000']
    observations = []
    def send(text, wait, expected=None):
        cmd.extend(key_args(text + '\r', delay=25))
        cmd.extend(['-id', '120', '-iw', wait, '-id', '6000', '-it'])
        observations.append({'command': text, 'expected': expected or wait})
    send('B:', 'B0>')
    cases = ([('SAVE 1 NOSPACE.COM', 'NO SPACE')] if a.group == 'full' else [
        ('DIR MISSING.TXT', 'NO FILE'), ('ERA MISSING.TXT', 'NO FILE'),
        ('REN MISSING.TXT NEW.TXT', 'NO FILE'),
        ('REN FIRST.TXT SECOND.TXT', 'FILE EXISTS'),
        ('SAVE X BAD.COM', '? SAVE pages filename'),
        ('SAVE 1 BAD.COM EXTRA', '? SAVE pages filename'),
        ('TYPE MISSING.TXT', 'NO FILE')])
    for command, diagnostic in cases:
        send('CLS', 'B0>')
        send(command, diagnostic)
        send('A0:STATE', 'STATE D=01 U=00 TOP=D501')
        send('TYPE KEEP.TXT', 'ECOLOGY KEEP SENTINEL')
    send('A:', 'A0>')
    send('STATE', 'STATE D=00 U=00 TOP=D501')
    send('VER', 'BetterCP/M 0.90')
    cmd.append('-ix')
    (w / 'invocation.json').write_text(json.dumps(cmd, indent=2) + '\n')
    (w / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')
    run(cmd, cwd=w, timeout=1800, check=True)
    analyze(a, w, report, original, before_raw, before_files, observations, image, secondary, revision)


def analyze(a, w, report, original, before_raw, before_files, observations, image, secondary, revision):
    shutil.copy2(__file__, w / 'analysis-runner.py')
    captures = sorted(w.glob('trs80-text-*.bin'), key=lambda f: int(f.stem.rsplit('-', 1)[1]))
    texts = [screen(f) for f in captures]
    assert len(texts) == len(observations)
    for i, (t, row) in enumerate(zip(texts, observations)):
        (w / f'screen-{i}.txt').write_text(t + '\n')
        assert (row['command'] == 'CLS' or row['command'] in t) and row['expected'] in t, (i, row, t)
        assert 'TRANSIENT MARKER' not in t, 'resident dispatch fell through'
    assert 'STATE D=00 U=00 TOP=D501' in texts[-1]
    tail = texts[-1][texts[-1].rindex('A0>VER'):]
    assert 'BetterCP/M 0.90' in tail and tail.rstrip().endswith('A0>')
    after_raw = extract_raw(secondary.read_bytes()); (w / 'b-after.raw').write_bytes(after_raw)
    current = files(after_raw)
    if a.group == 'ordinary':
        assert bytes(after_raw) == bytes(before_raw), 'ordinary failures mutated the data disk'
    else:
        empty = (0, b'NOSPACE COM')
        assert set(current) == set(before_files) | {empty}
        assert current[empty][0] == b''
        for key, value in before_files.items(): assert current[key] == value
        assert after_raw[4096:] == before_raw[4096:]
        assert sum(after_raw[i:i+32] != before_raw[i:i+32] for i in range(0,4096,32)) == 1
    audit = audit_files(original, image, dict(report, included=[f for f in report['included'] if f['name'] != 'STARTUP.SUB']), w)
    assert extract_raw(image.read_bytes())[:20480] == extract_raw(original.read_bytes())[:20480]
    (w / 'diskdefs').write_text('diskdef native-data\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 0\n os 2.2\nend\n')
    for path in ('b-before.raw', 'b-after.raw'):
        result = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'native-data', '-n', str(w / path)], cwd=w, capture_output=True, check=True)
        (w / (path + '.fsck.txt')).write_bytes(result.stdout + result.stderr)
    result = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'bettercpm-default', '-n', str(w / 'file-audit/after.raw')], cwd=w / 'file-audit', capture_output=True, check=True)
    (w / 'file-audit/filesystem.txt').write_bytes(result.stdout + result.stderr)
    assert sha(original) == report['sha256']
    (w / 'result.json').write_text(json.dumps({'status': 'PASS', 'card': '0579', 'group': a.group, 'cases': [(r['command'], r['expected']) for r in observations if r['command'].split()[0] in ('DIR', 'ERA', 'REN', 'SAVE') or r['command'] == 'TYPE MISSING.TXT'], 'baseline_sha256': sha(original), 'suite_revision': revision, 'procedure_sha256': sha(a.suite / 'suite/src/ECOTEST.ASM'), 'runner_sha256': sha(w / 'executed-runner.py'), 'analyzer_sha256': sha(w / 'analysis-runner.py'), 'emulator_sha256': sha(DEFAULT_EMULATOR), 'file_audit': audit, 'scope': 'native selected ordinary failure-recovery cases; caller restored A0/53K; no physical controller or power-loss simulation, no suite rows modified'}, indent=2) + '\n')
    print('PASS native ordinary failure recovery', a.group, w)


if __name__ == '__main__': main()
