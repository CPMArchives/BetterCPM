#!/usr/bin/env python3
"""Native shipped ED setup/protection and controlled rename-failure recovery."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw, add_file, FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE, DIRECTORY_ENTRIES
from build_source_disk import install_files, BLOCK_COUNT
from build_montezuma_extended_790k import build
from build_ccp import assemble
from run_validation_model4 import audit_files
from run_validation_returning import sha
from run_trs80_command import DEFAULT_EMULATOR, key_args
from test_sysgen_install import screen
from test_model4_copy import files
from system_layout import LAYOUT
from trs80gp_launch import run


def key(user, name):
    stem, ext = name.split('.')
    return user, (stem.ljust(8) + ext.ljust(3)).encode()


def symbols(path):
    return {m[2]: int(m[1], 16) for m in re.finditer(
        r'^([0-9a-f]{4})\s+.*?\b(FH_MATCH|FH_FAIL):', path.read_text(), re.M | re.I)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'build-root', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--group', choices=('setup', 'rename', 'directory-full', 'disk-full'), required=True)
    a = p.parse_args()
    w = a.output.resolve(); w.mkdir(parents=True, exist_ok=False)
    report = json.loads((a.baseline / 'report.json').read_text())
    original = a.baseline / report['image']
    assert report['target'] == 'trs80gp' and sha(original) == report['sha256']
    ed = a.build_root / 'build/utilities/ED.COM'
    assert sha(ed) == next(f['sha256'] for f in report['included'] if f['name'] == 'ED.COM')
    raw = extract_raw(original.read_bytes())
    for i in range(DIRECTORY_ENTRIES):
        at = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE + i * 32
        if raw[at] == 0 and raw[at + 1:at + 12] == b'STARTUP SUB': raw[at] = 0xE5
    add_file(raw, 'STARTUP.SUB', b':VER /BANNER\r\n\x1a')
    assembler = Path.home() / 'bin/z80asm'
    def program(name, source, origin=0x100):
        (w / (name + '.asm')).write_text(source)
        data = assemble(assembler, source, w / (name + '.COM'), w / (name + '.lst'), origin)
        return data
    state = program('STATE', """ ORG 100H
 LD C,25
 CALL 5
 OR A
 JR NZ,BAD
 LD C,32
 LD E,255
 CALL 5
 CP 5
 JR NZ,BAD
 LD HL,(6)
 LD DE,0D501H
 OR A
 SBC HL,DE
 JR NZ,BAD
 LD DE,GOOD
 JR SHOW
BAD: LD DE,ERROR
SHOW: LD C,9
 CALL 5
 JP 0
GOOD: DB 'CALLER A5 AND 53K PASS',13,10,'$'
ERROR: DB 'CALLER STATE FAILED',13,10,'$'
 END
""")
    add_file(raw, 'STATE.COM', state)
    hooks = {}
    if a.group == 'rename':
        prefix = (a.build_root / 'build/bdos/bdos.bin').read_bytes()[:3]
        assert prefix == bytes.fromhex('79d6b0'), 'unsupported BDOS dispatcher prefix'
        for nth in (1, 2):
            hook = program('HOOKBIN' + str(nth), f""" ORG 9000H
 LD A,C
 CP 23
 JR NZ,NORMAL
FH_MATCH: LD A,(COUNT)
 INC A
 LD (COUNT),A
 CP {nth}
 JR NZ,NORMAL
FH_FAIL: LD A,255
 LD HL,255
 OR A
 RET
NORMAL: LD A,C
 SUB 176
 JP {LAYOUT['BDOS'] + 3}
COUNT: DB 0
 END
""", 0x9000)
            syms = symbols(w / ('HOOKBIN' + str(nth) + '.lst'))
            hooks[nth] = syms
            installer = program('HOOK' + str(nth), f""" ORG 100H
 LD HL,{LAYOUT['BDOS']}
 LD A,(HL)
 CP 079H
 JR Z,INSTALL
 CP 0C3H
 JR NZ,BAD
 INC HL
 LD E,(HL)
 INC HL
 LD D,(HL)
 LD HL,09000H
 OR A
 SBC HL,DE
 JR NZ,BAD
INSTALL: LD HL,PAYLOAD
 LD DE,09000H
 LD BC,{len(hook)}
 LDIR
 LD HL,{LAYOUT['BDOS']}
 LD (HL),0C3H
 INC HL
 LD (HL),0
 INC HL
 LD (HL),090H
 LD DE,GOOD
 JR SHOW
BAD: LD DE,ERROR
SHOW: LD C,9
 CALL 5
 JP 0
GOOD: DB 'RENAME HOOK {nth} INSTALLED',13,10,'$'
ERROR: DB 'HOOK INSTALL FAILED',13,10,'$'
PAYLOAD: DB {','.join(str(b) for b in hook)}
 END
