#!/usr/bin/env python3
"""Execute assembled NDR, CCP and PATH with controlled BDOS disk/console I/O."""
import struct
from pathlib import Path
from build_stateful_test_rsx import symbols
from test_bios import Z80
import test_ccp
from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]

class Guest:
    def __init__(self):
        self.cpu = Z80(b'')
        self.base = 0x6000
        self.carrier = (ROOT/'build/rsx/NDR.RSX').read_bytes()
        size = struct.unpack_from('<H', self.carrier, 12)[0]
        self.cpu.mem[self.base:self.base+size] = self.carrier[512:512+size]
        self.relocations = [struct.unpack_from('<H', self.carrier, 48+2*i)[0]
                            for i in range(struct.unpack_from('<H', self.carrier, 22)[0])]
        for off in self.relocations:
            self.cpu.setword(self.base+off, self.cpu.word(self.base+off)+self.base-0x8000)
        labels = symbols(ROOT/'build/rsx/ndr.lst')
        self.entry_off = labels['NR_SERVICE']-0x8000
        self.table_off = labels['NR_TABLE']-0x8000
        self.loaded = True
        self.drive = self.user = 0
        self.dma = 0x80
        self.files = {}
        self.fail_write = False
        self.reset_console()
        self.install()

    def install(self):
        c = self.cpu
        c.mem[0] = 0xc3
        c.setword(1, LAYOUT['BIOS']+3)
        c.mem[LAYOUT['BIOS']+3:LAYOUT['BIOS']+6] = b'\xc3\xff\xff'
        c.mem[5:8] = b'\xc3\x00\x50'
        c.mem[0x5000:0x5003] = b'\xd3\x00\xc9'
        c.sp = 0x7f00
        c.port_write = self.bdos

    def reset_console(self):
        self.output = bytearray()

    def bdos(self, port, value):
        c = self.cpu
        fn, de = c.c, c.de
        if fn == 182:
            c.hl = self.base+self.entry_off if self.loaded else 0
            c.setword(de+12, c.hl)
            c.a = 0 if self.loaded else 1
        elif fn == 25:
            c.a = self.drive
        elif fn == 32:
            if c.e != 255: self.user = c.e
            c.a = self.user
        elif fn == 14:
            self.drive = c.e
            c.a = 0
        elif fn == 2:
            self.output.append(c.e)
        elif fn == 9:
            while c.mem[de] != 36:
                self.output.append(c.mem[de]); de += 1
        elif fn == 26:
            self.dma = de
        elif fn in (15, 16, 19, 20, 21, 22):
            name = (bytes(c.mem[de:de+12]), self.user)
            record = c.mem[de+32]
            if fn == 15:
                c.a = 0 if name in self.files else 255
            elif fn == 16:
                c.a = 0
            elif fn == 19:
                self.files.pop(name, None); c.a = 0
            elif fn == 22:
                self.files[name] = bytearray(); c.a = 0
            elif fn == 20:
                data = self.files[name][128*record:128*(record+1)]
                c.a = 0 if len(data) == 128 else 1
                if not c.a: c.mem[self.dma:self.dma+128] = data
                c.mem[de+32] += 1
            else:
                c.a = 1 if self.fail_write else 0
                if not c.a:
                    self.files[name] += c.mem[self.dma:self.dma+128]
                    c.mem[de+32] += 1
        else:
            raise AssertionError(f'unexpected BDOS {fn}')

    def run(self, tail, program='NDR', leading_space=True):
        c = self.cpu
        image = (ROOT/f'build/utilities/{program}.COM').read_bytes()
        c.mem[0x100:0x100+len(image)] = image
        data = (' '+tail if tail and leading_space else tail).encode('ascii')
        c.mem[0x80] = len(data)
        c.mem[0x81:0x81+len(data)] = data
        self.reset_console()
        self.install()
        c.run(0x100, limit=500000)
        return self.output.decode('ascii')

    def table(self):
        p = self.base+self.table_off
        return bytes(self.cpu.mem[p:p+320])

    def lookup(self, name):
        c = self.cpu
        data = name.encode('ascii')
        c.mem[0x4000:0x4000+len(data)] = data
        c.hl, c.b, c.a = 0x4000, len(data), 0
        c.run(self.base+self.entry_off, limit=10000)
        return c.a, c.de

    def move(self, newbase):
        # The STATEFUL manager copies all allocation bytes and fixes exactly
        # the ordinary linked-pointer relocation sites; there are no runtime pointers.
        c = self.cpu
        c.mem[newbase:newbase+512] = c.mem[self.base:self.base+512]
        for off in self.relocations:
            c.setword(newbase+off, c.word(newbase+off)+newbase-self.base)
        c.mem[self.base:self.base+512] = bytes(512)
        self.base = newbase

