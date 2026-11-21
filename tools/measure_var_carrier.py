#!/usr/bin/env python3
"""Measure a host-only private-carrier packing candidate; changes no artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
from build_z80pack_image import symbols
from build_ccp import relocation_offsets

ROOT = Path(__file__).resolve().parents[1]


def pack(data):
    """Grouped flag bytes; 12-bit backward distance, 4-bit length minus three."""
    result = bytearray()
    at = 0
    while at < len(data):
        flag_at = len(result)
        result.append(0)
        for bit in range(8):
            if at == len(data):
                break
            best, distance = 0, 0
            for previous in range(at - 1, max(-1, at - 4097), -1):
                length = 0
                while (length < 18 and at + length < len(data)
                       and data[previous + length] == data[at + length]):
                    length += 1
                if length > best:
                    best, distance = length, at - previous
                    if best == 18:
                        break
            if best >= 3:
                word = ((best - 3) << 12) | (distance - 1)
                result.extend(word.to_bytes(2, 'little'))
                at += best
            else:
                result[flag_at] |= 1 << bit
                result.append(data[at])
                at += 1
    return bytes(result)


def unpack(data, size):
    result = bytearray()
    at = 0
    while len(result) < size:
        if at >= len(data):
            raise ValueError('missing token flags')
        flags = data[at]
        at += 1
        for bit in range(8):
            if len(result) == size:
                break
            length = 1 if flags & (1 << bit) else 2
            if at + length > len(data):
                raise ValueError('truncated token')
            if length == 1:
                result.append(data[at])
            else:
                word = int.from_bytes(data[at:at + 2], 'little')
                count, distance = (word >> 12) + 3, (word & 4095) + 1
                if distance > len(result) or len(result) + count > size:
                    raise ValueError('invalid backreference')
                for _ in range(count):
                    result.append(result[-distance])
            at += length
    if at != len(data):
        raise ValueError('trailing tokens')
    return bytes(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    image = (root / 'build/ccp/ccp.bin').read_bytes()
    labels = symbols(root / 'build/ccp/ccp.lst')
    size = labels['CCP_DATA'] - 0xBB00
    payload = image[:size]
    packed = pack(payload)
    assert unpack(packed, size) == payload
    # Check the reference's literal, overlapping-copy and long-distance cases.
    for sample in (b'', b'x', bytes(range(256)), b'x' * 512,
                   bytes(range(256)) * 20):
        assert unpack(pack(sample), len(sample)) == sample
    for bad, expected in ((b'\0\0\0', 3), (b'\1', 1),
                          (b'\1x\0', 1)):
        try:
            unpack(bad, expected)
        except ValueError:
            pass
        else:
            raise AssertionError('reference accepted malformed stream')
    print(json.dumps({
        'status': 'host-only sizing candidate; no Z80 decoder or VAR code',
        'payload_sha256': hashlib.sha256(payload).hexdigest(),
        'ccp_payload_bytes': size,
        'ccp_allocation_bytes': (len(image) + 255) & ~255,
        'relocations': len(relocation_offsets(image, [
            ((root / 'build/ccp/ccp-alt.bin').read_bytes(), 0xBC01),
            ((root / 'build/ccp/ccp-check.bin').read_bytes(), 0xBD37)])),
        'raw_carrier_bytes': size + 1024,
        'checked_carrier_bytes': size + 1046,
        'carrier_capacity': 6656,
        'checked_spare_bytes': 6656 - size - 1046,
        'candidate_packed_payload_bytes': len(packed),
        'gross_payload_savings': size - len(packed),
        'round_trip': 'PASS',
        'limitations': 'excludes decoder, new format metadata, VAR code and fixups; not a fit or execution claim',
    }, indent=2))


if __name__ == '__main__':
    main()