""")
            add_file(raw, 'HOOK' + str(nth) + '.COM', installer)
        assert hooks[1] == hooks[2]
    source_names = (('CLASH', 'SYSFILE', 'ROFILE') if a.group == 'setup'
                    else ('R1', 'R2') if a.group == 'rename' else ('FULL',))
    fixtures = []
    for stem in source_names:
        fixtures.extend([(7, stem + '.TXT', b'ORIGINAL\r\n\x1a'),
                         (0, stem + '.TXT', b'USER ZERO SENTINEL\r\n\x1a')])
    if a.group == 'setup':
        fixtures.extend([(3, 'CLASH.TXT', b'DESTINATION\r\n\x1a'),
                         (7, 'CLASH.BAK', b'SOURCE BACKUP\x1a'),
                         (3, 'CLASH.BAK', b'DEST BACKUP\x1a'),
                         (3, 'CLASH.$$$', b'STALE WORK\x1a'),
                         (7, 'SYSFILE.BAK', b'SYS BACKUP\x1a'),
                         (7, 'SYSFILE.$$$', b'SYS WORK\x1a')])
    if a.group == 'directory-full':
        fixtures.extend((0, f'D{n:03}.DAT', b'') for n in range(126))
    elif a.group == 'disk-full':
        # Two directory blocks and two single-block source/sentinel files.
        fixtures.append((0, 'FILLER.BIN', bytes([0xA5]) * ((BLOCK_COUNT - 4) * 2048)))
    braw = bytearray(install_files(fixtures))
    live = [braw[i:i + 32] for i in range(0, 4096, 32) if braw[i] < 32]
    if a.group == 'directory-full':
        assert len(live) == DIRECTORY_ENTRIES
    elif a.group == 'disk-full':
        used = {0, 1}
        for row in live:
            used.update(int.from_bytes(row[i:i + 2], 'little') for i in range(16, 32, 2))
        assert used == set(range(BLOCK_COUNT)), 'fixture is not allocation-full'
    if a.group == 'setup':
        for at in range(0, 4096, 32):
            if braw[at] != 7: continue
            if braw[at + 1:at + 12] == b'SYSFILE TXT': braw[at + 10] |= 128
            if braw[at + 1:at + 12] == b'ROFILE  TXT': braw[at + 9] |= 128
    before = files(braw)
    (w / 'b-before.raw').write_bytes(braw)
    image = w / 'a.dmk'; image.write_bytes(build(bytes(raw)))
    secondary = w / 'b.dmk'; secondary.write_bytes(build(bytes(braw)))
    shutil.copy2(__file__, w / 'executed-runner.py')
    cmd = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx',
           '-d0', str(image), '-d1', str(secondary), '-itime', '15000',
           '-iw', 'Type TYPE README.TXT for more', '-id', '6000']
    if hooks: cmd += ['-tr', ','.join(f'{v:x}' for v in hooks[1].values())]
    def send(text, wait, delay=120, key_delay=12):
        cmd.extend(key_args(text, delay=key_delay))
        cmd.extend(['-id', '120', '-it', '-iw', wait, '-id', str(delay), '-it'])
    send('A5:\r', 'A5>', delay=6000)
    if a.group == 'setup':
        send('A0:ED B7:CLASH.TXT B3:\r', 'FILE EXISTS, ERASE IT', delay=6000)
        send('A0:STATE\r', 'CALLER A5 AND 53K PASS', delay=6000)
        send('A0:ED B7:SYSFILE.TXT\r', '"SYSTEM" FILE NOT ACCESSIBLE', delay=6000)
        send('A0:STATE\r', 'CALLER A5 AND 53K PASS', delay=6000)
        send('A0:ED B7:ROFILE.TXT\r', '** FILE IS READ/ONLY **')
        send('INEW\x1a\r', '*', key_delay=60)
        send('E\r', 'File R/O', key_delay=60)
        send('\r', 'A5>', delay=6000)
        send('A0:STATE\r', 'CALLER A5 AND 53K PASS', delay=6000)
    elif a.group == 'rename':
        for nth in (1, 2):
            send(f'A0:HOOK{nth}\r', f'RENAME HOOK {nth} INSTALLED', delay=6000)
            # Remove the previous editor prompt/diagnostic before waiting for
            # a fresh '*' from this invocation; trs80gp matches screen history.
            send('CLS\r', 'A5>', delay=6000)
            send(f'A0:ED B7:R{nth}.TXT\r', '*')
            send('INEW\x1a\r', '*', delay=6000, key_delay=60)
            send('E\r', 'Rename failed. Edited text retained in work file.', delay=6000, key_delay=60)
            send('A0:STATE\r', 'CALLER A5 AND 53K PASS', delay=6000)
    else:
        send('A0:ED B7:FULL.TXT\r', 'DISK OR DIRECTORY FULL' if a.group == 'directory-full' else '*', delay=6000)
        if a.group == 'disk-full':
            send('INEW\x1a\r', '*', key_delay=60)
            send('E\r', 'DISK OR DIRECTORY FULL', delay=6000, key_delay=60)
        send('A0:STATE\r', 'CALLER A5 AND 53K PASS', delay=6000)
    cmd.append('-ix')
    (w / 'invocation.json').write_text(json.dumps(cmd, indent=2) + '\n')
    run(cmd, cwd=w, timeout=1200, check=True)
    captures = sorted(w.glob('trs80-text-*.bin'), key=lambda f: int(f.stem.rsplit('-', 1)[1]))
    texts = [screen(f) for f in captures]
    for i, text in enumerate(texts): (w / f'screen-{i}.txt').write_text(text + '\n')
    assert 'A0:STATE' in texts[-1]
    final_state = texts[-1][texts[-1].rindex('A0:STATE'):]
    assert 'CALLER A5 AND 53K PASS' in final_state
    assert not any('CALLER STATE FAILED' in t or 'HOOK INSTALL FAILED' in t for t in texts)
    after_raw = extract_raw(secondary.read_bytes()); (w / 'b-after.raw').write_bytes(after_raw)
    current = files(after_raw)
    expected = dict(before)
    if a.group == 'setup':
        expected[key(7, 'ROFILE.$$$')] = None
        assert current[key(7, 'ROFILE.$$$')][0].split(b'\x1a')[0] == b'NEWORIGINAL\r\n'
        required = ('FILE EXISTS, ERASE IT', '"SYSTEM" FILE NOT ACCESSIBLE', 'File R/O')
    elif a.group == 'rename':
        expected.pop(key(7, 'R2.TXT'))
        expected[key(7, 'R2.BAK')] = before[key(7, 'R2.TXT')]
        for stem in ('R1', 'R2'):
            expected[key(7, stem + '.$$$')] = None
            assert current[key(7, stem + '.$$$')][0].split(b'\x1a')[0] == b'NEWORIGINAL\r\n'
        required = ('Rename failed. Edited text retained in work file.',)
    else:
        if a.group == 'disk-full':
            expected[key(7, 'FULL.$$$')] = None
            assert current[key(7, 'FULL.$$$')][0] == b'', 'failed write produced accepted data'
        else:
            assert bytes(after_raw) == bytes(braw), 'failed create modified the directory-full disk'
        required = ('DISK OR DIRECTORY FULL',)
    assert set(current) == set(expected), (set(current), set(expected))
    for k, value in expected.items():
        if value is not None:
            assert current[k][0] == value[0], k
            if k[1].endswith(b'TXT'): assert current[k][1] == value[1], k
    for diagnostic in required: assert any(diagnostic in t for t in texts), diagnostic
    fault_trace = None
    if hooks:
        trace = (w / 'bus-trace-0.txt').read_text()
        hits = {name: re.findall(r'^.*@' + f'{address:x}' + r' z ex.*$', trace, re.M | re.I)
                for name, address in hooks[1].items()}
        assert len(hits['FH_MATCH']) == 3 and len(hits['FH_FAIL']) == 2, hits
        fault_trace = {name: len(rows) for name, rows in hits.items()}
    audit = audit_files(original, image, dict(report, included=[f for f in report['included'] if f['name'] != 'STARTUP.SUB']), w)
    assert extract_raw(image.read_bytes())[:20480] == extract_raw(original.read_bytes())[:20480]
    (w / 'diskdefs').write_text('diskdef native-data\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 0\n os 2.2\nend\n')
    for disk, folder, fmt, transport in ((w / 'b-after.raw', w, 'native-data', 'raw,pcw800'),
                                        (w / 'file-audit/after.raw', w / 'file-audit', 'bettercpm-default', 'raw,pcw800')):
        result = subprocess.run(['fsck.cpm', '-T', transport, '-f', fmt, '-n', str(disk)], cwd=folder, capture_output=True, check=True)
        (folder / 'filesystem.txt').write_bytes(result.stdout + result.stderr)
    assert sha(original) == report['sha256']
    (w / 'result.json').write_text(json.dumps({'status': 'PASS', 'group': a.group,
        'baseline_sha256': report['sha256'], 'ed_sha256': sha(ed), 'runner_sha256': sha(w / 'executed-runner.py'),
        'emulator_sha256': sha(DEFAULT_EMULATOR), 'file_audit': audit, 'fault_trace': fault_trace,
        'scope': 'native shipped ED diagnostics, file preservation and caller A5 return; rename group uses a temporary RAM BDOS interception with no TPA boundary change; not physical disk-error qualification'}, indent=2) + '\n')
    print('PASS native ED recovery', a.group, w)


if __name__ == '__main__': main()
