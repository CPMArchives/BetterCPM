#!/usr/bin/env python3
"""Native CONFIG combined startup/drive save, rollback and next-cold defaults."""
import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
from pathlib import Path
from add_cpm_file_to_dmk import (extract_raw, add_file, FILESYSTEM_FIRST_SECTOR,
                                SECTOR_SIZE, DIRECTORY_ENTRIES)
from build_montezuma_extended_790k import build
from run_validation_model4 import audit_files
from run_validation_returning import sha
from run_trs80_command import DEFAULT_EMULATOR, key_args
from startup_record import build as startup_record
from system_layout import LAYOUT
from test_config_sysgen import probe
from test_sysgen_install import screen
from trs80gp_launch import run


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'build-root', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--case', choices=('save', 'rollback'), required=True)
    p.add_argument('--analyze-only', action='store_true',
                   help='Analyze retained first-session captures; save still checks a private cold boot')
    a = p.parse_args()
    w = a.output.resolve()
    if not a.analyze_only:
        w.mkdir(parents=True, exist_ok=False)
    else:
        assert w.is_dir()
    report = json.loads((a.baseline / 'report.json').read_text())
    original = a.baseline / report['image']
    assert report['target'] == 'trs80gp' and sha(original) == report['sha256']
    program = a.build_root / 'build/utilities/CONFIG.COM'
    assert sha(program) == next(f['sha256'] for f in report['included'] if f['name'] == 'CONFIG.COM')
    if a.analyze_only:
        shutil.copy2(__file__, w / 'analysis-runner.py')
        analyze(a, w, report, original, program,
                (w / 'SETUP.COM').read_bytes(), (w / 'CHECK.COM').read_bytes(),
                (w / 'before.raw').read_bytes())
        return
    setup = probe(w, fault=a.case == 'rollback')
    if a.case == 'rollback':
        # This supplemental probe's hand-encoded hook fails write 2 by default.
        # Move the single failure to write 3: both pending startup records have
        # been written, and the first changed drive-default record then fails.
        signature = bytes.fromhex('3a18903c321890fe02')
        assert setup.count(signature) == 1
        at = setup.index(signature) + 8
        patched = bytearray(setup)
        patched[at] = 3
        (w / 'fault-patch.json').write_text(json.dumps({
            'unpatched_sha256': hashlib.sha256(setup).hexdigest(),
            'offset': at, 'old': 2, 'new': 3,
            'scope': 'supplemental SETUP.COM only; fail third BIOS write once'
        }, indent=2) + '\n')
        setup = bytes(patched)
        (w / 'SETUP.COM').write_bytes(setup)
    check = probe(w, check=True)
    raw = extract_raw(original.read_bytes())
    for i in range(DIRECTORY_ENTRIES):
        off = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE + i * 32
        if raw[off] == 0 and raw[off + 1:off + 12] == b'STARTUP SUB':
            raw[off] = 0xE5
    # Avoid optional startup monitors so the declared 9000h probe hook cannot
    # overlap a reconstructed CPX/CCP. Keep the ordinary banner for boot gating.
    add_file(raw, 'STARTUP.SUB', b':VER /BANNER\r\n\x1a')
    add_file(raw, 'SETUP.COM', setup)
    add_file(raw, 'CHECK.COM', check)
    image = w / 'a.dmk'
    image.write_bytes(build(bytes(raw)))
    before = bytes(raw)
    (w / 'before.raw').write_bytes(before)
    shutil.copy2(__file__, w / 'executed-runner.py')
    shutil.copy2(Path(__file__).with_name('test_config_sysgen.py'), w / 'probe-helper.py')
    cmd = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx',
           '-d0', str(image), '-itime', '15000',
           '-iw', 'Type TYPE README.TXT for more', '-id', '6000']
    if a.case == 'rollback':
        cmd.extend(['-tr', '9000,900b'])
    def send(text, wait=None, delay=120):
        cmd.extend(key_args(text))
        if wait:
            cmd.extend(['-id', '120', '-it', '-iw', wait])
        cmd.extend(['-id', str(delay)])
        if wait:
            cmd.append('-it')
    send('SETUP\r', 'SYSGEN PROBE PASS')
    cmd.append('-it')
    send('\r', delay=6000)
    send('CONFIG\r', 'Your choice:')
    send('A', 'Pending startup command:')
    send('E', 'New command (ENTER keeps current):')
    send('VER\r', 'Pending startup command: VER')
    send('\x03', 'Your choice:')
    send('S', 'Save pending cold-boot changes only')
    send('B', 'Save all current settings on system disk A: (Y/N)?')
    expected = ('All current settings saved and verified.' if a.case == 'save'
                else 'Save failed. Original configuration restored.')
    send('Y', expected)
    cmd.extend(['-it', '-ix'])
    (w / 'invocation.json').write_text(json.dumps(cmd, indent=2) + '\n')
    run(cmd, cwd=w, timeout=900, check=True)
    analyze(a, w, report, original, program, setup, check, before)


