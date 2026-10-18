#!/usr/bin/env python3
"""Native OR-0143 media replacement, write protection and explicit reset."""
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
    p.add_argument('--mode', choices=('write', 'reset'), required=True)
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
    source = (Path(__file__).resolve().parents[1] / 'tests/fixtures/conformance/media-change-probe.mac').read_text()
    (w / 'probe.asm').write_text(source)
    probe = assemble(Path.home() / 'bin/z80asm', source, w / 'MEDIA.COM', w / 'probe.lst', 0x100)
    add_file(raw, 'MEDIA.COM', probe)
    add_file(raw, 'ANCHOR.DAT', b'CACHE EVICTION SENTINEL\x1a')
    state_source = (Path(__file__).resolve().parents[1] / 'tests/fixtures/conformance/returnstate.mac').read_text()
    (w / 'state.asm').write_text(state_source)
    state = assemble(Path.home() / 'bin/z80asm', state_source, w / 'STATE.COM', w / 'state.lst', 0x100)
    add_file(raw, 'STATE.COM', state)
    oldraw = install_files([(0, 'OLD.TXT', b'ORIGINAL MEDIA SENTINEL\r\n\x1a')])
    newraw = install_files([(0, 'NEW.TXT', b'REPLACEMENT SENTINEL\r\n\x1a')])
    (w / 'old-before.raw').write_bytes(oldraw)
    (w / 'new-before.raw').write_bytes(newraw)
    image = w / 'a.dmk'; image.write_bytes(build(bytes(raw)))
    old = w / 'old.dmk'; old.write_bytes(build(bytes(oldraw)))
    replacement = w / 'new.dmk'; replacement.write_bytes(build(bytes(newraw)))
    shutil.copy2(__file__, w / 'executed-runner.py')
    cmd = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx', '-d0', str(image), '-d1', str(old), '-itime', '15000', '-iw', 'Type TYPE README.TXT for more', '-id', '6000']
    def send(text, wait):
        cmd.extend(key_args(text, delay=25))
        cmd.extend(['-id', '120', '-it', '-iw', wait, '-id', '6000', '-it'])
    send('MEDIA' + (' R' if a.mode == 'reset' else '') + '\r', 'OR-0143 SWAP LOGGED B NOW')
    cmd.extend(['-im', 'eject', '1', '1', '-im', 'insert', '1', str(replacement)])
    send('Y', 'OR-0143 RESET AND CREATE PASS' if a.mode == 'reset' else 'Disk R/O')
    send('A0:STATE\r', 'STATE D=01 U=00 TOP=D501')
    send('VER\r', 'BetterCP/M 0.90')
    cmd.append('-ix')
    (w / 'invocation.json').write_text(json.dumps(cmd, indent=2) + '\n')
    run(cmd, cwd=w, timeout=1200, check=True)
    captures = sorted(w.glob('trs80-text-*.bin'), key=lambda f: int(f.stem.rsplit('-', 1)[1]))
    texts = [screen(f) for f in captures]
    for i, text in enumerate(texts): (w / f'screen-{i}.txt').write_text(text + '\n')
    assert any('OR-0143 REPLACEMENT READ AND PROTECTED' in t for t in texts)
    expected = 'OR-0143 RESET AND CREATE PASS' if a.mode == 'reset' else 'Disk R/O'
    assert any(expected in t for t in texts)
    assert not any('OR-0143 FAIL' in t or 'OR-0143 FIXTURE OR PROTECTION FAIL' in t for t in texts)
    assert 'STATE D=01 U=00 TOP=D501' in texts[-1]
    tail = texts[-1][texts[-1].rindex('B0>VER'):]
    assert 'BetterCP/M 0.90' in tail and tail.rstrip().endswith('B0>')
    after = extract_raw(replacement.read_bytes()); (w / 'new-after.raw').write_bytes(after)
    assert extract_raw(old.read_bytes()) == bytes(oldraw), 'old medium changed'
    if a.mode == 'write':
        assert bytes(after) == bytes(newraw), 'protected replacement changed'
    else:
        from test_model4_copy import files
        before_files = files(newraw); after_files = files(after)
        created = (0, b'CREATED TXT')
        assert set(after_files) == set(before_files) | {created}
        assert after_files[created][0] == b''
        for key, value in before_files.items(): assert after_files[key] == value
        # Exactly one previously free directory entry may change; no data block.
        assert after[4096:] == newraw[4096:]
        changed = [i for i in range(128) if after[i*32:(i+1)*32] != newraw[i*32:(i+1)*32]]
        assert len(changed) == 1
    audit = audit_files(original, image, dict(report, included=[f for f in report['included'] if f['name'] != 'STARTUP.SUB']), w)
    assert extract_raw(image.read_bytes())[:20480] == extract_raw(original.read_bytes())[:20480]
    (w / 'diskdefs').write_text('diskdef native-data\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 0\n os 2.2\nend\n')
    for path in ('old-before.raw', 'new-before.raw', 'new-after.raw'):
        result = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'native-data', '-n', str(w / path)], cwd=w, capture_output=True, check=True)
        (w / (path + '.fsck.txt')).write_bytes(result.stdout + result.stderr)
    checked = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'bettercpm-default', '-n', str(w / 'file-audit/after.raw')], cwd=w / 'file-audit', capture_output=True, check=True)
    (w / 'file-audit/filesystem.txt').write_bytes(checked.stdout + checked.stderr)
    assert sha(original) == report['sha256']
    (w / 'result.json').write_text(json.dumps({'status': 'PASS', 'card': '0143', 'mode': a.mode, 'baseline_sha256': sha(original), 'probe_sha256': sha(w / 'MEDIA.COM'), 'suite_revision': suite_revision, 'oracle_definitions_sha256': sha(a.suite / 'docs/conformance/tables/oracle-definitions.tsv'), 'runner_sha256': sha(w / 'executed-runner.py'), 'emulator_sha256': sha(DEFAULT_EMULATOR), 'old_medium_unchanged': True, 'protected_replacement_unchanged': a.mode == 'write', 'file_audit': audit, 'scope': 'external native OR-0143 witness using actual emulator media exchange; selected CKS-enabled fixture, no checksum-collision or hardware-sensor guarantee; no suite rows modified'}, indent=2) + '\n')
    print('PASS native media-change protection', a.mode, w)



if __name__ == '__main__': main()
