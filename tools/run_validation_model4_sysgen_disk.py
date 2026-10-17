#!/usr/bin/env python3
"""Validate shipped disk-source SYSGEN refusals, installation and native reboot."""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from add_cpm_file_to_dmk import add_file, extract_raw
from build_ccp import assemble
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR, key_args
from run_validation_model4 import audit_files, sha
from test_model4_copy import files
from test_sysgen_install import screen
import test_sysgen_install as installer
from trs80gp_launch import run

RESERVED = 20480


def alias_helper(work, source_drive, name):
    """Map logical C onto A/B through public binding calls, with no disk writes."""
    source = f'''        ASEG
        ORG 100H
        LD A,{source_drive}
        LD (REQ),A
        LD DE,REQ
        LD BC,03B5H
        CALL 5
        LD A,L
        OR A
        JR NZ,BAD
        LD A,2
        LD (REQ),A
        LD A,(REQ+20)
        BIT 5,A
        JR Z,SETIT
        AND 0DFH
        OR 040H
        LD (REQ+20),A
        LD HL,(REQ+2)
        SRL H
        RR L
        LD (REQ+2),HL
        LD HL,(REQ+15)
        ADD HL,HL
        LD (REQ+15),HL
SETIT:  LD DE,REQ
        LD BC,04B5H
        CALL 5
        LD A,L
        OR A
        JR NZ,BAD
        LD DE,GOOD
        JR SHOW
BAD:    LD DE,FAIL
SHOW:   LD C,9
        CALL 5
        JP 0
GOOD:   DB 26,'{name} READY',13,10,'$'
FAIL:   DB 26,'{name} FAILED',13,10,'$'
REQ:    DS 80
        END
'''
    return assemble(Path.home() / 'bin/z80asm', source, work / (name + '.COM'),
                    work / (name.lower() + '.lst'), 0x100)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    report = json.loads((args.baseline / 'report.json').read_text())
    original = args.baseline / report['image']
    assert report['target'] == 'trs80gp' and sha(original) == report['sha256']
    args.output.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='sysgen-disk-', dir=args.output.resolve()))
    shutil.copy2(__file__, work / 'executed-runner.py')
    raw = extract_raw(original.read_bytes())
    installer.OUT = work
    add_file(raw, 'SETBSYS.COM', installer.setup_program())
    for drive, name in ((0, 'ALIASA'), (1, 'ALIASB')):
        add_file(raw, name + '.COM', alias_helper(work, drive, name))
    source_before = bytes(raw)
    source = work / 'source.dmk'
    source.write_bytes(build(source_before))
    target_raw = extract_raw(original.read_bytes())
    sentinel = b'DISK SOURCE SYSGEN PRESERVES EXISTING FILES\r\n\x1a'
    add_file(target_raw, 'KEEP.TXT', sentinel)
    target_before = bytes(target_raw)
    target = work / 'target.dmk'
    target.write_bytes(build(target_before))
    target_dmk_before = target.read_bytes()

    def invocation():
        return [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx',
                '-d0', str(source), '-d1', str(target), '-itime', '15000',
                '-iw', 'Type TYPE README.TXT for more', '-id', '6000']

    def launch(label, command, count, timeout=600):
        folder = work / label
        folder.mkdir()
        (folder / 'invocation.json').write_text(json.dumps(command, indent=2) + '\n')
        run(command, cwd=folder, timeout=timeout)
        captures = sorted(folder.glob('trs80-text-*.bin'), key=lambda p: int(p.stem.rsplit('-', 1)[1]))
        texts = [screen(p) for p in captures]
        (folder / 'screens.txt').write_text('\n\n'.join(texts))
        assert len(texts) == count, texts
        assert not any('ALIASA FAILED' in t or 'ALIASB FAILED' in t for t in texts)
        return texts

    cmd = invocation()
    cmd += key_args('SETBSYS\r') + ['-iw', 'B SYSTEM READY', '-id', '6000']
    cmd += key_args('SYSGEN A: B:\r', delay=25) + ['-iw', 'Proceed (Y/N)?', '-it']
    cmd += key_args('N', delay=60) + ['-id', '6000', '-it']
    cmd += key_args('ALIASB\r') + ['-iw', 'ALIASB READY', '-id', '6000']
    cmd += key_args('SYSGEN B: C:\r', delay=25)
    cmd += ['-iw', 'Source and destination refer to the same physical drive.', '-id', '6000', '-it']
    cmd += key_args('ALIASA\r') + ['-iw', 'ALIASA READY', '-id', '6000']
    cmd += key_args('SYSGEN B: C:\r', delay=25)
    cmd += ['-iw', 'Physical drive 0 is protected as the running system disk.', '-id', '6000', '-it', '-ix']
    texts = launch('refusals', cmd, 4, timeout=900)
    assert 'Proceed (Y/N)?' in texts[0] and 'A0>' in texts[1]
    assert 'same physical drive.' in texts[2]
    assert 'Physical drive 0 is protected' in texts[3]
    assert target.read_bytes() == target_dmk_before
    assert bytes(extract_raw(source.read_bytes()))[:RESERVED] == source_before[:RESERVED]
    print('PASS: decline and logical-alias/physical-zero safeguards; target unchanged', work, flush=True)

    # Poison all system records to prove that a successful install replaces
    # the payload, while retaining a populated, independently checked filesystem.
    poisoned = b'\xa5' * RESERVED + target_before[RESERVED:]
    target.write_bytes(build(poisoned))
    (work / 'target-before-install.raw').write_bytes(poisoned)
    cmd = invocation()
    cmd += key_args('SETBSYS\r') + ['-iw', 'B SYSTEM READY', '-id', '6000']
    cmd += key_args('SYSGEN A: B:\r', delay=25) + ['-iw', 'Proceed (Y/N)?', '-it']
    cmd += key_args('Y', delay=60)
    cmd += ['-iw', 'System installed and verified.', '-id', '6000', '-it', '-ix']
    texts = launch('install', cmd, 2)
    assert 'System installed and verified.' in texts[1]
    installed = bytes(extract_raw(target.read_bytes()))
    assert installed[RESERVED:] == poisoned[RESERVED:]
    differences = [(i, a, b) for i, (a, b) in enumerate(zip(source_before[:RESERVED], installed[:RESERVED])) if a != b]
    assert differences == [(7030, 0xE0, 0xA0)], differences
    assert bytes(extract_raw(source.read_bytes()))[:RESERVED] == source_before[:RESERVED]
    assert files(installed[RESERVED:])[0, b'KEEP    TXT'][0].startswith(sentinel)
    (work / 'target-installed.raw').write_bytes(installed)
    print('PASS: confirmed disk install; payload and entire filesystem independently checked', work, flush=True)

    cmd = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx',
           '-d0', str(target), '-itime', '15000', '-iw', 'Type TYPE README.TXT for more', '-id', '6000']
    cmd += key_args('ED /VER\r') + ['-iw', 'BetterCP/M ED', '-id', '6000', '-it', '-ix']
    texts = launch('cold', cmd, 1, timeout=300)
    assert 'BetterCP/M ED' in texts[0] and 'A0>' in texts[0]
    assert bytes(extract_raw(target.read_bytes()))[:RESERVED] == installed[:RESERVED]
    assert files(extract_raw(target.read_bytes())[RESERVED:])[0, b'KEEP    TXT'][0].startswith(sentinel)
    source_audit = audit_files(original, source, report, work)
    target_audit = audit_files(original, target, report, work / 'cold')
    for folder in (work / 'file-audit', work / 'cold/file-audit'):
        check = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'bettercpm-default', '-n',
                                str(folder / 'after.raw')], cwd=folder, capture_output=True, text=True)
        (folder / 'filesystem.txt').write_text(check.stdout + check.stderr)
        assert check.returncode == 0
    assert sha(original) == report['sha256']
    result = dict(status='PASS', baseline_sha256=report['sha256'], emulator_sha256=sha(DEFAULT_EMULATOR),
                  runner_sha256=sha(Path(__file__)), payload_differences=differences,
                  source_file_audit=source_audit, target_file_audit=target_audit,
                  scope='Shipped native disk-source decline, distinct-logical-letter alias and physical-zero protection, confirmed install into poisoned system area, filesystem/sentinel preservation and installed cold boot; no physical-hardware or power-loss claim')
    (work / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: native disk-source SYSGEN campaign', work, flush=True)


if __name__ == '__main__':
    main()
