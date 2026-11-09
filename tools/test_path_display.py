#!/usr/bin/env python3
"""Execute PATH's NDR annotations and wrapping with controlled service discovery."""
from test_ndr import Guest
from system_layout import LAYOUT


class DisplayGuest(Guest):
    def __init__(self, width=None):
        self.width = width
        super().__init__()
        self.cpu.mem[LAYOUT['PDS_DESCRIPTOR']:LAYOUT['PDS_DESCRIPTOR']+4] = b'BM\x01\x05'
        self.path_address = LAYOUT['EXTENSIONS']-16

    def bdos(self, port, value):
        c = self.cpu
        if c.c == 182 and bytes(c.mem[c.de+4:c.de+8]) in (b'TCAP', b'MCON'):
            if self.width is None:
                c.a = 1
                return
            # Same-owner TCAP/MCON pair with the public immutable-facts ABI.
            c.mem[c.de+16] = 2
            c.mem[c.de+18] = 1
            c.mem[0x5200:0x5205] = bytes.fromhex('210053afc9')
            c.mem[0x5300:0x5308] = b'TC\x02\x08'+bytes([24 if self.width else 0, self.width, 0, 0])
            c.hl = 0x5200
            c.a = 0
            return
        super().bdos(port, value)

    def display(self):
        before = bytes(self.cpu.mem[self.path_address:self.path_address+13])
        context = (self.drive, self.user, self.dma)
        text = self.run('', 'PATH')
        assert before == bytes(self.cpu.mem[self.path_address:self.path_address+13])
        assert context == (self.drive, self.user, self.dma)
        return text


def main():
    g = DisplayGuest()
    g.run('ROOT A0:')
    g.run('ALIAS A0:')
    g.run('UTILS B0:')
    result = g.run('$$ ROOT: B3: C$: UTILS:', 'PATH')
    expected = 'PATH: $$: | A0:[ROOT] | B3: | C$: | B0:[UTILS]\r\n'
    assert result == g.display() == expected, result
    g.run('/DEL ROOT')
    assert g.display() == expected.replace('[ROOT]', '[ALIAS]')
    g.run('ROOT D7:')
    assert g.display() == expected.replace('[ROOT]', '[ALIAS]')
    g.run('/DEL ALIAS')
    assert g.display() == expected.replace('A0:[ROOT]', 'A0:')
    g.run('SYMBOL C5:')
    g.user = 5
    assert 'C$:[SYMBOL]' not in g.display()
    g.loaded = False
    numeric = 'PATH: $$: | A0: | B3: | C$: | B0:\r\n'
    assert g.display() == numeric
    assert g.run('/DEFAULT', 'PATH') == 'PATH: $$: | A0:\r\n'
    assert 'Usage: PATH' in g.run('/VER /HELP', 'PATH')
    assert 'PATH 1.0 (' in g.run('/VER', 'PATH')

    for width in (None, 0, 40, 80):
        g = DisplayGuest(width)
        locations = ['P31:', 'O30:', 'N29:', 'M28:', 'L27:', 'K26:']
        for index, du in enumerate(locations):
            g.run(f'ENTRY{index:03} {du}')
        g.run(' '.join(locations), 'PATH')
        text = g.display()
        entries = [du+f'[ENTRY{index:03}]' for index, du in enumerate(locations)]
        lines = ['PATH: '+entries[0]]
        for entry in entries[1:]:
            if len(lines[-1])+3+len(entry) >= (width or 80):
                lines.append('    | '+entry)
            else:
                lines[-1] += ' | '+entry
        assert text == '\r\n'.join(lines)+'\r\n', (width, text)
        assert all(len(line) < (width or 80) for line in text.splitlines())
        assert all(text.count(entry) == 1 for entry in entries)
    print('PASS PATH annotations, alias changes, absent NDR, symbols, queries, and 40/80-column wrapping')


if __name__ == '__main__':
    main()
