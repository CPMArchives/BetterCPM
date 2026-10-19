#!/usr/bin/env python3
"""Named SYSGEN export/install/reboot with shipped Model 4 release utilities."""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from add_cpm_file_to_dmk import add_file, extract_raw
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR, key_args as matrix_keys
from run_validation_model4 import audit_files, sha
from test_model4_copy import files
from test_sysgen_install import screen
import test_sysgen_install as installer
from trs80gp_launch import run

RESERVED = 20480


def key_args(text, delay=25):
    return matrix_keys(text, delay=delay)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    report = json.loads((args.baseline / 'report.json').read_text())
    original = args.baseline / report['image']
    assert report['target'] == 'trs80gp' and sha(original) == report['sha256']
    args.output.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='sysgen-', dir=args.output.resolve()))
    shutil.copy2(__file__, work / 'executed-runner.py')
    shutil.copy2(args.baseline / 'diskdefs', work / 'diskdefs')
    raw = extract_raw(original.read_bytes())
    # This private helper only installs a B: SYSTEM binding through public
    # disk-control services. Every shipped program remains the release binary.
    installer.OUT = work
    add_file(raw, 'SETBSYS.COM', installer.setup_program())
    source_before = bytes(raw)
    source = work / 'source.dmk'
    source.write_bytes(build(source_before))
    target_raw = extract_raw(original.read_bytes())
    sentinel = b'PRESERVED ACROSS NAMED SYSTEM EXPORT AND INSTALL\r\n\x1a'
    add_file(target_raw, 'KEEP.TXT', sentinel)
    target_before = bytes(target_raw)
    target = work / 'target.dmk'
    target.write_bytes(build(target_before))

    def invocation(image=source):
        return [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx',
                '-d0', str(image), '-d1', str(target), '-itime', '15000',
                '-iw', 'Type TYPE README.TXT for more', '-id', '6000']

    command = invocation()
    command += key_args('SETBSYS\r') + ['-iw', 'B SYSTEM READY', '-id', '6000']
    command += key_args('SYSGEN A: B:BASE090.SYS\r', delay=25)
    command += ['-iw', 'Package exported and verified.', '-id', '6000', '-it', '-ix']
    export = work / 'export'
    export.mkdir()
    (export / 'invocation.json').write_text(json.dumps(command, indent=2) + '\n')
    run(command, cwd=export, timeout=600)
    text = screen(export / 'trs80-text-0.bin')
    (export / 'screen.txt').write_text(text + '\n')
    assert 'Package exported and verified.' in text, text
    exported = bytes(extract_raw(target.read_bytes()))
    assert exported[:RESERVED] == target_before[:RESERVED]
    current = files(exported[RESERVED:])
    package = current[0, b'BASE090 SYS'][0]
    assert len(package) == 20608 and package[:8] == b'BCSY\x01\x01\xa0\x00'
    assert package[128:] == source_before[:RESERVED]
    for key, (content, entries) in files(target_before[RESERVED:]).items():
        assert current[key] == (content, entries), key
    assert bytes(extract_raw(source.read_bytes()))[:RESERVED] == source_before[:RESERVED]
    (work / 'BASE090.SYS').write_bytes(package)

    # Install from the named package back onto its own containing disk. The
    # utility must buffer its input and leave every filesystem byte untouched.
    install = work / 'install'
    install.mkdir()
    command = invocation()
    command += key_args('SETBSYS\r') + ['-iw', 'B SYSTEM READY', '-id', '6000']
    command += key_args('SYSGEN B:BASE090.SYS B:\r', delay=25)
    command += ['-iw', 'Proceed (Y/N)?', '-it']
    command += key_args('Y', delay=60)
    command += ['-iw', 'System installed and verified.', '-id', '6000', '-it', '-ix']
    (install / 'invocation.json').write_text(json.dumps(command, indent=2) + '\n')
    run(command, cwd=install, timeout=600)
    texts = [screen(p) for p in sorted(install.glob('trs80-text-*.bin'))]
    (install / 'screens.txt').write_text('\n\n'.join(texts))
    assert len(texts) == 2 and 'Proceed (Y/N)?' in texts[0]
    assert 'System installed and verified.' in texts[1]
    installed = bytes(extract_raw(target.read_bytes()))
    assert installed[RESERVED:] == exported[RESERVED:]
    # The sole defined payload change is the boot binding's surface/cylinder
    # track normalization; compare every byte rather than trusting the message.
    differences = [(i, before, after) for i, (before, after) in
                   enumerate(zip(package[128:], installed[:RESERVED])) if before != after]
    assert differences == [(7030, 0xE0, 0xA0)], differences
    assert files(installed[RESERVED:])[0, b'KEEP    TXT'][0].startswith(sentinel)

    cold = work / 'cold'
    cold.mkdir()
    command = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx',
               '-d0', str(target), '-itime', '15000',
               '-iw', 'Type TYPE README.TXT for more', '-id', '6000']
    command += key_args('ED /VER\r') + ['-iw', 'BetterCP/M ED', '-id', '6000', '-it', '-ix']
    (cold / 'invocation.json').write_text(json.dumps(command, indent=2) + '\n')
    run(command, cwd=cold, timeout=300)
    text = screen(cold / 'trs80-text-0.bin')
    (cold / 'screen.txt').write_text(text + '\n')
    assert 'BetterCP/M ED' in text and 'A0>' in text, text
    assert bytes(extract_raw(target.read_bytes()))[:RESERVED] == installed[:RESERVED]
    source_audit = audit_files(original, source, report, work)
    target_audit = audit_files(original, target, report, cold)
    for folder in (work / 'file-audit', cold / 'file-audit'):
        check = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f',
                                'bettercpm-default', '-n', str(folder / 'after.raw')],
                               cwd=folder, capture_output=True, text=True)
        (folder / 'filesystem.txt').write_text(check.stdout + check.stderr)
        assert check.returncode == 0
    assert sha(original) == report['sha256']
    result = dict(status='PASS', baseline_sha256=report['sha256'],
                  emulator_sha256=sha(DEFAULT_EMULATOR), runner_sha256=sha(Path(__file__)),
                  source_file_audit=source_audit, target_file_audit=target_audit,
                  payload_differences=differences,
                  scope='Shipped named export exact bytes, package install on containing disk, filesystem/sentinel preservation and installed native cold boot; no physical-drive or broad fault-injection claim')
    (work / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS', work, flush=True)


if __name__ == '__main__':
    main()
