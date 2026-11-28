#!/usr/bin/env python3
"""Cold boot a private Cromemco 16FDC diagnostic disk and verify guest/host sector I/O."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pty
import select
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src/platform/cromemco'
IMAGE_BYTES = 77 * 26 * 128


def digest(data):
    return hashlib.sha256(data).hexdigest()


def offset(track, sector):
    return (track * 26 + sector - 1) * 128


def assemble(assembler, source, out, origin):
    # Deliberately independent of the OS layout/checked build machinery.
    text = source
    for name in ('hardware', 'console', 'fdc'):
        text = text.replace(f'        INCLUDE {name}.inc', (SOURCE / f'{name}.inc').read_text())
    path = out.with_suffix('.asm')
    path.write_text(text, encoding='ascii')
    subprocess.run([str(assembler), '-fb', f'-o{out}', f'-l{out.with_suffix(".lst")}', str(path)], check=True)
    data = out.read_bytes()
    if origin and len(data) > origin and data[:origin] == bytes(origin):
        data = data[origin:]
        out.write_bytes(data)
    return data


def run(simulator, work, cpu='-z'):
    master, slave = pty.openpty()
    command = [str(simulator), cpu, '-R', '-M1', '-f0', '-r', str(simulator.parent / 'roms'), '-c', str(work / 'system.conf'), '-d', str(work / 'disks')]
    process = subprocess.Popen(command, cwd=work, stdin=slave, stdout=slave, stderr=slave)
    os.close(slave)
    transcript = bytearray()
    supplied_input = False
    deadline = time.monotonic() + 20
    try:
        while time.monotonic() < deadline:
            if select.select([master], [], [], 0.1)[0]:
                try:
                    block = os.read(master, 65536)
                except OSError:
                    process.wait(timeout=2)
                    break
                if not block:
                    process.wait(timeout=2)
                    break
                transcript.extend(block)
                if not supplied_input and b'SEND a' in transcript:
                    os.write(master, b'a')
                    supplied_input = True
            if process.poll() is not None:
                # Drain any remaining output before closing the PTY.
                while select.select([master], [], [], 0)[0]:
                    try:
                        block = os.read(master, 65536)
                    except OSError:
                        break
                    if not block:
                        break
                    transcript.extend(block)
                break
        if process.poll() is None:
            raise RuntimeError('Cromemco diagnostic timed out: ' + transcript.decode(errors='replace'))
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        os.close(master)
        (work / 'transcript.txt').write_bytes(transcript)
    return process.returncode, transcript.decode(errors='replace'), command


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--simulator', type=Path, required=True)
    p.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    boot = assemble(a.assembler.resolve(), (SOURCE / 'boot.mac').read_text(), out / 'boot.bin', 0x80)
    probe = assemble(a.assembler.resolve(), (SOURCE / 'probe.mac').read_text(), out / 'probe.bin', 0x1000)
    if len(boot) != 128 or len(probe) > 1024:
        raise ValueError(f'bootstrap/stage-two size: {len(boot)}/{len(probe)}')
    disks = out / 'disks'
    disks.mkdir()
    (disks / 'disk.map').write_text(''.join(f'drive{letter}.dsk\n' for letter in 'abcd'))
    originals = []
    for drive, letter in enumerate('abcd'):
        raw = bytearray(b'\xe5' * IMAGE_BYTES)
        raw[offset(2, 1):offset(2, 1)+128] = bytes([0x40+drive]) * 128
        raw[offset(76, 26):offset(76, 26)+128] = bytes([0x80+drive]) * 128
        if drive == 0:
            raw[:128] = boot
            raw[128:1152] = probe.ljust(1024, b'\x00')
        originals.append(bytes(raw))
        (disks / f'drive{letter}.dsk').write_bytes(raw)
    config = ('fp_port 10\n[MEMORY 1]\nram 0,256\n'
              'rom 0xc0,32,rdos252.hex\nboot 0xc000\n')
    (out / 'system.conf').write_text(config)
    code, transcript, command = run(a.simulator.resolve(), out)
    required = ('CROMEMCO Z80 16FDC BOOT', 'ROM RECLAIM AND UPPER 16K RAM PASS', 'CONSOLE INPUT PASS',
                'FOUR DRIVE READ WRITE PASS', 'INVALID ADDRESS PASS', 'CROMEMCO PROBE PASS')
    if code or any(text not in transcript for text in required) or 'CROMEMCO PROBE FAIL' in transcript:
        raise AssertionError(transcript)
    images = []
    for drive, letter in enumerate('abcd'):
        actual = (disks / f'drive{letter}.dsk').read_bytes()
        expected = bytearray(originals[drive])
        expected[offset(3, 2):offset(3, 2)+128] = bytes([0xc0+drive]) * 128
        if actual != expected:
            raise AssertionError(f'drive {letter}: unexpected whole-image differences')
        images.append({'drive': letter, 'sha256': digest(actual)})
    fault_results = []
    for fault in ('missing', 'wrong-size', 'read-only'):
        work = out / fault
        work.mkdir()
        (work / 'disks').mkdir()
        (work / 'system.conf').write_text(config)
        # Cold boot the same firmware with a diagnostic stage that requires
        # errors; a green normal-media run cannot satisfy these cases.
        fault_code = '''        LD A,1
        LD DE,00201H
        LD HL,02000H
        CALL CM_READ
        JP {read_condition},CM_FAIL
        LD A,1
        LD HL,02000H
        CALL CM_WRITE
        JP Z,CM_FAIL
        LD HL,CM_FMSG
        CALL CM_STRING
        JP CM_EXIT
CM_FMSG: DB 'MEDIA ERROR PASS',13,10,0
'''.format(read_condition='NZ' if fault == 'read-only' else 'Z')
        source = (SOURCE / 'probe.mac').read_text().replace('; @fault-test@', fault_code)
        payload = assemble(a.assembler.resolve(), source, work / 'probe.bin', 0x1000)
        if len(payload) > 1024:
            raise ValueError('fault diagnostic exceeds stage-two capacity')
        system = bytearray(originals[0])
        system[128:1152] = payload.ljust(1024, b'\x00')
        (work / 'disks/drivea.dsk').write_bytes(system)
        target = work / 'disks/driveb.dsk'
        if fault != 'missing':
            target.write_bytes(originals[1] if fault == 'read-only' else b'\xe5' * 127)
        if fault == 'read-only':
            target.chmod(0o444)
        (work / 'disks/disk.map').write_text(''.join(f'drive{letter}.dsk\n' for letter in 'ab') + '\n\n')
        expected = {p.name: p.read_bytes() for p in (work / 'disks').iterdir()}
        try:
            status, text, fault_command = run(a.simulator.resolve(), work)
            if status or 'MEDIA ERROR PASS' not in text or 'CROMEMCO PROBE FAIL' in text:
                raise AssertionError(fault + ': ' + text)
            actual = {p.name: p.read_bytes() for p in (work / 'disks').iterdir()}
            if expected != actual:
                raise AssertionError(fault + ': error path changed media')
        finally:
            if target.exists():
                target.chmod(0o644)
        fault_results.append({'case': fault, 'status': 'PASS', 'command': fault_command,
                              'media_unchanged': True, 'probe_sha256': digest(payload)})
    receipt = {'status': 'PASS', 'scope': 'hardware bring-up; not an OS boot',
               'command': command, 'cpu': 'Z80', 'ram_bytes': 65536,
               'boot': 'RDOS 2.52 banked ROM; sector entry 0080h',
               'console': 'FDC UART, ports 00h/01h',
               'emulator_sha256': digest(a.simulator.read_bytes()),
               'assembler_sha256': digest(a.assembler.read_bytes()),
               'boot_sha256': digest(boot), 'probe_sha256': digest(probe),
               'probe_bytes': len(probe), 'images': images,
               'checks': list(required), 'fault_cases': fault_results, 'exit_code': code}
    (out / 'result.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('PASS: disk cold boot, upper RAM, console, A-D I/O and whole-image integrity, invalid addresses, missing/wrong-size/read-only media')


if __name__ == '__main__':
    main()
