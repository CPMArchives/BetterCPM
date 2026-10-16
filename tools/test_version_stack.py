#!/usr/bin/env python3
"""Bound the pre-private-stack /VER path and preserve its byte-level matching."""
import tempfile
from pathlib import Path
from build_ccp import assemble
from test_bios import Z80
from test_utility_versions import address

ROOT = Path(__file__).resolve().parents[1]


def main():
    query = (ROOT/'src/utilities/common/version.inc').read_text().replace(
        '; @version-banner@', '        LD DE,UV_TEXT')
    with tempfile.TemporaryDirectory(prefix='bettercpm-version-stack-') as temp:
        work = Path(temp)
        text = ('        ORG 0100H\nSTART: CALL UV_CHECK\n        RET\n' +
                query + "\nUV_TEXT: DB 'Version test',13,10,'$'\n        END\n")
        image = assemble(Path.home()/'bin/z80asm', text, work/'version.bin',
                         work/'version.lst', 0x100)
        listing = (work/'version.lst').read_text(errors='replace')
        peak = 0

        def run(tail):
            nonlocal peak
            cpu = Z80(b'')
            cpu.mem[256:256+len(image)] = image
            cpu.mem[:3] = bytes.fromhex('c3ffff')
            cpu.mem[5:8] = bytes((0xDB, 254, 0xC9))
            cpu.mem[128] = len(tail)
            cpu.mem[129:129+len(tail)] = tail
            cpu.sp = 0xD638
            low = cpu.sp
            push = cpu.push

            def checked_push(value):
                nonlocal low
                push(value)
                low = min(low, cpu.sp)
            cpu.push = checked_push
            output = []

            def bdos(port):
                assert cpu.c == 9, cpu.c
                end = cpu.mem.index(36, cpu.de)
                output.append(bytes(cpu.mem[cpu.de:end]))
                return 0
            cpu.port_read = bdos
            cpu.a, cpu.bc, cpu.de, cpu.hl = 0xA5, 0x1234, 0x5678, 0x789A
            cpu.run(256, limit=100000)
            used = 0xD638-low
            peak = max(peak, used)
            assert used <= 24, (tail, used)
            if not output:
                assert (cpu.a, cpu.bc, cpu.de, cpu.hl) == (0xA5, 0x1234, 0x5678, 0x789A)
            return output

        for tail in (b'', b'LIST', b'LOAD FOO', b'/VER', b' /ver ',
                     b'/VER X', b'X /VER', b'/VERIFY', b'/VER /VER'):
            out = run(tail)
            if tail.strip().lower() == b'/ver':
                assert out == [b'Version test\r\n']
        # Exhaust all byte substitutions in the recognizer's fixed token.
        # This independently checks equivalence with its former OR-20h test.
        for index in range(4):
            for byte in range(256):
                tail = bytearray(b'/ver')
                tail[index] = byte
                out = run(tail)
                want = (byte | 0x20) == b'/ver'[index]
                assert bool(out) == want, (index, byte, out)
        assert address(listing, 'UV_CHECK') > 256
        print(f'PASS: /VER token matching, caller registers and pre-private-stack bound; peak {peak}/32 bytes, reserve {32-peak}')


if __name__ == '__main__':
    main()
