#!/usr/bin/env python3
"""Validate shipped native DUP on retained disposable physical-media fixtures."""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from add_cpm_file_to_dmk import add_file, extract_raw
from build_montezuma_extended_790k import RAW_SIZE, build, crc16
from run_trs80_command import DEFAULT_EMULATOR, key_args
from run_validation_model4 import audit_files, sha
from test_dup_operations import probe
from test_sysgen_install import screen
from trs80gp_launch import run


def sectors(image, count=160, check_crc=True):
    size = int.from_bytes(image[2:4], 'little')
    result = {}
    for track in range(count):
        base = 16 + track * size
        data = image[base:base + size]
        ids = []
        for slot in range(0, 128, 2):
            at = int.from_bytes(data[slot:slot + 2], 'little') & 0x3FFF
            if not at:
                break
            assert data[at:at + 3] == bytes((0xFE, track // 2, track % 2))
            sid, code = data[at + 3:at + 5]
            assert code == 2
            assert data[at + 5:at + 7] == crc16(b'\xa1' * 3 + data[at:at + 5]).to_bytes(2, 'big')
            mark = data.find(b'\xa1\xa1\xa1\xfb', at + 7)
            assert mark >= 0
            payload = data[mark + 4:mark + 516]
            if check_crc:
                assert data[mark + 516:mark + 518] == crc16(data[mark:mark + 516]).to_bytes(2, 'big')
            result[track, sid] = payload
            ids.append(sid)
        assert sorted(ids) == list(range(1, 11))
    return result


def patterned_source():
    image = bytearray(build(b'\xe5' * RAW_SIZE))
    size = int.from_bytes(image[2:4], 'little')
    bad_crc = None
    for track in range(4):
        base = 16 + track * size
        for slot in range(0, 20, 2):
            at = base + (int.from_bytes(image[base + slot:base + slot + 2], 'little') & 0x3FFF)
            mark = image.find(b'\xa1\xa1\xa1\xfb', at + 7)
            sid = image[at + 3]
            image[mark + 4:mark + 516] = bytes((track * 41 + sid * 3 + k + 19 * (k // 128)) % 256 for k in range(512))
            image[mark + 516:mark + 518] = crc16(image[mark:mark + 516]).to_bytes(2, 'big')
            if track == 0 and sid == 3:
                bad_crc = mark + 516
    assert bad_crc is not None
    return bytes(image), bad_crc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--group', choices=('all', 'decline', 'format', 'copy', 'crc'), default='all')
    args = parser.parse_args()
    report = json.loads((args.baseline / 'report.json').read_text())
    original = args.baseline / report['image']
    assert report['target'] == 'trs80gp' and sha(original) == report['sha256']
    args.output.mkdir(parents=True, exist_ok=True)
    results = []

    def prepare(label, helper=False):
        work = Path(tempfile.mkdtemp(prefix=label + '-', dir=args.output.resolve()))
        shutil.copy2(__file__, work / 'executed-runner.py')
        raw = extract_raw(original.read_bytes())
        if helper:
            # Public binding calls only; no shipped executable is replaced.
            add_file(raw, 'DSET.COM', probe(work, 'copy'))
        image = work / 'a.dmk'
        image.write_bytes(build(bytes(raw)))
        return work, image

    def command(work, image):
        cmd = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx',
               '-d0', str(image), '-d1', str(work / 'b.dmk'), '-d2', str(work / 'c.dmk'),
               '-itime', '15000', '-iw', 'Type TYPE README.TXT for more', '-id', '6000']
        # The default monitor pair leaves 50K; DUP's documented requirement is
        # 51K. Unload in dependency order and retain an explicit 53K witness.
        cmd += key_args('RSX UNLOAD ADM3A\r') + ['-id', '6000']
        cmd += key_args('RSX UNLOAD M4SCRN\r') + ['-id', '6000']
        # LIST prints its result before WBOOT reconstructs the command
        # environment. Use the same settled-return interval as other native
        # application runners before sending the next command.
        cmd += key_args('RSX LIST\r') + ['-iw', 'TPA available: 53K', '-id', '6000', '-it']
        return cmd

    def launch(work, cmd):
        (work / 'invocation.json').write_text(json.dumps(cmd, indent=2) + '\n')
        run(cmd, cwd=work, timeout=900)
        captures = sorted(work.glob('trs80-text-*.bin'), key=lambda p: int(p.stem.rsplit('-', 1)[1]))
        memory = screen(captures[0])
        (work / 'memory.txt').write_text(memory + '\n')
        assert 'No RSXs loaded' in memory and 'TPA available: 53K' in memory
        texts = [screen(path) for path in captures[1:]]
        assert not any('BINDING TEST FAIL' in text or 'DUP needs 51K' in text for text in texts)
        for i, text in enumerate(texts):
            (work / f'screen-{i}.txt').write_text(text + '\n')
        return texts

    def finish(work, image, label, detail):
        source_audit = audit_files(original, image, report, work)
        assert extract_raw(image.read_bytes())[:20480] == extract_raw(original.read_bytes())[:20480]
        check = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'bettercpm-default', '-n',
                                str(work / 'file-audit/after.raw')], cwd=work / 'file-audit',
                               capture_output=True, text=True)
        (work / 'file-audit/filesystem.txt').write_text(check.stdout + check.stderr)
        assert check.returncode == 0 and sha(original) == report['sha256']
        result = dict(status='PASS', case=label, detail=detail,
                      baseline_sha256=report['sha256'], emulator_sha256=sha(DEFAULT_EMULATOR),
                      runner_sha256=sha(Path(__file__)), source_file_audit=source_audit,
                      scope='Shipped native DUP with disposable emulator media; B/C patterned fixtures are not valid CP/M filesystems; no physical-hardware claim')
        (work / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        results.append(result)
        (args.output / ('summary-' + args.group + '.json')).write_text(json.dumps(results, indent=2) + '\n')
        print(label, 'PASS', work, flush=True)

    groups = ('decline', 'format', 'copy', 'crc') if args.group == 'all' else (args.group,)
    for group in groups:
        work, image = prepare(group, helper=group != 'format')
        source, bad_crc = patterned_source()
        if group == 'crc':
            corrupt = bytearray(source)
            corrupt[bad_crc] ^= 1
            source = bytes(corrupt)
        target = build(b'\xcc' * RAW_SIZE)
        (work / 'b.dmk').write_bytes(source)
        (work / 'c.dmk').write_bytes(target)
        cmd = command(work, image)
        if group != 'format':
            cmd += key_args('DSET\r') + ['-iw', 'BINDING TEST PASS', '-id', '6000']
        if group == 'decline':
            cmd += key_args('DUP /FORMAT A:\r') + ['-iw', 'protected system disk', '-id', '6000', '-it']
            cmd += key_args('DUP /FORMAT B:\r') + ['-id', '12000', '-it']
            cmd += key_args('N', delay=60) + ['-id', '6000']
            cmd += key_args('DUP /COPY B: C:\r') + ['-id', '12000', '-it']
            cmd += key_args('N', delay=60) + ['-id', '6000']
            cmd += key_args('DSET CHECK\r') + ['-id', '12000', '-it', '-ix']
            texts = launch(work, cmd)
            assert len(texts) == 4 and 'protected system disk' in texts[0]
            assert 'Format this disk? [Y/N]' in texts[1], texts[1]
            assert 'Destination contents will be erased. [Y/N]' in texts[2], texts[2]
            assert 'BINDING TEST PASS' in texts[3] and 'A0>' in texts[3]
            assert (work / 'b.dmk').read_bytes() == source and (work / 'c.dmk').read_bytes() == target
            finish(work, image, group, 'Boot physical drive protected; declined FORMAT/COPY preserve both raw DMKs; destination binding restored; normal warm return')
        elif group == 'format':
            # Interactive FORMAT, then direct CHECK, across the full default disk.
            cmd += key_args('DUP\r') + ['-iw', 'Your choice:'] + key_args('A')
            cmd += ['-iw', 'Your choice:'] + key_args('B') + ['-iw', '[Y/N]', '-it']
            cmd += key_args('Y', delay=60) + ['-iw', 'Format complete.', '-it']
            cmd += key_args('\r') + ['-iw', 'Your choice:'] + key_args('\x03') + ['-id', '6000']
            cmd += key_args('DUP /CHECK B:\r') + ['-iw', 'Check complete.', '-id', '6000', '-it', '-ix']
            texts = launch(work, cmd)
            assert len(texts) == 3 and 'Tracks written and verified: 00160' in texts[1]
            assert 'Unreadable sectors: 00000' in texts[2] and 'A0>' in texts[2]
            decoded = sectors((work / 'b.dmk').read_bytes())
            assert len(decoded) == 1600 and all(data == b'\xe5' * 512 for data in decoded.values())
            assert (work / 'c.dmk').read_bytes() == target
            finish(work, image, group, 'Interactive full 160-surface format; independently checked all 1600 IDs, sizes, header/data CRCs and erased payloads; direct CHECK clean')
        else:
            cmd += key_args('DUP /COPY B: C:\r') + ['-iw', '[Y/N]']
            cmd += key_args('Y', delay=60)
            cmd += ['-iw', 'CRC error' if group == 'crc' else 'Copy complete; destination verified.', '-id', '6000', '-it']
            cmd += key_args('DSET CHECK\r') + ['-iw', 'BINDING TEST PASS', '-id', '6000', '-it']
            cmd += key_args('DUP /CHECK B:\r') + ['-iw', 'Check complete.', '-id', '6000', '-it', '-ix']
            texts = launch(work, cmd)
            assert len(texts) == 3 and 'BINDING TEST PASS' in texts[1]
            assert 'A0>' in texts[-1] and (work / 'b.dmk').read_bytes() == source
            actual = (work / 'c.dmk').read_bytes()
            if group == 'copy':
                assert 'Unreadable sectors: 00000' in texts[-1]
                assert sectors(actual, 4) == sectors(source, 4)
                size = int.from_bytes(target[2:4], 'little')
                assert actual[16 + 4 * size:] == target[16 + 4 * size:]
                detail = 'Direct COPY reformats mismatched destination, verifies patterned payload across two cylinders/both sides including reserved track, preserves remaining tracks and source, restores binding; CHECK clean'
            else:
                assert 'sector ID 3' in texts[0] and 'Copy complete' not in texts[0]
                assert 'Unreadable sectors: 00001' in texts[-1]
                assert actual == target, 'First-track read failure changed destination'
                detail = 'Bad sector-3 CRC aborts COPY before writing; target/source unchanged; binding restored; CHECK counts exactly one bad sector and returns'
            finish(work, image, group, detail)


if __name__ == '__main__':
    main()
