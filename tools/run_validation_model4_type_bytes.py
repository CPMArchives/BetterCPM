#!/usr/bin/env python3
"""Native TYPE bytes captured at the public BIOS CONOUT boundary, test RAM only."""
import argparse
import json
import re
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
from test_model4_copy import files
from trs80gp_launch import run
ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'suite', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--analyze-only', action='store_true', help='Analyze retained captures and media without launching the emulator')
    a = p.parse_args()
    w = a.output.resolve()
    report = json.loads((a.baseline / 'report.json').read_text())
    original = a.baseline / report['image']
    assert report['target'] == 'trs80gp' and sha(original) == report['sha256']
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=a.suite, text=True).strip()
    assert revision == 'a9a878fcd2e36698c7e856654a85847a004fdd20'
    if a.analyze_only:
        assert (w / 'executed-runner.py').is_file()
        before_raw = (w / 'b-before.raw').read_bytes(); before_files = files(before_raw)
        emitted = {(key[1][:8].decode().strip() + '.' + key[1][8:].decode().strip()): value[0].split(b'\x1a',1)[0] for key, value in before_files.items()}
        assert json.loads((w / 'hook-forwarding.json').read_text())['status'] == 'PASS'
        analyze(a, w, report, original, before_raw, before_files,
                json.loads((w / 'observations.json').read_text()), w / 'a.dmk', w / 'b.dmk', revision, emitted)
        return
    w.mkdir(parents=True, exist_ok=False)
    raw = extract_raw(original.read_bytes())
    for i in range(DIRECTORY_ENTRIES):
        at = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE + i * 32
        if raw[at] == 0 and raw[at + 1:at + 12] == b'STARTUP SUB': raw[at] = 0xE5
    add_file(raw, 'STARTUP.SUB', b':VER /BANNER\r\n\x1a')
    source = (ROOT / 'tests/fixtures/conformance/returnstate.mac').read_text()
    (w / 'state.asm').write_text(source)
    assembler = Path.home() / 'bin/z80asm'
    state = assemble(assembler, source, w / 'STATE.COM', w / 'state.lst', 0x100)
    add_file(raw, 'STATE.COM', state)
    def assemble_fixture(name, source, origin=0x100):
        (w / (name + '.asm')).write_text(source)
        return assemble(assembler, source, w / (name + '.COM'), w / (name + '.lst'), origin)
    hook_source = (ROOT / 'tests/fixtures/conformance/console-log-hook.mac').read_text()
    hook = assemble_fixture('LOGHOOK', hook_source, 0x9000)
    # Verify ordinary forwarding and overflow guard before trusting the recorder.
    from test_bios import Z80
    for pointer in (0x9200, 0xA1FF, 0xA200):
        for z, carry in ((False, False), (True, False), (False, True), (True, True)):
            cpu = Z80(b''); cpu.mem[0x9000:0x9000 + len(hook)] = hook
            cpu.setword(0x9100, pointer); cpu.setword(0x9103, 0x8000)
            cpu.mem[0x8000] = 0xC9; cpu.mem[0xA200] = 0x5A
            cpu.a = 0x69; cpu.bc = 0x1234; cpu.de = 0x5678; cpu.hl = 0xABCD
            cpu.z = z; cpu.carry = carry
            before = (cpu.a, cpu.bc, cpu.de, cpu.hl, cpu.sp, cpu.z, cpu.carry)
            cpu.run(0x9000)
            assert (cpu.a, cpu.bc, cpu.de, cpu.hl, cpu.sp, cpu.z, cpu.carry) == before
            if pointer < 0xA200:
                assert cpu.mem[pointer] == 0x34 and cpu.word(0x9100) == pointer + 1
            else:
                assert cpu.mem[0xA200] == 0x5A and cpu.mem[0x9102] == 1
    (w / 'hook-forwarding.json').write_text(json.dumps({'status': 'PASS', 'cases': 12, 'scope': 'Z80 fixture ordinary forwarding, Z/C flags, stack, register and capture-boundary guard; full AF saved by PUSH/POP AF'}, indent=2) + '\n')
    payload = '\n'.join(' DB ' + ','.join(str(v) for v in hook[i:i+16]) for i in range(0,len(hook),16))
    starter = f""" ORG 100H
 LD HL,(1)
 LD DE,9
 ADD HL,DE
 LD A,(HL)
 CP 0C3H
 JP NZ,BAD
 INC HL
 LD (9105H),HL
 LD E,(HL)
 INC HL
 LD D,(HL)
 LD (9103H),DE
 LD HL,PAYLOAD
 LD DE,9000H
 LD BC,{len(hook)}
 LDIR
 LD HL,9200H
 LD (9100H),HL
 XOR A
 LD (9102H),A
 LD HL,(9105H)
 LD (HL),0
 INC HL
 LD (HL),90H
 LD DE,GOOD
 LD C,9
 CALL 5
 RET
BAD: LD DE,ERROR
 LD C,9
 CALL 5
 RET
GOOD: DB 'CAPTURE ON',13,10,'$'
ERROR: DB 'CAPTURE INSTALL FAILED',13,10,'$'
PAYLOAD:
{payload}
 END
"""
    add_file(raw, 'HSTART.COM', assemble_fixture('HSTART', starter))
    stop_source = (ROOT / 'tests/fixtures/conformance/console-log-stop.mac').read_text()
    add_file(raw, 'HSTOP.COM', assemble_fixture('HSTOP', stop_source))
    emitted = {'TEXT.TXT': b'TEXT_BYTES_42\r\n', 'EMPTY.TXT': b'',
               'CONTROL.TXT': b'CTRL_BEGIN\x07\x08\x0cCTRL_END\r\n',
               'CUTOFF.TXT': b'BEFORE_1A\r\n',
               'MULTI.TXT': b'MULTI_BEGIN' + b'0123456789ABCDEF' * 15 + b'END\r\n'}
    assert len(emitted['MULTI.TXT']) == 256
    fixtures = [(0, name, content + (b'\x1aMUST_NOT_BE_EMITTED' if name == 'CUTOFF.TXT' else b'')) for name, content in emitted.items()]
    before_raw = install_files(fixtures)
    before_files = files(before_raw)
    (w / 'b-before.raw').write_bytes(before_raw)
    image = w / 'a.dmk'; image.write_bytes(build(bytes(raw)))
    secondary = w / 'b.dmk'; secondary.write_bytes(build(bytes(before_raw)))
    shutil.copy2(__file__, w / 'executed-runner.py')
    cmd = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx', '-d0', str(image), '-d1', str(secondary), '-itime', '15000', '-iw', 'Type TYPE README.TXT for more', '-id', '6000']
    observations = []
    def send(text, wait, expected=None):
        cmd.extend(key_args(text + '\r', delay=25))
        cmd.extend(['-id', '120', '-iw', wait, '-id', '6000', '-it'])
        observations.append({'command': text, 'expected': expected or wait})
    send('B:', 'B0>')
    send('A0:HSTART', 'CAPTURE ON')
    for name in emitted:
        send('TYPE ' + name, 'B0>')
    send('TYPE MISSING.TXT', 'NO FILE')
    send('A0:HSTOP', 'CAPTURE SAVED AND VECTOR RESTORED')
    send('A0:STATE', 'STATE D=01 U=00 TOP=D501')
    send('A:', 'A0>')
    send('STATE', 'STATE D=00 U=00 TOP=D501')
    send('VER', 'BetterCP/M 0.90')
    cmd.append('-ix')
    (w / 'invocation.json').write_text(json.dumps(cmd, indent=2) + '\n')
    (w / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')
    run(cmd, cwd=w, timeout=1800, check=True)
    analyze(a, w, report, original, before_raw, before_files, observations, image, secondary, revision, emitted)


def analyze(a, w, report, original, before_raw, before_files, observations, image, secondary, revision, emitted):
    shutil.copy2(__file__, w / 'analysis-runner.py')
    captures = sorted(w.glob('trs80-text-*.bin'), key=lambda f: int(f.stem.rsplit('-', 1)[1]))
    texts = [screen(f) for f in captures]
    assert len(texts) == len(observations)
    for i, (t, row) in enumerate(zip(texts, observations)):
        (w / f'screen-{i}.txt').write_text(t + '\n')
        assert row['command'] in t and row['expected'] in t, (i, row, t)
        assert 'CAPTURE FAILED' not in t and 'CAPTURE INSTALL FAILED' not in t
    assert 'STATE D=00 U=00 TOP=D501' in texts[-1]
    tail = texts[-1][texts[-1].rindex('A0>VER'):]
    assert 'BetterCP/M 0.90' in tail and tail.rstrip().endswith('A0>')
    after_raw = extract_raw(secondary.read_bytes()); (w / 'b-after.raw').write_bytes(after_raw)
    current = files(after_raw)
    assert set(current) == set(before_files) | {(0, b'CONSOLE BIN')}
    for key, value in before_files.items(): assert current[key] == value
    log = current[0, b'CONSOLE BIN'][0]
    assert log[:8] == b'CONLOG01'
    length = int.from_bytes(log[8:10], 'little'); assert 0 < length <= 4096
    assert len(log) == 128 + ((length + 127) // 128) * 128
    stream = log[128:128+length]; (w / 'console.bin').write_bytes(stream)
    assert b'MUST_NOT_BE_EMITTED' not in stream
    spans = []
    for name, expected in emitted.items():
        # CCP redraws the input line on each keystroke. Only the complete
        # CR/LF-terminated command marks execution, not an earlier redraw.
        command = rb'B0>TYPE ' + re.escape(name.encode()) + rb' *\r\n'
        matches = list(re.finditer(command, stream)); assert len(matches) == 1
        start = matches[0].end()
        end = stream.index(b'B0>', start)
        output = stream[start:end]
        # CR/LF before/after payload belongs to command echo, TYPE and CCP.
        # Every payload byte remains exact, including BEL, BS and FF.
        if expected:
            assert output.count(expected) == 1, (name, output)
            prefix, suffix = output.split(expected)
            assert not prefix.strip(b'\r\n') and not suffix.strip(b'\r\n')
        else: assert not output.strip(b'\r\n'), (name, output)
        spans.append({'file': name, 'expected_hex': expected.hex(), 'observed_hex': output.hex(), 'status': 'PASS'})
    missing_marker = re.search(rb'B0>TYPE MISSING\.TXT *\r\n', stream)
    assert missing_marker
    missing = stream[missing_marker.end():].split(b'B0>',1)[0]
    assert b'NO FILE' in missing
    (w / 'byte-spans.json').write_text(json.dumps(spans, indent=2) + '\n')
    audit = audit_files(original, image, dict(report, included=[f for f in report['included'] if f['name'] != 'STARTUP.SUB']), w)
    assert extract_raw(image.read_bytes())[:20480] == extract_raw(original.read_bytes())[:20480]
    (w / 'diskdefs').write_text('diskdef native-data\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 0\n os 2.2\nend\n')
    for path in ('b-before.raw', 'b-after.raw'):
        result = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'native-data', '-n', str(w / path)], cwd=w, capture_output=True, check=True)
        (w / (path + '.fsck.txt')).write_bytes(result.stdout + result.stderr)
    result = subprocess.run(['fsck.cpm', '-T', 'raw,pcw800', '-f', 'bettercpm-default', '-n', str(w / 'file-audit/after.raw')], cwd=w / 'file-audit', capture_output=True, check=True)
    (w / 'file-audit/filesystem.txt').write_bytes(result.stdout + result.stderr)
    assert sha(original) == report['sha256']
    (w / 'result.json').write_text(json.dumps({'status': 'PASS', 'card': '0577', 'baseline_sha256': sha(original), 'suite_revision': revision, 'procedure_sha256': sha(a.suite / 'suite/src/ECOTEST.ASM'), 'runner_sha256': sha(w / 'executed-runner.py'), 'analyzer_sha256': sha(w / 'analysis-runner.py'), 'emulator_sha256': sha(DEFAULT_EMULATOR), 'console_sha256': sha(w / 'console.bin'), 'console_bytes': length, 'file_audit': audit, 'scope': 'native TYPE bytes at BIOS CONOUT with bounded test-only RAM hook, restored before dump; text, empty, BEL/BS/FF, 1Ah cutoff, two physical records and missing file; no TAB claim or arbitrary direct-hardware output capture'}, indent=2) + '\n')
    print('PASS native TYPE byte stream', w)


if __name__ == '__main__': main()
