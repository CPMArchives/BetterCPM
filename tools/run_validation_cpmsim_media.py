#!/usr/bin/env python3
"""Exercise shipped DUP/SYSGEN on retained disposable release-image copies."""
import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from build_z80pack_image import DEFAULT_FORMAT
from fdf_format import select_fdf
from run_validation_cpmsim_monitors import audit
from run_validation_returning import sha
from startup_record import build as startup_record
from system_layout import LAYOUT
from test_z80pack_sysgen_install import session as emulator_session

ROOT = Path(__file__).resolve().parents[1]


def session(*args, **kwargs):
    trace = emulator_session(*args, **kwargs)
    # The PTY helper's A0 gate can also match a later redisplay. Reject an
    # invalid initial user even if command-line editing subsequently masks it.
    prompts = re.findall(rb'(?:^|[\r\n])A([^>\r\n]{1,4})>', trace)
    assert prompts and all(user == b'0' for user in prompts), prompts
    return trace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--simulator', type=Path,
                        default=Path.home() / 'projects/git/z80pack/cpmsim/cpmsim')
    args = parser.parse_args()
    report = json.loads((args.baseline / 'report.json').read_text())
    original = args.baseline / report['image']
    assert report['target'] == 'z80pack' and sha(original) == report['sha256']
    args.output.mkdir(parents=True, exist_ok=True)
    fmt = select_fdf(ROOT / 'third_party/montezuma/DISK.FDF', DEFAULT_FORMAT)
    mapping = fmt.raw_record_map()

    def offset(record):
        track, within = divmod(record, fmt.spt)
        return track * fmt.raw_track_bytes + mapping[within] * 128

    system_offsets = [offset(i) for i in range(160)]

    def payload(data):
        return b''.join(data[at:at + 128] for at in system_offsets)

    def prepare(label):
        work = Path(tempfile.mkdtemp(prefix=label + '-', dir=args.output.resolve()))
        disks = work / 'disks'
        disks.mkdir()
        shutil.copy2(args.baseline / 'diskdefs', work / 'diskdefs')
        shutil.copy2(__file__, work / 'executed-runner.py')
        data = bytearray(original.read_bytes())
        # Fixture configuration only: avoid SUBMIT temporary-file writes when
        # checking byte-for-byte source preservation. All shipped files stay.
        startup = startup_record(':VER /BANNER', system_base=LAYOUT['SYSTEM'])
        for i in range(2):
            at = offset(i + 1)
            data[at:at + 128] = startup[i * 128:(i + 1) * 128]
        (disks / 'drivea.dsk').write_bytes(data)
        for drive in 'bc':
            (disks / f'drive{drive}.dsk').write_bytes(b'\xe5' * len(data))
        return work, disks

    def extract(work, disk, name, user=0):
        target = work / f'extracted-{user}-{name}'
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default',
                        str(disk), f'{user}:{name}', str(target)],
                       cwd=work, check=True, capture_output=True)
        return target.read_bytes()

    results = []

    def finish(work, disks, label, detail):
        shipped = audit(args.baseline, report, work, disks / 'drivea.dsk')
        for drive in 'bc':
            result = subprocess.run(
                ['fsck.cpm', '-T', 'raw', '-f', 'bettercpm-default', '-n',
                 str(disks / f'drive{drive}.dsk')],
                cwd=work, capture_output=True, text=True)
            (work / f'{drive}-filesystem.txt').write_text(result.stdout + result.stderr)
            assert result.returncode == 0, result.stdout + result.stderr
        result = dict(status='PASS', case=label, detail=detail,
                      baseline_sha256=report['sha256'],
                      simulator_sha256=sha(args.simulator),
                      runner_sha256=sha(Path(__file__)),
                      unchanged_shipped_files=shipped)
        (work / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        results.append(result)
        (args.output / 'media-summary.json').write_text(json.dumps(results, indent=2) + '\n')
        print(label, 'PASS', work, flush=True)

    work, disks = prepare('dup-format')
    source, target = disks / 'drivea.dsk', disks / 'driveb.dsk'
    before = source.read_bytes()
    target.write_bytes(b'\xa5' * len(before))
    trace = session(args.simulator, disks, [
        (b'DUP /FORMAT B:\r', b'[Y/N]', 30),
        (b'N', b'A0>_ ', 30), (b'BYE\r', b'System halted', 30)],
        work / 'decline.bin')
    assert target.read_bytes() == b'\xa5' * len(before)
    assert source.read_bytes() == before
    trace = session(args.simulator, disks, [
        (b'DUP /FORMAT A:\r', b'A0>_ ', 30),
        (b'DUP /FORMAT B:\r', b'[Y/N]', 30),
        (b'Y', b'A0>_ ', 120),
        (b'DUP /CHECK B:\r', b'A0>_ ', 120),
        (b'BYE\r', b'System halted', 30)], work / 'format-check.bin')
    assert b'protected system disk' in trace and b'Format complete.' in trace
    assert b'Unreadable sectors: 00000' in trace
    assert source.read_bytes() == before
    assert target.read_bytes() == b'\xe5' * len(before)
    finish(work, disks, 'dup-format', 'Declined format unchanged; A protected; B completely erased and verified; CHECK reports no unreadable sectors')

    work, disks = prepare('dup-copy')
    source, target = disks / 'drivea.dsk', disks / 'driveb.dsk'
    before, old = source.read_bytes(), target.read_bytes()
    session(args.simulator, disks, [
        (b'DUP /COPY A: B:\r', b'[Y/N]', 30),
        (b'N', b'A0>_ ', 30), (b'BYE\r', b'System halted', 30)],
        work / 'decline.bin')
    assert target.read_bytes() == old and source.read_bytes() == before
    trace = session(args.simulator, disks, [
        (b'DUP /COPY A: B:\r', b'[Y/N]', 30),
        (b'Y', b'A0>_ ', 120),
        (b'DUP /CHECK B:\r', b'A0>_ ', 120),
        (b'BYE\r', b'System halted', 30)], work / 'copy-check.bin')
    assert b'Copy complete; destination verified.' in trace
    assert b'Unreadable sectors: 00000' in trace
    assert source.read_bytes() == before and target.read_bytes() == before
    finish(work, disks, 'dup-copy', 'Declined copy unchanged; confirmed copy equals every source byte; source preserved; CHECK clean')

    work, disks = prepare('sysgen-roundtrip')
    source, target, installed = [disks / f'drive{drive}.dsk' for drive in 'abc']
    before, old_target = source.read_bytes(), target.read_bytes()
    trace = session(args.simulator, disks, [
        (b'SYSGEN A: B:BASE090.SYS\r', b'A0>_ ', 90),
        (b'BYE\r', b'System halted', 30)], work / 'export.bin')
    assert b'Package exported and verified.' in trace
    package = extract(work, target, 'BASE090.SYS')
    assert len(package) == 161 * 128 and package[:8] == b'BCSY\x01\x01\xa0\x00'
    assert package[128:] == payload(before)
    assert source.read_bytes() == before
    reserved = fmt.reserved_records * 128
    assert target.read_bytes()[:reserved] == old_target[:reserved]
    exported = target.read_bytes()
    trace = session(args.simulator, disks, [
        (b'SYSGEN A: B:BASE090.SYS\r', b'Replace existing package (Y/N)?', 30),
        (b'N', b'A0>_ ', 30), (b'BYE\r', b'System halted', 30)],
        work / 'decline-replacement.bin')
    assert target.read_bytes() == exported and source.read_bytes() == before
    trace = session(args.simulator, disks, [
        (b'SYSGEN A: B:BASE090.SYS\r', b'Replace existing package (Y/N)?', 30),
        (b'Y', b'A0>_ ', 90), (b'BYE\r', b'System halted', 30)],
        work / 'replace.bin')
    assert b'Package exported and verified.' in trace
    assert extract(work, target, 'BASE090.SYS') == package
    listing = subprocess.check_output(['cpmls', '-T', 'raw', '-f', 'bettercpm-default', str(target)], cwd=work).lower()
    assert b'sysgen.$$$' not in listing and b'sysgen.bak' not in listing
    # A complete command filesystem on C makes reboot a genuine install test;
    # poison only the system area, and add an independently checked sentinel.
    installed.write_bytes(b'\xa5' * reserved + before[reserved:])
    sentinel = work / 'KEEP.TXT'
    sentinel.write_bytes(b'USER SEVEN SURVIVES SYSTEM INSTALL\r\n')
    subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default',
                    str(installed), str(sentinel), '7:KEEP.TXT'], cwd=work, check=True)
    old_installed = installed.read_bytes()
    trace = session(args.simulator, disks, [
        (b'SYSGEN B:BASE090.SYS C:\r', b'Proceed (Y/N)?', 30),
        (b'N', b'A0>_ ', 30), (b'BYE\r', b'System halted', 30)],
        work / 'decline-install.bin')
    assert installed.read_bytes() == old_installed
    trace = session(args.simulator, disks, [
        (b'SYSGEN B:BASE090.SYS C:\r', b'Proceed (Y/N)?', 30),
        (b'Y', b'A0>_ ', 90), (b'BYE\r', b'System halted', 30)],
        work / 'install.bin')
    assert b'System installed and verified.' in trace
    assert source.read_bytes() == before
    assert installed.read_bytes()[reserved:] == old_installed[reserved:]
    assert extract(work, installed, 'KEEP.TXT', 7).startswith(sentinel.read_bytes())
    # Record-zero binding is destination-specific; SYSGEN's verified message
    # alone is not used as the reboot oracle.
    boot = work / 'reboot'
    (boot / 'disks').mkdir(parents=True)
    shutil.copy2(installed, boot / 'disks/drivea.dsk')
    for drive in 'bc':
        shutil.copy2(disks / f'drive{drive}.dsk', boot / f'disks/drive{drive}.dsk')
    trace = session(args.simulator, boot / 'disks', [
        (b':VER /BANNER\r', b'A0>_ ', 30),
        (b'BYE\r', b'System halted', 30)], work / 'cold-boot.bin')
    assert trace.count(b'An enhanced CP/M-compatible OS') >= 2
    finish(work, disks, 'sysgen-roundtrip', 'Named 161-record export matches all 160 source records; decline/replace; declined/confirmed reinstall preserves user-7 sentinel and entire filesystem; installed disk cold-boots')


if __name__ == '__main__':
    main()
