#!/usr/bin/env python3
"""Native external witnesses for BDOS buffered-input and BIOS-resource cards."""
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
from trs80gp_launch import run


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'suite', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    w = a.output.resolve(); w.mkdir(parents=True, exist_ok=False)
    report = json.loads((a.baseline / 'report.json').read_text())
    original = a.baseline / report['image']
    assert report['target'] == 'trs80gp' and sha(original) == report['sha256']
    suite_revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=a.suite, text=True).strip()
    assert suite_revision == 'a9a878fcd2e36698c7e856654a85847a004fdd20', 'unexpected suite revision'
    raw = extract_raw(original.read_bytes())
    for i in range(DIRECTORY_ENTRIES):
        at = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE + i * 32
        if raw[at] == 0 and raw[at + 1:at + 12] == b'STARTUP SUB': raw[at] = 0xE5
    add_file(raw, 'STARTUP.SUB', b':VER /BANNER\r\n\x1a')
    source = (Path(__file__).resolve().parents[1] / 'tests/fixtures/conformance/bdos-manual-probes.mac').read_text()
    (w / 'probe.asm').write_text(source)
    probe = assemble(Path.home() / 'bin/z80asm', source, w / 'BDOPROBE.COM', w / 'probe.lst', 0x100)
    add_file(raw, 'BDOPROBE.COM', probe)
    state_source = (Path(__file__).resolve().parents[1] / 'tests/fixtures/conformance/returnstate.mac').read_text()
    (w / 'state.asm').write_text(state_source)
    state = assemble(Path.home() / 'bin/z80asm', state_source, w / 'STATE.COM', w / 'state.lst', 0x100)
    add_file(raw, 'STATE.COM', state)
    braw = bytearray(install_files([(0, 'SENTINEL.TXT', b'UNCHANGED RESOURCE FIXTURE\r\n\x1a')]))
    (w / 'b-before.raw').write_bytes(braw)
    image = w / 'a.dmk'; image.write_bytes(build(bytes(raw)))
    secondary = w / 'b.dmk'; secondary.write_bytes(build(bytes(braw)))
    shutil.copy2(__file__, w / 'executed-runner.py')
    cmd = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx', '-d0', str(image), '-d1', str(secondary), '-itime', '15000', '-iw', 'Type TYPE README.TXT for more', '-id', '6000']
    def send(text, wait):
        cmd.extend(key_args(text, delay=12))
        cmd.extend(['-id', '120', '-it', '-iw', wait, '-id', '6000', '-it'])
    send('A0:BDOPROBE\r', '0420 INPUT READY:')
    send('BUFFER42\r', 'OR-0519 PASS:')
    send('A0:STATE\r', 'STATE D=00 U=00 TOP=D501')
    send('VER\r', 'BetterCP/M 0.90')
    cmd.append('-ix')
    (w / 'invocation.json').write_text(json.dumps(cmd, indent=2) + '\n')
    run(cmd, cwd=w, timeout=1200, check=True)
    captures = sorted(w.glob('trs80-text-*.bin'), key=lambda f: int(f.stem.rsplit('-', 1)[1]))
    texts = [screen(f) for f in captures]
    for i, text in enumerate(texts): (w / f'screen-{i}.txt').write_text(text + '\n')
    assert any('OR-0420 PASS:' in t for t in texts)
    assert any('OR-0519 PASS:' in t for t in texts)
    assert not any('OR-0420 FAIL' in t or 'OR-0519 FAIL' in t for t in texts)
    assert 'STATE D=00 U=00 TOP=D501' in texts[-1]
    tail = texts[-1][texts[-1].rindex('A0>VER'):]
    assert 'BetterCP/M 0.90' in tail and tail.rstrip().endswith('A0>')
    after = extract_raw(secondary.read_bytes()); (w / 'b-after.raw').write_bytes(after)
    assert bytes(after) == bytes(braw), 'resource selection changed the data disk'
    audit = audit_files(original, image, dict(report, included=[f for f in report['included'] if f['name'] != 'STARTUP.SUB']), w)
    assert extract_raw(image.read_bytes())[:20480] == extract_raw(original.read_bytes())[:20480]
    (w / 'diskdefs').write_text('diskdef native-data\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 0\n os 2.2\nend\n')
    for path in ('b-before.raw', 'b-after.raw'):
        result = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'native-data', '-n', str(w / path)], cwd=w, capture_output=True, check=True)
        (w / (path + '.fsck.txt')).write_bytes(result.stdout + result.stderr)
    checked = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'bettercpm-default', '-n', str(w / 'file-audit/after.raw')], cwd=w / 'file-audit', capture_output=True, check=True)
    (w / 'file-audit/filesystem.txt').write_bytes(checked.stdout + checked.stderr)
    assert sha(original) == report['sha256']
    (w / 'result.json').write_text(json.dumps({'status': 'PASS', 'cards': ['0420', '0519'], 'baseline_sha256': sha(original), 'probe_sha256': sha(w / 'BDOPROBE.COM'), 'suite_revision': suite_revision, 'oracle_definitions_sha256': sha(a.suite / 'docs/conformance/tables/oracle-definitions.tsv'), 'runner_sha256': sha(w / 'executed-runner.py'), 'emulator_sha256': sha(DEFAULT_EMULATOR), 'data_disk_unchanged': True, 'file_audit': audit, 'scope': 'external native oracle witnesses; no suite result rows modified; A B A resource selection and one buffered-input line'}, indent=2) + '\n')
    print('PASS native BDOS external probes', w)



if __name__ == '__main__': main()