def analyze(a, w, report, original, program, setup, check, before):
    image = w / 'a.dmk'
    expected = ('All current settings saved and verified.' if a.case == 'save'
                else 'Save failed. Original configuration restored.')
    captures = sorted(w.glob('trs80-text-*.bin'),
                      key=lambda f: int(f.stem.rsplit('-', 1)[1]))
    assert len(captures) >= 2
    texts = [screen(f) for f in captures]
    for i, text in enumerate(texts):
        (w / f'screen-{i}.txt').write_text(text + '\n')
    assert any('SYSGEN PROBE PASS' in text for text in texts)
    assert not any('SYSGEN PROBE FAIL' in text for text in texts)
    assert expected in texts[-1]
    fault_trace = None
    if a.case == 'rollback':
        trace = (w / 'bus-trace-0.txt').read_text()
        entries = re.findall(r'^.*@9000 z ex.*$', trace, re.M | re.I)
        failures = re.findall(r'^.*@900b z ex.*$', trace, re.M | re.I)
        assert len(entries) >= 3 and len(failures) == 1, (entries, failures)
        fault_trace = {'hook_calls': len(entries), 'one_shot_failure_calls': len(failures),
                       'failed_instruction': failures[0]}
    after = bytes(extract_raw(image.read_bytes()))
    (w / 'after.raw').write_bytes(after)
    changed = {i for i, (x, y) in enumerate(zip(before, after)) if x != y}
    reserved = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
    # Cold SUBMIT STARTUP creates/deletes its queue. Permit only that deleted
    # entry and its previously free blocks, never arbitrary filesystem changes.
    used_before = {0, 1}
    for i in range(DIRECTORY_ENTRIES):
        off = reserved + i * 32
        if before[off] < 32:
            used_before.update(int.from_bytes(before[off + j:off + j + 2], 'little')
                               for j in range(16, 32, 2))
    scratch = set()
    for i in range(DIRECTORY_ENTRIES):
        off = reserved + i * 32
        if after[off + 1:off + 12] != b'$$$     SUB':
            continue
        assert after[off] == 0xE5, 'live startup queue remains'
        if before[off:off + 32] == bytes([0xE5]) * 32:
            scratch.update(range(off, off + 32))
            for j in range(16, 32, 2):
                block = int.from_bytes(after[off + j:off + j + 2], 'little')
                if block:
                    assert block not in used_before, 'queue overlaps original live file'
                    start = reserved + block * 2048
                    scratch.update(range(start, start + 2048))
    if a.case == 'rollback':
        assert after[:reserved] == before[:reserved], 'rollback changed system area'
        assert changed <= scratch, 'unexplained filesystem changes after rollback'
    else:
        resident = (a.build_root / 'build/system/resident.bin').read_bytes()
        at = resident.index(b'BDCF' + bytes((5, 4, 4, 64)))
        physical, table = struct.unpack_from('<HH', resident, at + 8)
        base = 8 * 128 - LAYOUT['SYSTEM']
        drive_allowed = set(range(base + physical, base + physical + 24))
        for n in range(4):
            drive_allowed.update(range(base + table + n * 80 + 16,
                                       base + table + n * 80 + 80))
        assert changed <= set(range(128, 384)) | drive_allowed | scratch
        assert changed & drive_allowed, 'no drive defaults changed'
        assert after[128:384] == startup_record('VER', system_base=LAYOUT['SYSTEM'])
        cold = w / 'cold'
        cold.mkdir()
        cold_image = cold / 'a.dmk'
        shutil.copy2(image, cold_image)
        args = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx',
                '-d0', str(cold_image), '-itime', '15000',
                '-iw', 'BetterCP/M 0.90', '-id', '6000']
        args += key_args('CHECK\r') + ['-iw', 'SYSGEN PROBE PASS', '-id', '120', '-it', '-ix']
        (cold / 'invocation.json').write_text(json.dumps(args, indent=2) + '\n')
        run(args, cwd=cold, timeout=480, check=True)
        text = screen(cold / 'trs80-text-0.bin')
        (cold / 'screen.txt').write_text(text + '\n')
        assert 'SYSGEN PROBE PASS' in text and 'SYSGEN PROBE FAIL' not in text
        assert bytes(extract_raw(cold_image.read_bytes())) == after
    audit = audit_files(original, image,
                        dict(report, included=[f for f in report['included']
                                               if f['name'] != 'STARTUP.SUB']), w)
    r = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'bettercpm-default',
                        '-n', str(w / 'after.raw')],
                       cwd=w / 'file-audit', capture_output=True, check=True)
    (w / 'filesystem.txt').write_bytes(r.stdout + r.stderr)
    assert sha(original) == report['sha256']
    (w / 'result.json').write_text(json.dumps({
        'status': 'PASS', 'case': a.case, 'baseline_sha256': report['sha256'],
        'config_sha256': sha(program), 'setup_sha256': hashlib.sha256(setup).hexdigest(),
        'check_sha256': hashlib.sha256(check).hexdigest(),
        'execution_runner_sha256': sha(w / 'executed-runner.py'),
        'analysis_runner_sha256': sha(Path(__file__)), 'emulator_sha256': sha(DEFAULT_EMULATOR),
        'changed_logical_bytes': len(changed),
        'changed_system_bytes': sum(i < reserved for i in changed),
        'declared_queue_scratch_changes': len(changed & scratch),
        'file_audit': audit, 'fault_trace': fault_trace,
        'scope': 'native combined pending startup and active drive defaults; third-write one-shot controlled rollback or save/next-cold activation; not physical power-loss qualification'
    }, indent=2) + '\n')
    print('PASS native CONFIG combined', a.case, w)


if __name__ == '__main__':
    main()
