#!/usr/bin/env python3
"""Qualify reserved MCON and screen-backend metadata on both supported BIOS backends."""
from build_rsx_module import make_module
import test_rsxcarrier as carrier
from system_layout import LAYOUT


def check(capabilities, *, backend=0x2002, major=1, minor=0,
          reconstruction='STATEFUL', identity=b'MCON', entry=9, expected=False):
    image = make_module(name='MONTEST', version=(0, 1), services=[],
                        linked_base=0x9000, code=b'\0'*8+b'\xc9'*8,
                        relocations=[], reconstruction_class=reconstruction,
                        callable_services=[(identity, major, minor, 9, capabilities)])
    if entry != 9:
        image = bytearray(image)
        offset = image.index(identity) + 6
        image[offset:offset+2] = entry.to_bytes(2, 'little')
        image = bytes(image)
    cpu, _ = carrier.phase_one(image, b'MONTEST ')
    assert cpu.a == 0
    # Only stub the capability leaf. Execute the full carrier/metadata validators.
    cpu.mem[LAYOUT['BIOS']+63:LAYOUT['BIOS']+67] = bytes((0x21, backend & 255, backend >> 8, 0xC9))
    before = carrier.phase_two(cpu, len(image))
    assert (cpu.a == 0) == expected, (backend, major, minor, capabilities, reconstruction)
    if expected:
        assert cpu.mem[carrier.REQUEST+10] == 1
    else:
        assert cpu.mem[carrier.REQUEST+10] == 0xCC
        assert bytes(cpu.mem[carrier.FACTS:carrier.FACTS+26]) == before


def legacy_cases(identity):
    count = 0
    for backend, matching in [(0x2002, 1), (0x7337, 2)]:
        for bits in [0, 1, 2, 3, 4, 0x101, 0xFFFF]:
            check(bits, backend=backend, identity=identity, expected=bits == matching)
            count += 1
        for major, minor in [(0, 0), (1, 1), (2, 0)]:
            check(matching, backend=backend, identity=identity, major=major, minor=minor)
            count += 1
        for entry in [0, 7, 16, 0xFFFF]:
            check(matching, backend=backend, identity=identity, entry=entry)
            count += 1
        for reconstruction in ['STATELESS', 'COLD_ONLY']:
            check(matching, backend=backend, identity=identity, reconstruction=reconstruction)
            count += 1
        check(0xFFFF, backend=backend, major=2, minor=3,
              identity=b'TEST', reconstruction='STATELESS', expected=True)
        count += 1
    return count


def main():
    count=sum(legacy_cases(identity) for identity in [b'MCON', b'SCRN'])
    print(f'PASS: {count} MCON/SCRN version/class/platform cases; unsupported/invalid dependent MCON remains rejected; other callable identities unchanged')


if __name__ == '__main__':
    main()
