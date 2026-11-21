#!/usr/bin/env python3
"""Execute the emitted protected COM reader at its exact record boundary.

The disk-call fixture supplies deterministic sequential records. The production
CL_NEXT/CL_END/CL_BIG instructions perform all placement, copying and rejection.
This is an instruction-level boundary check, not native emulator qualification.
"""
import argparse
import json
from pathlib import Path

from build_z80pack_image import symbols
from test_bios import SENTINEL, Z80


def check(root: Path, target: str) -> dict:
    context = root / 'build/profile/context.json'
    if context.exists():
        layout = json.loads(context.read_text())['symbols']
    else:
        from build_profiles import symbols as layout_symbols
        layout = layout_symbols((root/'src/system/layout.inc').read_text())
    out = root/'build'/target if target != 'model4' else root/'build/system'
    labels = symbols(out/'extensions.lst')
    binary = (out/'extensions.bin').read_bytes()
    top = layout['LY_TPA']
    fit = (top-256)//128*128
    floor = 54272 if target == 'model4' else 57344
    assert fit >= floor, (target, fit, floor)
    for length in (fit, fit+128):
        cpu = Z80(b'')
        cpu.mem[layout['LY_EXT']:layout['LY_EXT']+len(binary)] = binary
        # The COM load runs on the existing protected system stack, not in TPA.
        cpu.sp = layout['LY_SYS']+0x74
        cpu.setword(layout['LY_SYS']+0x90, top)
        cpu.mem[top:layout['LY_SYS']] = b'\xa5'*(layout['LY_SYS']-top)
        before = bytes(cpu.mem[top:layout['LY_SYS']])
        cpu.mem[layout['LY_BDOS']:layout['LY_BDOS']+3] = b'\xd3\x00\xc9'
        cpu.mem[layout['LY_SYS']+3:layout['LY_SYS']+6] = bytes((0xc3, SENTINEL&255, SENTINEL>>8))
        record = [0]

        def disk(port, _value):
            assert port&255 == 0 and cpu.c == 20
            number = record[0]
            if number*128 == length:
                cpu.a = 1  # CP/M sequential EOF
            else:
                cpu.mem[layout['LY_BUF']:layout['LY_BUF']+128] = bytes((number&255,))*128
                record[0] += 1
                cpu.a = 0

        cpu.port_write = disk
        cpu.hl = 256
        cpu.run(labels['CL_NEXT'], limit=500000)
        assert bytes(cpu.mem[top:layout['LY_SYS']]) == before, 'reader overwrote gateway/PDS'
        result = cpu.mem[layout['LY_EXT']-14]
        assert result == (0 if length == fit else 255), (target, length, result)
        for number in range(fit//128):
            assert cpu.mem[256+number*128:384+number*128] == bytes((number&255,))*128
    return dict(target=target, raw_com=top-256, maximum_com=fit,
                accepted_bytes=fit, rejected_bytes=fit+128,
                protected_canary='PASS', method='production reader / controlled disk records')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--target', choices=('model4','z80pack','trs80m2'), default='model4')
    args = parser.parse_args()
    print(json.dumps(check(args.root, args.target), indent=2))
