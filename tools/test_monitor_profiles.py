#!/usr/bin/env python3
"""Check isolated profile parser routing and host output; not full renderer qualification."""
import json
import re
from pathlib import Path
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'build/audit/monitor-efficiency'


def load(folder):
    cpu = Z80((folder / 'bios.bin').read_bytes())
    table = {name.upper(): int(address, 16) for address, name in re.findall(
        r'^([0-9a-f]{4})\s+.*?\b([A-Z][A-Z0-9_]*):',
        (folder / 'bios.lst').read_text(errors='replace'), re.M | re.I)}
    return cpu, table


def parser_checks(folder, both):
    cpu, table = load(folder)
    # Stub the screen primitives only. Execute the assembled frontend and
    # coordinate state machine; this campaign does not test rendered pixels.
    handlers = ('BELLHANDLER', 'VT_LEFT', 'VT_TAB', 'INCVIDROW', 'CRHANDLER',
                'CLS', 'VT_UP', 'VT_DOWN', 'VT_RIGHT', 'HOMECURSOR',
                'VT_REVERSE', 'CLREOS', 'CLREOL')
    tags = {name: 160+i for i, name in enumerate(handlers)}
    entry = table['PROFILE_OUT' if both else 'VT_OUTPUT']
    if both:
        cpu.mem[table['VT_PROFILE']] = 1

    def send(character):
        cpu.c = character
        cpu.run(entry)
        return cpu.a

    count = 0
    for row in range(256):
        for col in range(256):
            for character in (27, ord('Y'), row, col):
                send(character)
            expected = min((row-32) & 255, 23) | (min((col-32) & 255, 79) << 8)
            assert cpu.word(table['VIDEOPOS']) == expected, (row, col)
            assert cpu.mem[table['ESCFLAG']] == 0
            count += 1
    def route(char, name, escape=False):
        address = table[name]
        saved = bytes(cpu.mem[address:address+3])
        cpu.mem[address:address+3] = bytes((0x3E, tags[name], 0xC9))
        if escape:
            send(27)
        assert send(char) == tags[name], (char, name)
        cpu.mem[address:address+3] = saved

    for char, name in ((7,'BELLHANDLER'), (8,'VT_LEFT'), (9,'VT_TAB'),
                       (10,'INCVIDROW'), (13,'CRHANDLER'), (28,'CLS')):
        route(char, name)
    for char, name in zip('ABCDHIJK', ('VT_UP', 'VT_DOWN', 'VT_RIGHT', 'VT_LEFT',
                         'HOMECURSOR', 'VT_REVERSE', 'CLREOS', 'CLREOL')):
        route(ord(char), name, True)
        assert cpu.mem[table['ESCFLAG']] == 0
    # Currently unimplemented VT52 modes are consumed; not claimed supported.
    for char in 'FGZ=>[\\':
        send(27)
        send(ord(char))
        assert cpu.mem[table['ESCFLAG']] == 0
    print(f'{folder.name}: {count} coordinate sequences and control/escape routing passed (renderer stubbed)')


def host_checks(folder, expected_clear):
    cpu, table = load(folder)
    output = []
    cpu.port_write = lambda port, value: output.append((port & 255, value))
    for character in b'ABC\x1bY!"':
        cpu.c = character
        cpu.run(table['PL_CONOT'])
    assert output == [(1, ch) for ch in b'ABC\x1bY!"']
    output.clear()
    cpu.c = 28
    cpu.run(table['PL_CONOT'])
    assert output == [(1, ch) for ch in expected_clear], output
    print(f'{folder.name}: output passthrough and clear sequence passed (host display not tested)')


def main():
    rows = {r['profile']: Path(r['directory']) for r in json.loads((AUDIT/'profiles.json').read_text())}
    parser_checks(rows['vt52-screen'], False)
    parser_checks(rows['both-screen'], True)
    host_checks(rows['host-ansi'], b'\x1b[2J\x1b[H')
    host_checks(rows['host-vt52-pass'], b'\x1bH\x1bJ')


if __name__ == '__main__':
    main()
