#!/usr/bin/env python3
"""Check that native qualification cannot conceal extra code or changed bytes."""
from qualify_codec_native import native_text, verify_native


def main():
    expected = bytes(range(129))
    raw = expected + b'\x1a'*127
    log = b'CODE SIZE    0081 (0100-0180)'
    verify_native(raw, expected, log)
    rejected = 0
    for candidate, transcript in ((b'\xff'+raw[1:],log), (raw[:-1],log),
                                  (raw+b'\x1a'*128,log), (raw[:-1]+b'\x00',log),
                                  (raw,b'CODE SIZE    0082'), (raw,b'')):
        try:
            verify_native(candidate,expected,transcript)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError('invalid native result accepted')
    prepared = native_text("        DB 'exists; nothing replaced.',13,10 ; comment\n        DB '',13,10\n")
    assert b"'exists; nothing replaced.'" in prepared and b'comment' not in prepared
    assert b"''" not in prepared and b'DB 13,10' in prepared
    print(f'PASS: {rejected} invalid parity receipts rejected; quoted text preserved.')


if __name__ == '__main__':
    main()
