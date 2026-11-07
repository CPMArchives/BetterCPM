"""Independently reviewed CONSTEST operator prompts, keystrokes and expected results."""

BUFFERED = [
    (106, b'Type AB then Enter. Expect count 02 and data [AB]: ', b'AB\r', b'AB'),
    (108, b'Type ABC then Enter. Expect count 03: ', b'ABC\r', b'ABC'),
    (109, b'Type XYZ then Enter. Expect data [XYZ] at buffer+2: ', b'XYZ\r', b'XYZ'),
    (111, b'Type AB then Enter. Expect count 02/data [AB], no CR stored: ', b'AB\r', b'AB'),
    (112, b'Type AB then Ctrl-J. Expect count 02/data [AB], no LF stored: ', b'AB\n', b'AB'),
    (113, b'Maximum is 1. Type Z only; no additional character is required: ', b'Z', b'Z'),
    (114, b'Type M then Enter. Expect M echoed, count 01, data [M]: ', b'M\r', b'M'),
    (115, b'Type AB, Backspace, C, Enter. Expect count 02/data [AC]: ', b'AB\x08C\r', b'AC'),
    (116, b'Type AB, DEL, C, Enter. Expect count 02/data [AC]: ', b'AB\x7fC\r', b'AC'),
    (122, b'Expect count 02/data [AC]: ', b'AB\x08C\r', b'AC'),
]

ECHO = [
    (95, b'Press Enter; cursor should return to column zero: ', b'\r', b'\r\r\nOBSERVED: return A=0D\r\n'),
    (96, b'Press Ctrl-J; cursor should advance one line: ', b'\n', b'\n\r\nOBSERVED: return A=0A\r\n'),
    (97, b'After ABC, press Backspace; X should overwrite C:\r\nABC', b'\x08', b'\x08X\r\nEXPECTED: display ends as ABX.\r\n'),
    (98, b'After A, press TAB; B should land at next tab stop:\r\nA', b'\t', b'       B\r\nEXPECTED: TAB was expanded to the next eight-column stop.\r\n'),
    (99, b'Press Ctrl-A; nothing should appear between brackets: [', b'\x01', b']\r\nOBSERVED: return A=01\r\n'),
    (100, b'After A, press TAB; B should use the shared next tab stop:\r\nA', b'\t', b'       B\r\nEXPECTED: Function 1 TAB used the column established by Function 9.\r\n'),
]

DIRECT = [
    (83, b'Press K now: ', b'K', b'\r\nOBSERVED: return A=4B', b''),
    (84, b'Press U; nothing should appear between these brackets: [', b'U', b']\r\nOBSERVED: return A=55', b']'),
    (93, b'Press R now: ', b'R', b'R\r\nOBSERVED: return A=52', b'R'),
    (94, b'Press G; it should appear between brackets: [', b'G', b'G]\r\nOBSERVED: return A=47', b'G]'),
]

CONTROLS = [
    (118, b'Type AB, Ctrl-E, CD, Enter. Expect new line and data [ABCD]: ', b'AB\x05CD\r', b'ABCD', b'AB\r\nCD'),
    (119, b'Type AB, Ctrl-R, CD, Enter. Expect redisplay and data [ABCD]: ', b'AB\x12CD\r', b'ABCD', b'AB#\r\nABCD'),
    (120, b'Type AB, Ctrl-U, CD, Enter. Expect new line and data [CD]: ', b'AB\x15CD\r', b'CD', b'AB#\r\nCD'),
    (121, b'Type AB, Ctrl-X, CD, Enter. Expect erased line and data [CD]: ', b'AB\x18CD\r', b'CD', b'CD'),
]