def main():
    # CP/M supplies a blank-prefixed tail for ordinary command invocation.
    # Also accept raw tails and multiple blanks, including mixed-case options.
    cli = Guest()
    for i, prefix in enumerate(('', ' ', '   ')):
        cli.loaded = False
        for query in ('/H', '/HELP', '/VER'):
            before = cli.table()
            output = cli.run(prefix+query, leading_space=False)
            assert 'Named Directory Management' in output, (prefix, query, output)
            assert cli.table() == before
        cli.loaded = True
        assert 'updated' in cli.run(prefix+'/clear', leading_space=False)
        assert '0 of 32 names in use' in cli.run(prefix, leading_space=False)
        name, filename = f'MIX{i}', f'WS{i}'
        assert 'updated' in cli.run(prefix+name.lower()+'   P31:  ', leading_space=False)
        assert '1 of 32 names in use' in cli.run(prefix, leading_space=False)
        before = cli.table()
        assert 'saved' in cli.run(prefix+'/save   '+filename+'  ', leading_space=False)
        assert 'updated' in cli.run(prefix+'/clear', leading_space=False)
        assert 'loaded' in cli.run(prefix+'/load   '+filename+'  ', leading_space=False)
        assert cli.table() == before
        assert 'updated' in cli.run(prefix+'/del   '+name.lower(), leading_space=False)
        before = cli.table()
        for invalid in ('/CLEAR extra', '/DEL', '/LOA WS0', '/SAVEX WS0', '/LOAD WS0 extra'):
            cli.run(prefix+invalid, leading_space=False)
            assert cli.table() == before, (prefix, invalid)
    g = Guest()
    assert '/LOAD' in g.run('/HELP')
    assert 'Named Directory Management' in g.run('/VER')
    for name, du in [('ROOT','A0:'), ('COMMANDS','A0:'), ('UTILS','B0:'), ('LAST','P31:')]:
        assert 'updated' in g.run(f'{name} {du}')
    assert g.lookup('commands') == (0, 0x100)
    assert g.lookup('COMMAND') [0] == 255
    assert g.lookup('LAST') == (0, 0x101f)
    for bad in ('A A0:', 'P31 A0:', '123 A0:', 'LONGER999 A0:', 'ROOT C2:', 'BAD A32:', 'BAD Q0:', 'BAD A0: extra'):
        before = g.table(); g.run(bad); assert g.table() == before, bad
    assert 'COMMANDS A0:' in g.run('')
    before = g.table()
    assert 'saved' in g.run('/SAVE TEST')
    saved = dict(g.files)
    assert len(next(iter(saved.values()))) == 384
    assert 'File exists' in g.run('/SAVE TEST')
    assert 'updated' in g.run('/CLEAR')
    assert not any(g.table())
    assert 'loaded' in g.run('/LOAD TEST')
    assert g.table() == before
    key = next(iter(saved))
    for invalid in (saved[key][:-128], saved[key]+bytes(128), b'BAD!'+saved[key][4:]):
        g.files[key] = bytearray(invalid)
        assert 'unchanged' in g.run('/LOAD TEST')
        assert g.table() == before
    duplicate = bytearray(saved[key]); duplicate[74:82] = duplicate[64:72]
    g.files[key] = duplicate
    assert 'unchanged' in g.run('/LOAD TEST')
    assert g.table() == before
    g.files = saved
    g.fail_write = True
    assert 'failed' in g.run('/SAVE FAIL')
    assert len(g.files) == 1
    g.fail_write = False
    g.move(0x6800)
    assert g.lookup('LAST') == (0, 0x101f)
    assert g.table() == before
    assert 'updated' in g.run('/DEL ROOT')
    assert 'updated' in g.run('ROOT C3:')
    # Saved sets honor DU-qualified filenames and restore caller context.
    assert 'saved' in g.run('/SAVE B31:MY_SET')
    assert g.user == 0
    assert 'loaded' in g.run('/LOAD B31:MY_SET')
    assert g.user == 0
    # Same DU may have multiple aliases; reverse lookup uses first live slot.
    for i in range(28):
        assert 'updated' in g.run(f'ND{i:02d} A0:')
    assert 'full' in g.run('OVERFLOW A0:')
    before = g.table()
    assert g.lookup('OVERFLOW')[0] == 255
    assert g.table() == before

    # Assemble-time common code is exercised through CCP's relocated carrier.
    ccp = test_ccp.cpu()
    ccp.mem[g.base:g.base+512] = g.cpu.mem[g.base:g.base+512]
    g.cpu = ccp
    g.install()
    ccp.run(test_ccp.symbol('CN_PROMPT'), limit=10000)
    assert g.output.endswith(b' [COMMANDS] '), g.output
    data = test_ccp.symbol('CCP_DATA'); count = test_ccp.symbol('CCP_COUNT')
    def normalize(text):
        text = text.encode('ascii')
        ccp.mem[data:data+len(text)] = text
        ccp.mem[count] = len(text)
        ccp.run(test_ccp.symbol('CN_NORMAL'), limit=100000)
        return bytes(ccp.mem[data:data+ccp.mem[count]]).decode('ascii')
    for source, expected in (
        ('DIR UTILS:*.TXT','DIR B00:*.TXT'),
        ('COPY LAST:TEXT.TXT=UTILS:','COPY P31:TEXT.TXT=B00:'),
        ('TYPE "UTILS:literal text" LAST:FILE','TYPE "UTILS:literal text" P31:FILE'),
        ('UTILS:HELLO mixedCase.txt','B00:HELLO mixedCase.txt'),
        (':UTILS:HELLO x',':B00:HELLO x'),
        ('.UTILS:HELLO x','.B00:HELLO x'),
        ('DIR UNKNOWN:*.TXT','DIR UNKNOWN:*.TXT'),
        ('LAST:','P31:'),
    ):
        actual = normalize(source)
        assert actual == expected and not ccp.carry, (source, actual, expected)
    assert 'updated' in g.run('/DEL ND00')
    assert 'updated' in g.run('Q C0:')
    assert normalize('Q:APP') == 'C00:APP'
    assert normalize('GO Q:'+'x'*120) == 'GO C00:'+'x'*120
    normalize('GO Q:'+'x'*122)
    assert ccp.carry, 'overflowing expansion must reject the command'
    normalize('LAST:')
    ccp.run(test_ccp.symbol('CCP_NAVIGATE'), limit=10000)
    assert ccp.carry and (g.drive,g.user) == (15,31)
    g.reset_console()
    ccp.run(test_ccp.symbol('CN_PROMPT'), limit=10000)
    assert g.output == b' [LAST] ', g.output
    normalize('UTILS:HELLO x')
    ccp.run(test_ccp.symbol('CCP_LQUAL'), limit=10000)
    assert ccp.mem[test_ccp.symbol('CCP_FCB')] == 2
    assert ccp.mem[0x45] == 7
    assert ccp.word(0x43) == data+4
    ccp.run(test_ccp.symbol('CCP_LURST'), limit=10000)
    assert g.user == 31
    g.loaded = False
    g.reset_console(); ccp.run(test_ccp.symbol('CN_PROMPT'), limit=10000)
    assert not g.output
    assert 'not loaded' in g.run('')
    # PATH resolves once into its existing numeric representation.
    g.loaded = True
    ccp.setword(1, LAYOUT['BIOS']+3)
    ccp.mem[LAYOUT['BIOS']+3:LAYOUT['BIOS']+6] = b'\xc3\xff\xff'
    ccp.mem[LAYOUT['PDS_DESCRIPTOR']:LAYOUT['PDS_DESCRIPTOR']+4] = b'BM\x01\x05'
    address = LAYOUT['EXTENSIONS']-16
    result = g.run('$$ ROOT: B2: UTILS: C0:', 'PATH')
    expected = bytes([5,0,255,3,3,2,2,2,0,3,0])
    assert bytes(ccp.mem[address:address+len(expected)]) == expected, result
    snapshot = bytes(ccp.mem[address:address+13])
    g.run('/DEL UTILS')
    assert bytes(ccp.mem[address:address+13]) == snapshot
    print('PASS NDR capacity, names, validation, saved sets, failed I/O, relocation, prompt, navigation, command qualification, absence and numeric PATH capture')

if __name__ == '__main__': main()
