#!/usr/bin/env python3
"""Verify Model 4 DUP preserves attributes in a bounded two-cylinder fixture."""
import argparse
import hashlib
import json
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build, RAW_SIZE
from run_trs80_command import DEFAULT_EMULATOR
from test_disk_utilities import medium, keys
import test_dup_operations
from test_sysgen_install import screen
from trs80gp_launch import run as run_trs80gp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    # Match the DMK builder's logical sector order. Retain the existing
    # two-cylinder binding ABI and its independent restoration checker.
    original = test_dup_operations.binding
    def binding(physical, sides):
        row = bytearray(original(physical, sides))
        row[20:30] = bytes((1,3,5,7,9,2,4,6,8,10))
        return bytes(row)
    test_dup_operations.binding = binding
    try:
        setup = test_dup_operations.probe(report, 'same')
    finally:
        test_dup_operations.binding = original
    system = medium((('DSET.COM', setup),))
    raw = bytearray([0xE5]) * RAW_SIZE
    # SPT=40, OFF=1, 1 KiB blocks, 32 entries, byte block numbers.
    directory = 40 * 128
    limit = 2 * 2 * 40 * 128
    for mask in range(8):
        entry = bytearray(32)
        entry[1:9] = f'ATTR{mask}   '.encode()
        entry[9:12] = bytes(ord(c) | (128 if mask & (1 << n) else 0)
                            for n,c in enumerate('DAT'))
        entry[15] = 1
        entry[16] = mask + 1
        raw[directory+mask*32:directory+(mask+1)*32] = entry
        at = directory + (mask + 1) * 1024
        raw[at:at+128] = bytes((mask * 19 + i) & 255 for i in range(128))
    source = build(bytes(raw))
    target_raw = bytearray([0xE5]) * RAW_SIZE
    target_raw[:limit] = bytes([0xA5]) * limit
    target = build(bytes(target_raw))
    for name, image in [('system.dmk', system), ('source.dmk', source),
                        ('target.dmk', target), ('target-before.dmk', target)]:
        (report / name).write_bytes(image)
    steps = [('DSET\r',3000), ('DUP\r',3000), ('B',1000), ('B',1000),
             ('C',1000), ('Y',15000), ('\r',1000), ('\x03',2000),
             ('DSET CHECK\r',3000), ('DUP\r',3000), ('C',1000),
             ('C',6000), ('\r',1000), ('\x03',2000), ('DSET CHECK\r',3000)]
    invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo',
        '-d0', str(report / 'system.dmk'), '-d1', str(report / 'source.dmk'),
        '-d2', str(report / 'target.dmk'), '-id', '3000']
    for text, delay in steps:
        invocation += keys(text) + ['-id',str(delay),'-it']
    invocation += ['-ix']
    (report / 'invocation.json').write_text(json.dumps(invocation,indent=2)+'\n')
    run_trs80gp(invocation, cwd=report, check=True, timeout=110)
    texts = []
    captures = sorted(report.glob('trs80-text-*.bin'),
                      key=lambda p: int(p.stem.rsplit('-',1)[1]))
    for capture in captures:
        text = screen(capture)
        capture.with_suffix('.txt').write_text(text)
        texts.append(text)
    assert len(texts) == len(steps), len(texts)
    for index in (0,8,14):
        assert 'BINDING TEST PASS' in texts[index], texts[index]
    assert 'Copy complete; destination verified.' in texts[5], texts[5]
    assert 'Unreadable sectors: 00000' in texts[11], texts[11]
    assert (report / 'system.dmk').read_bytes() == system
    assert (report / 'source.dmk').read_bytes() == source
    after = extract_raw((report / 'target.dmk').read_bytes())
    assert after[:limit] == raw[:limit], 'copied metadata or payload differs'
    assert after[limit:] == target_raw[limit:], 'copy exceeded bounded geometry'
    # A separate CHECK-only launch proves the operation itself writes no media.
    before = [(report / name).read_bytes() for name in ('system.dmk','source.dmk','target.dmk')]
    check = report / 'check-only'
    check.mkdir()
    check_invocation = invocation[:invocation.index('-id')] + ['-id','3000']
    for text, delay in [('DSET\r',3000),('DUP\r',3000),('C',1000),('C',6000),
                        ('\r',1000),('\x03',2000)]:
        check_invocation += keys(text) + ['-id',str(delay),'-it']
    check_invocation += ['-ix']
    (check / 'invocation.json').write_text(json.dumps(check_invocation,indent=2)+'\n')
    run_trs80gp(check_invocation,cwd=check,check=True,timeout=55)
    check_texts = [screen(capture) for capture in check.glob('trs80-text-*.bin')]
    assert any('Unreadable sectors: 00000' in text for text in check_texts), check_texts
    assert [(report / name).read_bytes() for name in ('system.dmk','source.dmk','target.dmk')] == before
    (report / 'evidence.json').write_text(json.dumps({'result':'PASS',
        'attributes':list(range(8)), 'copied_bytes':limit, 'cylinders':2,
        'source_sha256':hashlib.sha256(source).hexdigest(),
        'copied_region_sha256':hashlib.sha256(after[:limit]).hexdigest(),
        'emulator_sha256':hashlib.sha256(DEFAULT_EMULATOR.read_bytes()).hexdigest()},indent=2)+'\n')
    print('PASS: Model 4 DUP attributes/payload preserved, binding restored, CHECK writes no media')


if __name__ == '__main__':
    main()
