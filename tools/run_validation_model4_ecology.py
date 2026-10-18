#!/usr/bin/env python3
"""External native resident semantic/SAVE witnesses; not fabricated suite rows."""
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
    add_file(raw, 'STARTUP.SUB', b':VER /BANNER\r\n\x1a')
    source = (ROOT / 'tests/fixtures/conformance/returnstate.mac').read_text()
    (w / 'state.asm').write_text(source)
    assembler = Path.home() / 'bin/z80asm'
    state = assemble(assembler, source, w / 'STATE.COM', w / 'state.lst', 0x100)
    add_file(raw, 'STATE.COM', state)
    fixtures = [(0, 'KEEP.TXT', b'ECOLOGY KEEP SENTINEL\r\n\x1a')]
    for name in ('DIR', 'ERA', 'REN', 'SAVE', 'TYPE', 'USER'):
        marker = f" ORG 100H\n LD DE,MSG\n LD C,9\n CALL 5\n RET\nMSG: DB 'TRANSIENT MARKER {name}',13,10,'$'\n END\n"
        (w / (name + '.asm')).write_text(marker)
        binary = assemble(assembler, marker, w / (name + '.COM'), w / (name + '.lst'), 0x100)
        fixtures.append((0, name + '.COM', binary))
    before_raw = install_files(fixtures)
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
    send('DIR KEEP.TXT', 'KEEP')
    send('REN KEEP.TXT NEW.TXT', 'B0>')
    send('TYPE NEW.TXT', 'ECOLOGY KEEP SENTINEL')
    send('ERA NEW.TXT', 'B0>')
    send('DIR NEW.TXT', 'NO FILE')
    send('USER 3', 'B3>')
    send('A0:STATE', 'STATE D=01 U=03 TOP=D501')
    send('USER 0', 'B0>')
    # Resident POKE avoids a transient primer/return overwriting the page.
    for offset in range(0, 256, 16):
        send('POKE %04X ' % (0x100 + offset) + ' '.join('%02X' % v for v in range(offset, offset + 16)), 'B0>')
    send('SAVE 1 ECOSAVE.COM', 'B0>')
    send('A0:STATE', 'STATE D=01 U=00 TOP=D501')
    send('A:', 'A0>')
    send('STATE', 'STATE D=00 U=00 TOP=D501')
    send('VER', 'BetterCP/M 0.90')
    cmd.append('-ix')
    (w / 'invocation.json').write_text(json.dumps(cmd, indent=2) + '\n')
    (w / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')
    run(cmd, cwd=w, timeout=1800, check=True)
    captures = sorted(w.glob('trs80-text-*.bin'), key=lambda f: int(f.stem.rsplit('-', 1)[1]))
    texts = [screen(f) for f in captures]
    assert len(texts) == len(observations)
    for i, (t, row) in enumerate(zip(texts, observations)):
        (w / f'screen-{i}.txt').write_text(t + '\n')
        assert row['command'] in t and row['expected'] in t, (i, row, t)
        assert 'TRANSIENT MARKER' not in t, 'resident dispatch fell through'
    assert 'KEEP     TXT' in texts[1], 'DIR output did not list the fixture'
    assert 'STATE D=00 U=00 TOP=D501' in texts[-1]
    tail = texts[-1][texts[-1].rindex('A0>VER'):]
    assert 'BetterCP/M 0.90' in tail and tail.rstrip().endswith('A0>')
    after_raw = extract_raw(secondary.read_bytes()); (w / 'b-after.raw').write_bytes(after_raw)
    current = files(after_raw)
    expected_keys = set(before_files) - {(0, b'KEEP    TXT')} | {(0, b'ECOSAVE COM')}
    assert set(current) == expected_keys
    for key, value in before_files.items():
        if key != (0, b'KEEP    TXT'): assert current[key] == value
    saved = current[0, b'ECOSAVE COM'][0]
    assert saved == bytes(range(256)), 'SAVE page differs or wrong length'
    (w / 'ECOSAVE.COM').write_bytes(saved)
    audit = audit_files(original, image, dict(report, included=[f for f in report['included'] if f['name'] != 'STARTUP.SUB']), w)
    assert extract_raw(image.read_bytes())[:20480] == extract_raw(original.read_bytes())[:20480]
    (w / 'diskdefs').write_text('diskdef native-data\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 0\n os 2.2\nend\n')
    for path in ('b-before.raw', 'b-after.raw'):
        result = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'native-data', '-n', str(w / path)], cwd=w, capture_output=True, check=True)
        (w / (path + '.fsck.txt')).write_bytes(result.stdout + result.stderr)
    result = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'bettercpm-default', '-n', str(w / 'file-audit/after.raw')], cwd=w / 'file-audit', capture_output=True, check=True)
    (w / 'file-audit/filesystem.txt').write_bytes(result.stdout + result.stderr)
    assert sha(original) == report['sha256']
    (w / 'result.json').write_text(json.dumps({'status': 'PASS', 'cards': ['0569', '0575'], 'baseline_sha256': sha(original), 'suite_revision': revision, 'procedure_sha256': sha(a.suite / 'suite/src/ECOTEST.ASM'), 'runner_sha256': sha(w / 'executed-runner.py'), 'emulator_sha256': sha(DEFAULT_EMULATOR), 'save_sha256': sha(w / 'ECOSAVE.COM'), 'file_audit': audit, 'scope': 'selected native resident semantics and one SAVE page, namesake marker COMs not executed, caller restored A0/53K; private fixture artifacts retained for audit; TYPE byte stream and failure matrix not covered'}, indent=2) + '\n')
    print('PASS native resident ecology 0569/0575', w)


if __name__ == '__main__': main()
