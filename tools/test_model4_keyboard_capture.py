#!/usr/bin/env python3
"""Check row-spanning keyboard hex output using the retained native capture."""
from pathlib import Path

from test_model4_keyboard_modifiers import EXPECTED, keyboard_output

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / 'docs/engineering/evidence/2026-11-03-model4-caps/native-modifiers-video.bin'


def main():
    video = CAPTURE.read_bytes()
    expected = ' '.join(f'{byte:02X}' for byte in EXPECTED)
    # Native PRINT placed the two digits of 41 on adjacent display rows.
    assert video[319:321] == b'41'
    assert keyboard_output(video) == expected
    # Retain failures for a wrong digit, missing digit, extra output, missing
    # probe title, or incomplete screen; do not merely join all hex digits.
    for position, value in ((320, ord('2')), (320, ord(' ')),
                            (160 + 3 * len(EXPECTED), ord('0'))):
        changed = bytearray(video)
        changed[position] = value
        assert keyboard_output(changed) != expected
    for invalid in (video[:1919], b'X' + video[1:]):
        try:
            keyboard_output(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid probe capture was accepted')
    print(f'PASS: {len(EXPECTED)} native bytes, row-spanning pair and malformed-output checks')


if __name__ == '__main__':
    main()
