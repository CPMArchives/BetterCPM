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
    from build_ccp import assemble
    from startup_record import parse
    from system_layout import LAYOUT
    helpers={}
    for value in (0x95,0x55):
        text=f" ORG 100H\n LD A,(3)\n CP {value}\n JR NZ,BAD\n LD DE,OK\n JR PRINT\nBAD: LD DE,FAIL\nPRINT: LD C,9\n CALL 5\n RET\nOK: DB 'LIVE IOBYTE {value:02X} PASS',13,10,'$'\nFAIL: DB 'IOBYTE CHECK FAIL',13,10,'$'\n END\n"
        (work/f'io{value:02x}.asm').write_text(text)
        code=assemble(Path.home()/'bin/z80asm',text,work/f'IO{value:02X}.COM',work/f'io{value:02x}.lst',0x100)
        helpers[f'IO{value:02X}.COM']=code;add_file(raw,f'IO{value:02X}.COM',code)
    source_before = bytes(raw)
    source = work / 'source.dmk'
    source.write_bytes(build(source_before))
    target_raw = extract_raw(original.read_bytes())
    sentinel = b'PRESERVED ACROSS NAMED SYSTEM EXPORT AND INSTALL\r\n\x1a'
    add_file(target_raw, 'KEEP.TXT', sentinel)
    for name,code in helpers.items():add_file(target_raw,name,code)
    target_before = bytes(target_raw)
    target = work / 'target.dmk'
    target.write_bytes(build(target_before))

    configured=False
    def invocation(image=source):
        return [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx',
                '-d0', str(image), '-d1', str(target), '-itime', '15000',
                '-iw', ('BetterCP/M VER 1.0 (Resident' if configured else 'Type TYPE README.TXT for more'), '-id', '6000']

    command = invocation()
    command += key_args('IO95\r',delay=60)+['-iw','LIVE IOBYTE 95 PASS','-id','6000','-it']
    command += key_args('CONFIG /STARTUP="VER /VER"\r',delay=60)+['-iw','Save pending cold-boot changes on system disk A: (Y/N)?']+key_args('Y',delay=60)+['-iw','Pending cold-boot changes saved and verified.','-id','6000','-it']
    command += key_args('CONFIG /IOBYTE=85\r',delay=60)+['-iw','Save disk-boot IOBYTE (Y/N)?']+key_args('Y',delay=60)+['-iw','Disk-boot IOBYTE saved; live unchanged.','-id','6000']
    command += key_args('IO95\r',delay=60)+['-iw','LIVE IOBYTE 95 PASS','-id','6000','-it']
    command += key_args('SETBSYS\r') + ['-iw', 'B SYSTEM READY', '-id', '6000']
    command += key_args('SYSGEN A: B:BASE090.SYS\r', delay=25)
    command += ['-iw', 'Package exported and verified.', '-id', '6000', '-it', '-ix']
    export = work / 'export'
    export.mkdir()
    (export / 'invocation.json').write_text(json.dumps(command, indent=2) + '\n')
    run(command, cwd=export, timeout=600)
    export_texts=[screen(f) for f in sorted(export.glob('trs80-text*'))]
    assert len(export_texts)==4 and all('LIVE IOBYTE 95 PASS' in export_texts[i] for i in (0,2))
    assert 'Pending cold-boot changes saved and verified.' in export_texts[1]
    text=export_texts[-1]
    (export / 'screen.txt').write_text(text + '\n')
    assert 'Package exported and verified.' in text, text
    exported = bytes(extract_raw(target.read_bytes()))
    assert exported[:RESERVED] == target_before[:RESERVED]
    current = files(exported[RESERVED:])
    package = current[0, b'BASE090 SYS'][0]
    assert len(package) == 20608 and package[:8] == b'BCSY\x01\x01\xa0\x00'
    configured_source=bytes(extract_raw(source.read_bytes()))[:RESERVED]
    assert package[128:] == configured_source
    assert parse(configured_source[128:384],system_base=LAYOUT['SYSTEM'])=='VER /VER'
    assert configured_source[513]==0x55 and source_before[513]==0x95
    assert all(configured_source[i]==source_before[i] for i in range(RESERVED) if not (128<=i<384 or i==513))
    configured=True
    for key, (content, entries) in files(target_before[RESERVED:]).items():
        assert current[key] == (content, entries), key
    assert bytes(extract_raw(source.read_bytes()))[:RESERVED] == configured_source
    (work / 'BASE090.SYS').write_bytes(package)
    (work / 'exported-target.raw').write_bytes(exported)
    (work / 'configured-source.raw').write_bytes(bytes(extract_raw(source.read_bytes())))

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
    (work / 'installed-target.raw').write_bytes(installed)
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
               '-iw', 'BetterCP/M VER 1.0 (Resident', '-id', '6000']
    command += key_args('IO55\r',delay=60)+['-iw','LIVE IOBYTE 55 PASS','-id','6000','-it']
    command += key_args('CONFIG /SHOW\r',delay=60)+['-iw','Saved disk-boot IOBYTE (decimal): 85','-it','-id','6000']
    command += key_args('TYPE KEEP.TXT\r',delay=60)+['-iw','PRESERVED ACROSS NAMED SYSTEM EXPORT AND INSTALL','-id','6000','-it','-ix']
    (cold / 'invocation.json').write_text(json.dumps(command, indent=2) + '\n')
    run(command, cwd=cold, timeout=300)
    cold_texts=[screen(f) for f in sorted(cold.glob('trs80-text*'))];assert len(cold_texts)==3
    assert 'LIVE IOBYTE 55 PASS' in cold_texts[0]
    assert 'Saved disk-boot IOBYTE (decimal): 85' in cold_texts[1]
    text=cold_texts[-1]
    (cold / 'screen.txt').write_text(text + '\n')
    assert 'PRESERVED ACROSS NAMED SYSTEM EXPORT AND INSTALL' in text and 'A0>' in text, text
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
                  scope='Native CONFIG startup and IOBYTE save/live unchanged, exact configured named package, confirmed containing-disk install preserving complete filesystem, installed cold boot executes saved startup and restores IOBYTE55; shipped files/sentinel preserved.')
    (work / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS', work, flush=True)


if __name__ == '__main__':
    main()
